## Middleware Implementation

The application uses a middleware-based approach for cross-cutting concerns:

### Authentication Middleware

The authentication middleware handles API key validation and authorization:

1. **API Key Extraction**: Extracts the API key from the `X-API-Key` header
2. **Authentication**: Validates the API key against the database
3. **Path Analysis**: Normalizes the request path and extracts resource identifiers
4. **Permission Checking**: Matches the request against defined permission rules
5. **Resource Ownership Verification**: Ensures users only access authorized resources

The middleware implements a sophisticated pattern-matching algorithm to determine which permission rules apply to a given request, enforcing both role-based permissions and resource ownership.

### Audit Middleware

The audit middleware logs all API operations:

1. **Request Capture**: Records incoming request details
2. **Response Capture**: Records response status and timing
3. **Audit Log Creation**: Stores a complete audit record including:
   - User ID and API key information
   - Resource type and ID
   - Action performed
   - Request status (success/failure)
   - Timestamp
   - Request duration

All audit logs are searchable through the `/audit-logs` endpoint (accessible only to root users).# Image Management API

A scalable, cloud-based service for teams to securely store, organize, and retrieve images using modern cloud technologies. Built with FastAPI, Google Cloud Storage, and MongoDB.

This service follows clean architecture principles with a clear separation of concerns:
- Domain-driven design with well-defined interfaces
- Repository pattern for data access abstraction
- Dependency injection for flexible component integration
- Middleware for cross-cutting concerns like authentication and audit logging

## Features

### Core Features
- **Team-based Organization**: Create and manage teams with associated users and images
- **User Management**: Create, retrieve, update, and delete users within teams
- **Image Storage**: Upload, organize, and manage images with metadata
- **Cloud Storage Integration**: Seamless integration with Google Cloud Storage
- **API Key Authentication**: Secure access control with API key validation
- **Comprehensive Audit Logging**: Track all system operations for security and compliance
- **Containerized Deployment**: Docker-based setup for local development and cloud deployment

### Architecture Highlights
- **Clean Architecture**: Clear separation between domain, application, and infrastructure layers
- **Repository Pattern**: Abstraction layer for data access with MongoDB implementation
- **Dependency Injection**: Flexible component wiring through factory pattern
- **Middleware Pipeline**: Centralized request/response processing for authentication and audit logging
- **Interface-Based Design**: Well-defined contracts between system components

## Technology Stack

- **Backend Framework**: FastAPI
- **Database**: MongoDB (via Motor async driver)
- **Storage**: Google Cloud Storage
- **Authentication**: Custom API key system
- **Containerization**: Docker and Docker Compose
- **Cloud Deployment**: Google Cloud Run

## Project Structure

```
image-management-api/
├── middleware/
│   ├── __init__.py
│   ├── audit_middleware.py            # Middleware for audit logging
│   └── authentication_middleware.py   # API key authentication middleware
├── models/
│   ├── __init__.py
│   ├── api_key_model.py               # Pydantic model for API keys
│   ├── audit_log_model.py             # Pydantic model for audit logs
│   ├── image_model.py                 # Pydantic model for images
│   ├── team_model.py                  # Pydantic model for teams
│   └── user_model.py                  # Pydantic model for users
├── repository/
│   ├── implementation/
│   │   ├── mongodb/
│   │   │   ├── api_key_repository.py  # MongoDB implementation for API keys
│   │   │   ├── audit_log_repository.py# MongoDB implementation for audit logs
│   │   │   ├── image_repository.py    # MongoDB implementation for images
│   │   │   ├── team_repository.py     # MongoDB implementation for teams
│   │   │   └── user_repository.py     # MongoDB implementation for users
│   │   └── mongodb_repository.py      # Base MongoDB repository implementation
│   ├── interfaces/
│   │   ├── domains/
│   │   │   ├── api_key_repository_interface.py
│   │   │   ├── audit_log_repository_interface.py
│   │   │   ├── image_repository_interface.py
│   │   │   ├── team_repository_interface.py
│   │   │   └── user_repository_interface.py
│   │   └── repository_interface.py    # Base repository interface
│   ├── __init__.py
│   └── repository_factory.py          # Factory for repository creation
├── routers/
│   ├── __init__.py
│   ├── api_key_router.py              # API key management endpoints
│   ├── audit_log_router.py            # Audit log access endpoints
│   ├── image_router.py                # Image upload and management endpoints
│   ├── team_router.py                 # Team management endpoints
│   └── user_router.py                 # User management endpoints
├── services/
│   ├── implementation/                # Service implementations
│   ├── interfaces/                    # Service interfaces
│   ├── __init__.py
│   └── service_factory.py             # Factory for service creation
├── utils/                             # Utility functions and helpers
├── .dockerignore
├── .env.example                       # Example environment variables
├── cloud-run-deploy.sh                # GCP deployment script
├── dependencies.py                    # Dependency injection configuration
├── docker-compose.yml                 # Local development setup
├── Dockerfile                         # Container definition
├── EntityDiagram.drawio               # Database entity relationship diagram
├── main.py                            # Application entry point
├── README.md                          # Project documentation
└── requirements.txt                   # Python dependencies
```

