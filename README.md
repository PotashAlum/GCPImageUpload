# Team Image Management API

A scalable, cloud-based service for teams to securely store, organize, and retrieve images using modern cloud technologies. Built with FastAPI, Google Cloud Storage, and MongoDB.

## Hierarchical Resource Architecture

This service follows a clean, hierarchical resource design pattern:

```
/teams
└── /{team_id}
    ├── /users
    │   └── /{user_id}
    │       ├── /api-keys
    │       │   └── /{api_key_id}
    │       └── /images
    │           └── /{image_id}
    ├── /api-keys
    │   └── /{api_key_id}
    └── /images
        └── /{image_id}
```

This design makes authorization simpler, API navigation more intuitive, and resource relationships clearer.

## Authentication and Authorization

All endpoints require an API key provided in the `X-API-Key` header. The system includes three roles:

### User Roles

1. **Root**: System administrators with full access to all resources
2. **Admin**: Team administrators who can manage team resources 
3. **User**: Regular users who can access their own resources

### Hierarchical Permissions

The permission model follows a role hierarchy approach:
- If a path requires "user" access, all roles can access it
- If a path requires "admin" access, only admin and root can access it
- If a path requires "root" access, only root can access it

### Resource Ownership Verification

After role-based access is confirmed, resource ownership is verified:
- Users can only access their own resources (images, API keys)
- Admins can access all resources within their team
- Root can access all resources in the system

## API Endpoints

### Teams
- `POST /teams/` - Create a new team (Root only)
- `GET /teams/` - List all teams (Root only)
- `GET /teams/{team_id}` - Get a specific team (Team members)
- `DELETE /teams/{team_id}` - Delete a team (Root only)

### Team Users
- `POST /teams/{team_id}/users/` - Create a new user in a team (Admin+)
- `GET /teams/{team_id}/users/` - List users in a team (All team members)
- `GET /teams/{team_id}/users/{user_id}` - Get a specific team user (All team members)
- `DELETE /teams/{team_id}/users/{user_id}` - Delete a team user (Admin+)

### Team API Keys
- `POST /teams/{team_id}/users/{user_id}/api-keys/` - Create a new API key for team (Admin+)
- `GET /teams/{team_id}/api-keys/` - List team API keys (Admin+)
- `GET /teams/{team_id}/api-keys/{api_key_id}` - Get a specific team API key (Admin+)
- `DELETE /teams/{team_id}/api-keys/{api_key_id}` - Delete a team API key (Admin+)

### Team User API Keys
- `GET /teams/{team_id}/users/{user_id}/api-keys/` - List user API keys (User for self, Admin for all)
- `GET /teams/{team_id}/users/{user_id}/api-keys/{api_key_id}` - Get a specific user API key (User for self, Admin for all)
- `DELETE /teams/{team_id}/users/{user_id}/api-keys/{api_key_id}` - Delete a user API key (User for self, Admin for all)

### Team Images
- `POST /teams/{team_id}/images/` - Upload a new image (All team members)
- `GET /teams/{team_id}/images/` - List team images (All team members)
- `GET /teams/{team_id}/images/{image_id}` - Get a specific team image (All team members)
- `DELETE /teams/{team_id}/images/{image_id}` - Delete a team image (Admin for all, User for own)

### Team User Images
- `GET /teams/{team_id}/users/{user_id}/images/` - List user images (User for self, Admin for all)
- `GET /teams/{team_id}/users/{user_id}/images/{image_id}` - Get a specific user image (User for self, Admin for all)
- `DELETE /teams/{team_id}/users/{user_id}/images/{image_id}` - Delete a user image (User for self, Admin for all)

### Audit Logs
- `GET /audit-logs/` - List audit logs with optional filtering (Root only)

## Setup and Usage

### Getting Started with Authentication

1. **Initial Setup**: Use the root API key (configured in environment variables)
   ```
   X-API-Key: your-root-api-key
   ```

2. **Create a Team**: Using the root API key
   ```bash
   curl -X POST "http://localhost:8080/teams/" \
     -H "X-API-Key: your-root-api-key" \
     -H "Content-Type: application/json" \
     -d '{"name": "Engineering Team", "description": "Product development team"}'
   ```

3. **Create an Admin API Key**: Using the root API key
   ```bash
   curl -X POST "http://localhost:8080/teams/{team_id}/api-keys/" \
     -H "X-API-Key: your-root-api-key" \
     -H "Content-Type: application/json" \
     -d '{"name": "Engineering Admin Key", "role": "admin"}'
   ```

4. **Create Users**: Using the admin API key
   ```bash
   curl -X POST "http://localhost:8080/teams/{team_id}/users/" \
     -H "X-API-Key: admin-api-key-from-step-3" \
     -H "Content-Type: application/json" \
     -d '{"username": "john.doe", "email": "john.doe@example.com"}'
   ```

5. **Create User API Keys**: Using the admin API key
   ```bash
   curl -X POST "http://localhost:8080/teams/{team_id}/api-keys/" \
     -H "X-API-Key: admin-api-key-from-step-3" \
     -H "Content-Type: application/json" \
     -d '{"name": "John's API Key", "role": "user", "user_id": "user-id-from-step-4"}'
   ```

6. **Upload an Image**: Using the user API key
   ```bash
   curl -X POST "http://localhost:8080/teams/{team_id}/images/" \
     -H "X-API-Key: user-api-key-from-step-5" \
     -F "user_id=user-id-from-step-4" \
     -F "title=Project Screenshot" \
     -F "description=Latest UI design" \
     -F "tags=ui,design,prototype" \
     -F "file=@/path/to/your/image.jpg"
   ```

## Benefits of Hierarchical API Design

1. **Intuitive Resource Navigation**
   - Clear, nested paths reflect real-world relationships between resources
   - Makes API exploration and usage more intuitive for developers

2. **Simplified Authorization Logic**
   - Path parameters provide context for ownership verification
   - Role requirements map cleanly to resource paths

3. **Consistent Access Patterns**
   - Similar resources use consistent URL patterns
   - Standard CRUD operations follow predictable conventions

4. **Self-documenting API**
   - URL structure itself provides context about resource relationships
   - Path hierarchy reveals organizational structure of resources

## Security Considerations

- API keys should never be shared between users
- Use HTTPS in production to protect API keys in transit
- Rotate API keys regularly
- The root API key should be carefully protected