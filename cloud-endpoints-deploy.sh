#!/bin/bash
# Script to deploy Cloud Endpoints and Cloud Run with ESPv2

set -e

# Variables
PROJECT_ID="ancient-acumen-458608-u2"
SERVICE_NAME="user-image-service"
REGION="europe-west1"
IMAGE_NAME="user-image-service"
API_TITLE="User Image Management Service"
API_VERSION="v1"
ENDPOINTS_SERVICE_NAME="user-image-service-endpoints"
OPENAPI_YAML="openapi-spec.yaml"
MONGODB_URI="mongodb+srv://alamgirnasir:Zr2b8X9TbLmezWjH@sereacttest.cfhjzb6.mongodb.net/?retryWrites=true&w=majority&appName=SereactTest"
GCS_BUCKET_NAME="user-images-bucket"
ROOT_API_KEY="your-root-admin-key"

# Ensure required commands are installed
command -v gcloud >/dev/null 2>&1 || { echo "gcloud is required but not installed. Aborting."; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "curl is required but not installed. Aborting."; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "jq is required but not installed. Aborting."; exit 1; }
command -v envsubst >/dev/null 2>&1 || { echo "envsubst is required but not installed. Aborting."; exit 1; }

echo "======= Setting up Google Cloud Endpoints with ESPv2 ======="

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable \
  servicemanagement.googleapis.com \
  servicecontrol.googleapis.com \
  endpoints.googleapis.com \
  artifactregistry.googleapis.com \
  run.googleapis.com

# Get the project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

# Create temporary working directory
TMP_DIR=$(mktemp -d)
echo "Working in temporary directory: $TMP_DIR"

# Create a copy of the OpenAPI spec
cp $OPENAPI_YAML $TMP_DIR/

# First, deploy the Cloud Run service without ESP
echo "Building and deploying the base Cloud Run service..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME

# Deploy to Cloud Run first to get the URL
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --no-allow-unauthenticated \
  --set-env-vars="MONGODB_URI=$MONGODB_URI,GCS_BUCKET_NAME=$GCS_BUCKET_NAME,ROOT_API_KEY=$ROOT_API_KEY"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format="value(status.url)" | sed 's/https:\/\///')

echo "Service URL: $SERVICE_URL"

# Update OpenAPI spec with the correct host
sed -i "s/user-image-service-xxxx-xx.a.run.app/$SERVICE_URL/g" $TMP_DIR/$OPENAPI_YAML

# Deploy the Endpoints configuration
echo "Deploying Endpoints configuration..."
ENDPOINTS_SERVICE_CONFIG_ID=$(gcloud endpoints services deploy $TMP_DIR/$OPENAPI_YAML \
  --project $PROJECT_ID \
  --format="value(serviceConfig.id)")

echo "Endpoints service config ID: $ENDPOINTS_SERVICE_CONFIG_ID"

# Create or update ESP service account
ESP_SERVICE_ACCOUNT="esp-$SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts describe $ESP_SERVICE_ACCOUNT --project $PROJECT_ID &>/dev/null || \
  gcloud iam service-accounts create esp-$SERVICE_NAME \
    --display-name="ESP service account for $SERVICE_NAME" \
    --project $PROJECT_ID

# Grant necessary roles to ESP service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$ESP_SERVICE_ACCOUNT" \
  --role="roles/servicemanagement.serviceController"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$ESP_SERVICE_ACCOUNT" \
  --role="roles/servicecontrol.serviceAgent"

# Create or update API key for testing
echo "Creating API key for testing..."
API_KEY_NAME="test-key-for-$SERVICE_NAME"

# Check if API key already exists
if gcloud alpha services api-keys list --filter="displayName:$API_KEY_NAME" --format="value(name)" | grep -q .; then
  KEY_NAME=$(gcloud alpha services api-keys list --filter="displayName:$API_KEY_NAME" --format="value(name)")
  echo "API key $API_KEY_NAME already exists with ID: $KEY_NAME"
else
  # Create new API key
  KEY_NAME=$(gcloud alpha services api-keys create --display-name="$API_KEY_NAME" --api-target=service=$SERVICE_URL --format="value(name)")
  echo "Created new API key with ID: $KEY_NAME"
fi

# Get the actual key string
API_KEY_STRING=$(gcloud alpha services api-keys get-key-string $KEY_NAME --format="value(keyString)")
echo "API Key String: $API_KEY_STRING"

# Deploy ESPv2 sidecar with Cloud Run
echo "Deploying Cloud Run service with ESPv2 sidecar..."
gcloud run deploy $SERVICE_NAME \
  --image="gcr.io/endpoints-release/endpoints-runtime-serverless:2" \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="ESPv2_ARGS=--cors_preset=basic,--service=$SERVICE_URL,--rollout_strategy=managed,--service_control_check_timeout_ms=1000,--service_control_quota_timeout_ms=1000,--service_control_report_timeout_ms=2000" \
  --service-account=$ESP_SERVICE_ACCOUNT \
  --cpu=1 \
  --memory=512Mi \
  --concurrency=80 \
  --max-instances=10 \
  --ingress=all

# Get the ESP URL
ESP_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format="value(status.url)")

echo "ESPv2 proxy URL: $ESP_URL"

# Test the API with the generated API key
echo "Testing the API..."
curl -s -X GET "$ESP_URL/teams?key=$API_KEY_STRING" -H "Content-Type: application/json" | jq

echo "===== Cloud Endpoints ESPv2 deployment complete ====="
echo "API Base URL: $ESP_URL"
echo "API Key for testing: $API_KEY_STRING"
echo ""
echo "Example API call:"
echo "curl -s -X GET \"$ESP_URL/teams?key=$API_KEY_STRING\" -H \"Content-Type: application/json\" | jq"
echo ""
echo "To create API keys for production use, visit:"
echo "https://console.cloud.google.com/apis/credentials?project=$PROJECT_ID"

# Cleanup
rm -rf $TMP_DIR