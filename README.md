# Team Image Management API

A scalable, cloud-based service for teams to securely store, organize, and retrieve images using modern cloud technologies. Built with FastAPI, Google Cloud Storage, and MongoDB.

## Overview

This service provides:
- Hierarchical team-based resources for intuitive resource navigation
- Secure API key management with role-based permissions
- Comprehensive audit logging
- Efficient image storage and retrieval with metadata extraction
- Full deployment options for both local development and Google Cloud Platform

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

### Secure API Key Management

API keys are managed securely with the following features:
- API keys are never stored directly in the database
- A key prefix is stored for efficient lookup
- Keys are securely hashed using PBKDF2 with a unique salt for each key
- The full API key is only returned once during creation
- Authentication verifies keys by rehashing and comparing to stored hash

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

## Prerequisites

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (for GCP deployment)
- A Google Cloud Platform account (for GCP deployment)

## Deployment Options

### Local Deployment

#### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd team-image-management-api
```

#### 2. Set Up Environment Variables

Create a `.env` file in the root directory based on the provided `.env.example`:

```bash
cp .env.example .env
```

Edit the `.env` file with your local configuration:

```
# MongoDB connection string
MONGODB_URI=mongodb://mongodb:27017/user_image_db
# Google Cloud Storage bucket name
GCS_BUCKET_NAME=your-local-test-bucket
# Root API key for initial setup
ROOT_API_KEY=your-secure-root-key
```

#### 3. Set Up GCP Credentials for Local Development

Even for local development, you'll need GCP credentials to use Google Cloud Storage:

1. Create a service account in the Google Cloud Console with Storage Admin permissions
2. Download the JSON key file
3. Create a `credentials` directory in the project root:

```bash
mkdir -p credentials
```

4. Place the downloaded JSON key file in the `credentials` directory and rename it to `gcp-credentials.json`

#### 4. Start the Application with Docker Compose

The application is containerized and can be run with Docker Compose:

```bash
docker-compose up
```

This will:
- Start a MongoDB container
- Build and start the Team Image Management API container
- Link the containers on the same network
- Mount the credentials directory into the container

#### 5. Verify the Deployment

The API should now be accessible at http://localhost:8080/

Test it with a health check:

```bash
curl http://localhost:8080/health
```

You should receive a response like:

```json
{"status": "healthy"}
```

### Google Cloud Platform Deployment

#### 1. Set Up Your GCP Project

1. Create a new GCP project (or use an existing one):

```bash
gcloud projects create [PROJECT_ID] --name="[PROJECT_NAME]"
```

2. Set your project as the default:

```bash
gcloud config set project [PROJECT_ID]
```

3. Enable the required APIs:

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
```

#### 2. Set Up MongoDB

For production, you should use MongoDB Atlas or another managed MongoDB service:

1. Create a MongoDB Atlas account at https://www.mongodb.com/cloud/atlas
2. Set up a new cluster (the free tier is sufficient for testing)
3. Configure network access to allow connections from your GCP services
4. Create a database user with appropriate permissions
5. Get your MongoDB connection string from the Atlas dashboard

#### 3. Set Up Google Cloud Storage

1. Create a Cloud Storage bucket for your images:

```bash
gsutil mb -p [PROJECT_ID] -l [REGION] gs://[BUCKET_NAME]
```

2. Create a service account with Storage Admin permissions:

```bash
gcloud iam service-accounts create image-storage-admin

gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:image-storage-admin@[PROJECT_ID].iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

3. Download the service account key:

```bash
gcloud iam service-accounts keys create credentials/gcp-credentials.json \
  --iam-account=image-storage-admin@[PROJECT_ID].iam.gserviceaccount.com
