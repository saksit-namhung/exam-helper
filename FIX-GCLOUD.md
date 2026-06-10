# Fix gcloud Installation and Deploy

Your gcloud installation is corrupted. Here are solutions:

## Solution 1: Reinstall gcloud (Recommended)

### Step 1: Remove old installation
```bash
# Remove the corrupted installation
rm -rf ~/Config/google-cloud-sdk*
rm -rf ~/.config/gcloud
```

### Step 2: Install fresh gcloud
```bash
# Download and install (macOS)
curl https://sdk.cloud.google.com | bash

# Or using Homebrew
brew install google-cloud-sdk
```

### Step 3: Initialize
```bash
# Restart terminal, then:
gcloud init

# Login
gcloud auth login

# Set project
gcloud config set project alert-streamer-230808
```

### Step 4: Deploy
```bash
cd /Users/saksit/Projects/exam-helper
./deploy.sh alert-streamer-230808 asia-southeast1
```

## Solution 2: Manual Deploy via Cloud Console (Quick)

1. **Build Docker image locally:**
   ```bash
   cd /Users/saksit/Projects/exam-helper
   docker build -t exam-helper:latest .
   ```

2. **Push to Google Container Registry** (via Console):
   - Go to: https://console.cloud.google.com/gcr/images/alert-streamer-230808
   - Follow instructions to push your image

3. **Deploy via Cloud Console:**
   - Go to: https://console.cloud.google.com/run?project=alert-streamer-230808
   - Click "CREATE SERVICE"
   - Select "Deploy one revision from an existing container image"
   - Choose your pushed image
   - Set:
     - Region: asia-southeast1
     - Memory: 512 MiB
     - CPU: 1
     - Max instances: 10
     - Authentication: Allow unauthenticated
   - Click CREATE

## Solution 3: Use Cloud Shell (Easiest)

1. **Open Cloud Shell:**
   - Go to: https://console.cloud.google.com
   - Click the terminal icon (top right)

2. **Upload your project:**
   ```bash
   # In Cloud Shell, clone or upload your project
   git clone https://github.com/saksit-namhung/exam-helper.git
   cd exam-helper
   ```

3. **Deploy:**
   ```bash
   gcloud run deploy exam-helper \
     --source . \
     --region=asia-southeast1 \
     --allow-unauthenticated \
     --memory=512Mi
   ```

## Solution 4: Quick gcloud Fix (Try First)

```bash
# Unset problematic Python
unset CLOUDSDK_PYTHON

# Use system Python
export CLOUDSDK_PYTHON=/usr/bin/python3

# Try deploy
cd /Users/saksit/Projects/exam-helper
gcloud run deploy exam-helper \
  --source . \
  --region=asia-southeast1 \
  --allow-unauthenticated \
  --project=alert-streamer-230808
```

## Which Solution to Use?

- **Fastest:** Solution 3 (Cloud Shell) - 5 minutes
- **Best long-term:** Solution 1 (Reinstall gcloud) - 10 minutes  
- **No CLI needed:** Solution 2 (Console UI) - 10 minutes
- **Quick try:** Solution 4 - 2 minutes

I recommend trying Solution 4 first, then Solution 3 if that fails.
