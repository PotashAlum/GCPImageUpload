# Team Image Management API - Deployment Guide

This guide provides step-by-step instructions for deploying the Team Image Management API both locally using Docker and on Google Cloud Platform. This API is a scalable, cloud-based service for teams to securely store, organize, and retrieve images.

## Prerequisites

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (for GCP deployment)
- A Google Cloud Platform account (for GCP deployment)

## Local Deployment

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd team-image-management-api
```

### 2. Set Up Environment Variables

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

### 3. Set Up GCP Credentials for Local Development

Even for local development, you'll need GCP credentials to use Google Cloud Storage:

1. Create a service account in the Google Cloud Console with Storage Admin permissions
2. Download the JSON key file
3. Create a `credentials` directory in the project root:

```bash
mkdir -p credentials
```

4. Place the downloaded JSON key file in the `credentials` directory and rename it to `gcp-credentials.json`

### 4. Start the Application with Docker Compose

The application is containerized and can be run with Docker Compose:

```bash
docker-compose up
```

This will:
- Start a MongoDB container
- Build and start the Team Image Management API container
- Link the containers on the same network
- Mount the credentials directory into the container

### 5. Verify the Deployment

The API should now be accessible at http://localhost:8080/

Test it with a health check:

```bash
curl http://localhost:8080/health
```

You should receive a response like:

```json
{"status": "healthy"}
```

### 6. Initialize Your Environment

Follow these steps to initialize your environment:

1. Create a team using the root API key:

```bash
curl -X POST "http://localhost:8080/teams/" \
  -H "X-API-Key: your-secure-root-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Engineering Team", "description": "Product development team"}'
```

2. Use the returned `team_id` to create an admin API key:

```bash
curl -X POST "http://localhost:8080/teams/{team_id}/api-keys/" \
  -H "X-API-Key: your-secure-root-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Admin API Key", "role": "admin"}'
```

3. Continue with user and API key creation as outlined in the README.md

## Google Cloud Platform Deployment

### 1. Set Up Your GCP Project

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

### 2. Set Up MongoDB

For production, you should use MongoDB Atlas or another managed MongoDB service:

1. Create a MongoDB Atlas account at https://www.mongodb.com/cloud/atlas
2. Set up a new cluster (the free tier is sufficient for testing)
3. Configure network access to allow connections from your GCP services
4. Create a database user with appropriate permissions
5. Get your MongoDB connection string from the Atlas dashboard

### 3. Set Up Google Cloud Storage

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

### 4. Edit the Cloud Run Deployment Script

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

### 5. Deploy to Cloud Run

Make the deployment script executable and run it:

```bash
chmod +x cloud-run-deploy.sh
./cloud-run-deploy.sh
```

This script will:
1. Build the container image and push it to Google Container Registry
2. Create a Cloud Storage bucket for logs if it doesn't exist
3. Deploy the service to Cloud Run with your environment variables

### 6. Verify the Deployment

Once the deployment is complete, you should see a URL for your Cloud Run service. Verify it's working:

```bash
curl https://your-cloud-run-url.a.run.app/health
```

You should receive a response like:

```json
{"status": "healthy"}
```

### 7. Initialize Your Environment on Cloud Run

Follow the same initialization steps as for local deployment, but use your Cloud Run URL:

```bash
curl -X POST "https://your-cloud-run-url.a.run.app/teams/" \
  -H "X-API-Key: your-secure-root-api-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Engineering Team", "description": "Product development team"}'
```

## Accessing and Using the API

After deployment (either locally or on GCP), you can use the API as described in the main README.md. The hierarchical resource design follows this pattern:

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

All API requests require an API key in the `X-API-Key` header.

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

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)