```

#### 4. Edit the Cloud Run Deployment Script

Edit the `cloud-run-deploy.sh` script with your GCP project settings:

```bash
PROJECT_ID="your_project_id"
IMAGE_NAME="team-image-management-api"
REGION="europe-west1"  # Choose your preferred region
SERVICE_NAME="team-image-management-api"
MONGODB_URI="your_mongo_db_uri_from_atlas"
GCS_BUCKET_NAME="your_image_bucket_name"
ROOT_API_KEY="your-secure-root-api-key"
```

#### 5. Deploy to Cloud Run

Make the deployment script executable and run it:

```bash
chmod +x cloud-run-deploy.sh
./cloud-run-deploy.sh
```

This script will:
1. Build the container image and push it to Google Container Registry
2. Create a Cloud Storage bucket for logs if it doesn't exist
3. Deploy the service to Cloud Run with your environment variables

#### 6. Verify the Deployment

Once the deployment is complete, you should see a URL for your Cloud Run service. Verify it's working:

```bash
curl https://your-cloud-run-url.a.run.app/health
```

You should receive a response like:

```json
{"status": "healthy"}
```

## Getting Started with Authentication

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
   curl -X POST "http://localhost:8080/teams/{team_id}/users/{user_id}/api-keys" \
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
   curl -X POST "http://localhost:8080/teams/{team_id}/users/{user_id}/api-keys" \
     -H "X-API-Key: admin-api-key-from-step-3" \
     -H "Content-Type: application/json" \
     -d '{"name": "John's API Key", "role": "user"}'
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

## Configuration Options

### Environment Variables

- `MONGODB_URI`: Connection string for MongoDB
- `GCS_BUCKET_NAME`: Name of the Google Cloud Storage bucket for image storage
- `ROOT_API_KEY`: The super-admin API key for initial setup and system administration
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to the GCP service account credentials JSON file

### Custom Configurations

For more advanced configurations:

- Edit the `docker-compose.yml` file for local deployment adjustments
- Edit the `cloud-run-deploy.sh` script for GCP deployment adjustments

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

## Troubleshooting

### Common Issues with Local Deployment

1. **MongoDB connection errors**: Ensure MongoDB container is running and the connection string is correct
   ```bash
   docker ps
   # Check if MongoDB container is running and healthy
   ```

2. **GCP credentials issues**: Verify the credentials file is in the correct location
   ```bash
   ls -la credentials/
   # Should show gcp-credentials.json
   ```

3. **API key authentication failures**: Double-check the ROOT_API_KEY in your .env file matches what you're using in requests

### Common Issues with GCP Deployment

1. **Deployment failures**: Check Cloud Build logs
   ```bash
   gcloud builds list
   gcloud builds log [BUILD_ID]
   ```

2. **Runtime errors**: Check Cloud Run logs
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=[SERVICE_NAME]"
   ```

3. **MongoDB connection issues**: Verify your Atlas network settings allow connections from GCP

4. **GCS access issues**: Check the service account permissions and bucket CORS settings

## Security Best Practices

1. **API Keys**:
   - API keys are never stored in plain text in the database
   - Only a key prefix, hash, and salt are stored for secure verification
   - Rotate API keys regularly
   - Use the least privileged role necessary for each key
   - Never share API keys between users

2. **MongoDB**:
   - Use strong authentication credentials
   - Configure network access to restrict connections
   - Enable encryption at rest

3. **Google Cloud**:
   - Keep service account keys secure
   - Follow the principle of least privilege for service accounts
   - Enable Cloud Audit Logging

## API Key Security Implementation

The service implements a secure API key management system:

1. **Key Generation**: When a new API key is created, a secure random token is generated
2. **Key Storage**: 
   - Only the first 8 characters (prefix) of the key are stored for lookup
   - A unique salt is generated for each key
   - The key is hashed using PBKDF2 with 100,000 iterations
   - Only the prefix, hash, and salt are stored in the database
3. **Key Authentication**:
   - When a key is provided, the system looks up potential matches by prefix
   - For each potential match, it rehashes the provided key with the stored salt
   - If the computed hash matches the stored hash, authentication succeeds
4. **Key Verification**: This approach ensures that even if the database is compromised, the actual API keys cannot be retrieved

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)