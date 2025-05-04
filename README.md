# User Image Management Service

A lightweight REST API for user account creation and image management, with cloud storage integration.

## Features

- User management (create, read, update, delete)
- Image upload and management
- Google Cloud Storage integration
- API key authentication
- Containerized deployment with Docker
- Ready for Google Cloud Run

## Setup and Installation

### Local Development

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example` with your own values
4. Start the service:
   ```
   uvicorn main:app --reload
   ```

### Google Cloud Deployment

1. Create a Google Cloud Storage bucket
2. Set up MongoDB (either locally, Atlas, or Cloud MongoDB)
3. Update the `cloud-run-deploy.sh` script with your values
4. Make the script executable and run it:
   ```
   chmod +x cloud-run-deploy.sh
   ./cloud-run-deploy.sh
   ```

## API Endpoints

### Authentication

All endpoints require an API key in the `X-API-Key` header.

### Users

- `POST /users/` - Create a new user
- `GET /users/` - List all users
- `GET /users/{user_id}` - Get a specific user
- `PUT /users/{user_id}` - Update a user
- `DELETE /users/{user_id}` - Delete a user and all their images

### Images

- `POST /users/{user_id}/images/` - Upload an image for a user
- `GET /users/{user_id}/images/` - List all images for a user
- `GET /users/{user_id}/images/{image_id}` - Get a specific image
- `PUT /users/{user_id}/images/{image_id}` - Update image metadata
- `DELETE /users/{user_id}/images/{image_id}` - Delete an image

## API Documentation

When running, API documentation is available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`