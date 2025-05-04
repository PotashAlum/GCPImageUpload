#!/bin/bash
# Script to build and deploy to Google Cloud Run

PROJECT_ID="your-gcp-project-id"
IMAGE_NAME="user-image-service"
REGION="us-central1"
SERVICE_NAME="user-image-service"

# Build the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/user_image_db?retryWrites=true&w=majority,GCS_BUCKET_NAME=user-images-bucket,API_KEYS=your-api-key-1,your-api-key-2"
