# Google Cloud Run Deployment Guide

## Prerequisites

1. **Google Cloud Account**: Sign up at https://cloud.google.com
2. **Google Cloud CLI (gcloud)**: Install from https://cloud.google.com/sdk/docs/install
3. **Docker** (optional, for local testing): Install from https://www.docker.com/get-started

## File Structure for Deployment

Your project now includes these deployment files:
- `Dockerfile` - Container configuration
- `.dockerignore` - Excludes unnecessary files from Docker build
- `.gcloudignore` - Excludes files from Cloud Run deployment
- `requirements.txt` - Updated with gunicorn for production
- `app.py` - Updated to use PORT environment variable

## Deployment Steps

### 1. Set Up Google Cloud Project

```bash
# Login to Google Cloud
gcloud auth login

# Set the project as active
gcloud config set project alert-streamer-230808

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 2. Configure Cloud Build & Artifact Registry

```bash
# Set your region (choose one close to your users)
export REGION=asia-southeast1  # or us-central1, europe-west1, etc.

# Set project ID
export PROJECT_ID=alert-streamer-230808

# Update gcloud configuration
gcloud config set run/region $REGION
```

### 3. Deploy to Cloud Run

#### Option A: Direct Deployment (Recommended)

```bash
# Deploy directly from source code (Cloud Run will build the container)
gcloud run deploy exam-helper \
  --source . \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --max-instances=10
```

#### Option B: Build and Deploy Separately

```bash
# Build the container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/exam-helper

# Deploy the container
gcloud run deploy exam-helper \
  --image gcr.io/$PROJECT_ID/exam-helper \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --max-instances=10
```

### 4. Access Your Application

After deployment completes, you'll see a service URL like:
```
https://exam-helper-xxxx-xx.a.run.app
```

Visit this URL in your browser to use your app!

## Configuration Options

### Memory & CPU
- `--memory=512Mi` - Adjust based on JSON file sizes (512Mi should be enough for your current files)
- `--cpu=1` - One CPU should be sufficient

### Scaling
- `--max-instances=10` - Maximum concurrent instances (reduce for lower costs)
- `--min-instances=0` - Default (scales to zero when not in use)
- `--min-instances=1` - Keep one instance warm (faster response, higher cost)

### Authentication
- `--allow-unauthenticated` - Public access (current setting)
- Remove this flag to require authentication

### Environment Variables

If you need to set custom environment variables:
```bash
gcloud run deploy exam-helper \
  --set-env-vars="DATA_DIR=/app/resources"
```

## Testing Locally with Docker

Before deploying, test locally:

```bash
# Build the Docker image
docker build -t exam-helper .

# Run locally
docker run -p 8080:8080 -e PORT=8080 exam-helper

# Test at http://localhost:8080
```

## Updating Your Deployment

To deploy updates:

```bash
# Simply re-run the deploy command
gcloud run deploy exam-helper \
  --source . \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated
```

## Monitoring & Logs

```bash
# View logs
gcloud run services logs read exam-helper --region=$REGION

# View service details
gcloud run services describe exam-helper --region=$REGION

# Follow logs in real-time
gcloud run services logs tail exam-helper --region=$REGION
```

## Cost Optimization

Cloud Run pricing (as of 2024):
- **Free Tier**: 2 million requests/month, 360,000 GB-seconds of memory
- Charged only when handling requests
- Scales to zero when idle (no cost)

To minimize costs:
1. Use `--min-instances=0` (default) to scale to zero
2. Adjust `--memory` to minimum needed
3. Set `--max-instances` to limit concurrent scaling

## Troubleshooting

### Build Fails
```bash
# Check build logs
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

### Service Not Responding
```bash
# Check service status
gcloud run services describe exam-helper --region=$REGION

# Check logs for errors
gcloud run services logs read exam-helper --region=$REGION --limit=50
```

### Permission Issues
```bash
# Make service publicly accessible
gcloud run services add-iam-policy-binding exam-helper \
  --region=$REGION \
  --member="allUsers" \
  --role="roles/run.invoker"
```

## Cleanup

To delete the service and avoid charges:
```bash
gcloud run services delete exam-helper --region=$REGION
```

## Custom Domain (Optional)

To use your own domain:

1. Verify domain ownership in Google Cloud Console
2. Map domain to service:
```bash
gcloud run domain-mappings create \
  --service=exam-helper \
  --domain=exam.yourdomain.com \
  --region=$REGION
```
3. Update DNS records as instructed

## Support & Resources

- Cloud Run Documentation: https://cloud.google.com/run/docs
- Pricing Calculator: https://cloud.google.com/products/calculator
- Community Support: https://stackoverflow.com/questions/tagged/google-cloud-run
