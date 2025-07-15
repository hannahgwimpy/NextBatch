#!/bin/bash
# scripts/build-containers.sh

set -e

ECR_REGISTRY="YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com"
ECR_REPO="nextflow-containers"

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_REGISTRY

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names $ECR_REPO --region us-east-1 || \
    aws ecr create-repository --repository-name $ECR_REPO --region us-east-1

# Build and push base container
echo "Building and pushing base container..."
docker build -t $ECR_REGISTRY/$ECR_REPO:base -f Dockerfile.base .
docker push $ECR_REGISTRY/$ECR_REPO:base

# Build and push tool-specific containers
for tool in bwa samtools gatk; do
    echo "Building and pushing $tool container..."
    docker build -t $ECR_REGISTRY/$ECR_REPO:$tool -f Dockerfile.$tool .
    docker push $ECR_REGISTRY/$ECR_REPO:$tool
done

echo "All containers built and pushed successfully."
