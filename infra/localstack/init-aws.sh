#!/bin/bash
set -e

echo "Initializing LocalStack AWS resources..."

# Wait for LocalStack
until aws --endpoint-url=http://localhost:4566 s3 ls > /dev/null 2>&1; do
    echo "Waiting for LocalStack..."
    sleep 2
done

# Create S3 bucket for data lake
aws --endpoint-url=http://localhost:4566 s3 mb s3://ada-data-lake --region us-east-1 || true
aws --endpoint-url=http://localhost:4566 s3 mb s3://ada-processed --region us-east-1 || true

# Create SQS queues
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name vendas-events --region us-east-1 || true
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name financeiro-events --region us-east-1 || true

echo "LocalStack resources initialized successfully!"
echo "S3 Buckets:"
aws --endpoint-url=http://localhost:4566 s3 ls
echo "SQS Queues:"
aws --endpoint-url=http://localhost:4566 sqs list-queues --region us-east-1
