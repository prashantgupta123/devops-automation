#!/bin/bash
set -e

S3_BUCKET=$1
VERSION=$2

if [ -z "$S3_BUCKET" ] || [ -z "$VERSION" ]; then
  echo "Usage: $0 <s3-bucket> <version>"
  exit 1
fi
echo "Building agent version $VERSION for S3 bucket $S3_BUCKET"

# Convert version to lowercase, replace spaces with underscores, remove special characters, replace dots with underscores
VERSION=$(echo "$VERSION" | tr '[:upper:]' '[:lower:]' | tr ' ' '_' | tr -cd '[:alnum:]-._' | tr '.' '_')

echo "Cleaning up local files"
rm -f agent.zip
rm -rf package
rm -rf .venv

echo "Building agent"

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip --no-cache-dir
pip install -r requirements.txt --no-cache-dir
deactivate

echo "Packaging agent"

mkdir package || true
cp -r .venv/lib/python3.*/site-packages/* package/
cp -r main.py package/
cd package
find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
zip -r ../agent.zip *
cd ..

echo "Uploading agent to S3"

aws s3 cp agent.zip s3://$S3_BUCKET/agent-$VERSION.zip
echo "Agent uploaded to s3://$S3_BUCKET/agent-$VERSION.zip"

rm -f agent.zip
rm -rf package
rm -rf .venv

echo "Cleaned up local files"
echo "Script completed successfully"