## API Endpoints

### Authentication
All endpoints require an API key provided in the `X-API-Key` header.

### Teams
- `POST /teams/` - Create a new team
- `GET /teams/` - List all teams
- `GET /teams/{team_id}` - Get a specific team
- `DELETE /teams/{team_id}` - Delete a team
- `GET /teams/{team_id}/api-keys` - List team API keys
- `GET /teams/{team_id}/api-keys/{api_key_id}` - Get a specific team API key
- `GET /teams/{team_id}/users` - List team users
- `GET /teams/{team_id}/users/{user_id}` - Get a specific team user
- `GET /teams/{team_id}/images` - List team images
- `GET /teams/{team_id}/images/{image_id}` - Get a specific team image
- `DELETE /teams/{team_id}/images/{image_id}` - Delete a team image

### Users
- `POST /users/` - Create a new user
- `GET /users/` - List all users
- `GET /users/{user_id}` - Get a specific user
- `DELETE /users/{user_id}` - Delete a user

### Images
- `POST /images/` - Upload a new image
- `GET /images/` - List images (filtered by team_id)
- `GET /images/{image_id}` - Get a specific image
- `DELETE /images/{image_id}` - Delete an image

### API Keys
- `POST /api-keys/` - Create a new API key
- `GET /api-keys/` - List all API keys
- `GET /api-keys/{api_key_id}` - Get a specific API key
- `DELETE /api-keys/{api_key_id}` - Delete an API key

### Audit Logs
- `GET /audit-logs/` - List audit logs (with optional filtering)

## Setup and Installation

### Prerequisites
- Docker and Docker Compose
- Google Cloud Platform account (for cloud deployment)
- Google Cloud SDK (for deployment)

### Environment Variables
Create a `.env` file based on the example below:

```
MONGODB_URI=mongodb://mongodb:27017/user_image_db
GCS_BUCKET_NAME=your-gcs-bucket-name
ROOT_API_KEY=your-root-admin-key
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-credentials.json
```

### Local Development

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/image-management-api.git
   cd image-management-api
   ```

2. Create a `credentials` directory and place your GCP service account key file there:
   ```
   mkdir -p credentials
   # Copy your gcp-credentials.json file into the credentials directory
   ```

3. Start the services using Docker Compose:
   ```
   docker-compose up
   ```

4. The API will be available at `http://localhost:8080`
   - API documentation: `http://localhost:8080/docs`
   - ReDoc documentation: `http://localhost:8080/redoc`

### Google Cloud Deployment

1. Update the `cloud-run-deploy.sh` script with your GCP project details:
   ```bash
   PROJECT_ID="your-gcp-project-id"
   IMAGE_NAME="user-image-service"
   REGION="your-preferred-region"
   SERVICE_NAME="user-image-service"
   MONGODB_URI="your-mongodb-connection-string"
   GCS_BUCKET_NAME="your-gcs-bucket-name"
   ROOT_API_KEY="your-secure-api-key"
   ```

2. Make the script executable and run it:
   ```
   chmod +x cloud-run-deploy.sh
   ./cloud-run-deploy.sh
   ```

