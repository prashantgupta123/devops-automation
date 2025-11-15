#!/bin/bash

# Create deployment package for Lambda function
echo "Creating Lambda deployment package..."

# Clean up previous builds
rm -rf package/
rm -f lambda-deployment.zip

# Create package directory
mkdir -p package

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t package/

# Copy source files
echo "Copying source files..."
cp lambda_function.py package/
cp AWSSession.py package/
cp Notification.py package/
cp input.json package/

# Create deployment zip
echo "Creating deployment zip..."
cd package
zip -r ../lambda-deployment.zip .
cd ..

# Clean up
rm -rf package/

echo "Deployment package created: lambda-deployment.zip"
echo "Ready to upload to AWS Lambda!"