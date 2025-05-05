#!/bin/bash
# Script to build and deploy to Google Cloud Run

PROJECT_ID="your_project_id"
IMAGE_NAME="your_image_name"
REGION="europe-west1"
SERVICE_NAME="your_service_name"
MONGODB_URI="your_mongo_db_uri"
GCS_BUCKET_NAME="your_image_bucket_name"
ROOT_API_KEY="your-root-admin-key"

# Build the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME

# Create a Cloud Storage bucket for logs if it doesn't exist
gsutil mb -p $PROJECT_ID -l $REGION gs://$PROJECT_ID-logs || true

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="MONGODB_URI=$MONGODB_URI,GCS_BUCKET_NAME=$GCS_BUCKET_NAME,ROOT_API_KEY=$ROOT_API_KEY"