3. The script will:
   - Build and push the container image to Google Container Registry
   - Create a Cloud Storage bucket for logs (if it doesn't exist)
   - Deploy the service to Cloud Run with appropriate environment variables

## Usage Example

### Creating a Team
```bash
curl -X POST "http://localhost:8080/teams/" \
  -H "X-API-Key: your-root-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Engineering Team", "description": "Product development team"}'
```

### Creating a User
```bash
curl -X POST "http://localhost:8080/users/" \
  -H "X-API-Key: your-root-api-key" \
  -H "Content-Type: application/json" \
  -d '{"username": "john.doe", "email": "john.doe@example.com", "team_id": "team-id-from-previous-step"}'
```

### Uploading an Image
```bash
curl -X POST "http://localhost:8080/images/" \
  -H "X-API-Key: your-api-key" \
  -F "user_id=user-id-from-previous-step" \
  -F "team_id=team-id-from-first-step" \
  -F "title=Project Screenshot" \
  -F "description=Latest UI design" \
  -F "tags=ui,design,prototype" \
  -F "file=@/path/to/your/image.jpg"
```

## Authentication and Authorization

The API uses a comprehensive role-based access control system with API keys:

### API Key Authentication
All API endpoints require an API key, which must be provided in the `X-API-Key` header with each request. The system has three user roles:

1. **Root** - System administrators with full access to all resources
2. **Admin** - Team administrators who can manage users and resources within their team
3. **User** - Regular users who can access their own resources and team resources

### User Hierarchy and Permissions

```
Root
 └── Team 1
     ├── Admin 1
     │   └── Users
     └── Admin 2
         └── Users
 └── Team 2
     └── Admin
         └── Users
```

### Role-Based Access Control

- **Root Users**: Can access everything in the system
  - Create and manage teams
  - Generate API keys for team admins
  - Access all users, images, and audit logs

- **Admin Users**: Can manage their team's resources
  - Create and manage users within their team
  - Generate API keys for team users
  - Access all images in their team
  - Cannot access resources from other teams

- **Regular Users**: Have limited access
  - Upload and manage their own images
  - View team images
  - Cannot access other users' resources or resources from other teams

### Permission Examples

| Endpoint | Root | Admin | User |
|----------|------|-------|------|
| POST /teams/ | ✅ | ❌ | ❌ |
| GET /teams/{team_id} | ✅ | ✅ | ✅ |
| POST /users/ | ✅ | ✅ | ❌ |
| GET /users/{user_id} | ✅ | ✅ | Self only |
| POST /api-keys/ | ✅ | ✅ | ❌ |
| POST /images/ | ✅ | ✅ | ✅ |
| GET /audit-logs/ | ✅ | ❌ | ❌ |

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
   curl -X POST "http://localhost:8080/api-keys/" \
     -H "X-API-Key: your-root-api-key" \
     -H "Content-Type: application/json" \
     -d '{"name": "Engineering Admin Key", "role": "admin", "team_id": "team-id-from-step-2"}'
   ```

4. **Create Users**: Using the admin API key
   ```bash
   curl -X POST "http://localhost:8080/users/" \
     -H "X-API-Key: admin-api-key-from-step-3" \
     -H "Content-Type: application/json" \
     -d '{"username": "john.doe", "email": "john.doe@example.com", "team_id": "team-id-from-step-2"}'
   ```

5. **Create User API Keys**: Using the admin API key
   ```bash
   curl -X POST "http://localhost:8080/api-keys/" \
     -H "X-API-Key: admin-api-key-from-step-3" \
     -H "Content-Type: application/json" \
     -d '{"name": "John's API Key", "role": "user", "user_id": "user-id-from-step-4", "team_id": "team-id-from-step-2"}'
   ```

### Security Considerations

- API keys should never be shared between users
- Use HTTPS in production to protect API keys in transit
- Rotate API keys regularly
- The root API key should be carefully protected

## Development and Contribution

### Architecture Notes
This project follows Clean Architecture principles with domain-driven design:

1. **Core Domain Layer**:
   - Domain models defined in the `models` package
   - Repository interfaces in `repository/interfaces/domains`
   - Service interfaces in `services/interfaces`

2. **Application Layer**:
   - FastAPI routers in the `routers` package
   - Middleware components in the `middleware` package
   - Factory pattern for dependency injection

3. **Infrastructure Layer**:
   - MongoDB implementations in `repository/implementation/mongodb`
   - Service implementations in `services/implementation`
   - Cloud storage integration in storage service

### Adding New Features
When adding new features, follow this workflow:
1. Define domain models in the `models` package
2. Create repository interfaces in `repository/interfaces/domains`
3. Implement repositories in `repository/implementation/mongodb`
4. Define service interfaces and implement them
5. Create new routers and register them in `main.py`

### Running Tests
```
# TODO: Add tests
```

### Code Style
This project follows PEP 8 guidelines for Python code.

## License
[MIT License](LICENSE)