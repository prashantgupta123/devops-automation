#!/bin/bash

# AWS Security Breach Notification - Deployment Script
# This script packages the Python layer and creates a new Lambda layer version

set -e

LAYER_NAME="AWS-Generic-Security"
REGION="${AWS_REGION:-us-east-1}"
RUNTIME="python3.14"

echo "=========================================="
echo "AWS Security Breach Notification Deployment"
echo "=========================================="
echo ""

# Navigate to python directory
cd python

echo "✓ Verifying directory structure..."
if [ ! -d "core" ] || [ ! -d "handlers" ] || [ ! -d "services" ] || [ ! -d "utils" ]; then
    echo "✗ Error: Required directories not found"
    exit 1
fi

if [ ! -f "main.py" ]; then
    echo "✗ Error: main.py not found"
    exit 1
fi

echo "✓ Directory structure verified"
echo ""

# Create layer package
echo "Creating Lambda layer package..."
cd ..
rm -f layer.zip
cd python
zip -r ../layer.zip * -x "*.pyc" -x "__pycache__/*" -x ".gitignore" -x "test_*.py"
cd ..

echo "✓ Layer package created: layer.zip"
echo ""

# Publish layer version
echo "Publishing Lambda layer version..."
LAYER_VERSION=$(aws lambda publish-layer-version \
    --layer-name "$LAYER_NAME" \
    --description "Security monitoring layer - Refactored" \
    --zip-file fileb://layer.zip \
    --compatible-runtimes "$RUNTIME" \
    --region "$REGION" \
    --query 'Version' \
    --output text)

echo "✓ Layer published successfully"
echo "  Layer Name: $LAYER_NAME"
echo "  Version: $LAYER_VERSION"
echo "  Region: $REGION"
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update CloudFormation stack with LambdaLayerVersion=$LAYER_VERSION"
echo "2. Test with sample events"
echo "3. Monitor CloudWatch Logs: /aws/lambda/AWS-Generic-Security-$REGION"
echo ""
