import pytest
import boto3
import os
import json
import sys
from moto import mock_aws

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lambda_function.handler import generate_samplesheet

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

@pytest.fixture
def mock_env_vars(aws_credentials):
    """Set up mocked environment variables for the Lambda function."""
    os.environ['DYNAMODB_TABLE'] = 'test-table'
    os.environ['S3_BUCKET'] = 'test-bucket'

@mock_aws
def test_generate_samplesheet_success(mock_env_vars):
    """Tests the successful generation of a samplesheet."""
    # 1. Setup Mock AWS environment
    s3_client = boto3.client('s3', region_name='us-east-1')
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    # Create mock S3 bucket
    bucket_name = os.environ['S3_BUCKET']
    s3_client.create_bucket(Bucket=bucket_name)

    # Create mock DynamoDB table
    table_name = os.environ['DYNAMODB_TABLE']
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[{'AttributeName': 'experiment_id', 'KeyType': 'HASH'}, {'AttributeName': 'sample_id', 'KeyType': 'RANGE'}],
        AttributeDefinitions=[{'AttributeName': 'experiment_id', 'AttributeType': 'S'}, {'AttributeName': 'sample_id', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    # 2. Populate with test data
    experiment_id = 'EXP001'
    sample_id = 'SAM001'
    s3_key = f'raw_data/{sample_id}.fastq.gz'

    # Add item to DynamoDB
    table.put_item(Item={
        'experiment_id': experiment_id,
        'sample_id': sample_id,
        's3_object_key': s3_key,
        'experimental_group': 'treatment',
        'treatment': 'drug_x'
    })

    # Create S3 object and add tags
    s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body='dummy-content')
    s3_client.put_object_tagging(
        Bucket=bucket_name,
        Key=s3_key,
        Tagging={'TagSet': [{'Key': 'fastq_2', 'Value': 'raw_data/SAM001_R2.fastq.gz'}]}
    )

    # 3. Call the handler
    event = {
        'body': json.dumps({'experiment_id': experiment_id})
    }
    response = generate_samplesheet(event, {}, dynamodb=dynamodb, s3_client=s3_client)

    # 4. Assert the response
    assert response['statusCode'] == 200
    assert 'text/csv' in response['headers']['Content-Type']
    
    body = response['body']
    expected_csv = (
        'sample,fastq_1,fastq_2,experimental_group,treatment\r\n' # Note csv module uses \r\n
        'SAM001,s3://test-bucket/raw_data/SAM001.fastq.gz,raw_data/SAM001_R2.fastq.gz,treatment,drug_x\r\n'
    )
    assert body == expected_csv

@mock_aws
def test_generate_samplesheet_not_found(mock_env_vars):
    """Tests the case where no samples are found for an experiment_id."""
    # Setup mock AWS environment
    s3_client = boto3.client('s3', region_name='us-east-1')
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    # Create mock S3 bucket
    s3_client.create_bucket(Bucket=os.environ['S3_BUCKET'])

    # Create mock DynamoDB table (but don't add items)
    dynamodb.create_table(
        TableName=os.environ['DYNAMODB_TABLE'],
        KeySchema=[{'AttributeName': 'experiment_id', 'KeyType': 'HASH'}, {'AttributeName': 'sample_id', 'KeyType': 'RANGE'}],
        AttributeDefinitions=[{'AttributeName': 'experiment_id', 'AttributeType': 'S'}, {'AttributeName': 'sample_id', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
    )

    event = {
        'body': json.dumps({'experiment_id': 'EXP_NOT_FOUND'})
    }
    response = generate_samplesheet(event, {}, dynamodb=dynamodb, s3_client=s3_client)

    assert response['statusCode'] == 404
    assert 'No samples found' in response['body']
