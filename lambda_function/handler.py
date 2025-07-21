import os
import json
import boto3
import csv
from io import StringIO

def generate_samplesheet(event, context, dynamodb=None, s3_client=None):
    """
    Generates a Nextflow samplesheet by combining experimental context from DynamoDB
    with core sample metadata from S3 object tags.

    Args:
        event (dict): API Gateway Lambda Proxy Input Format
        context (dict): Lambda Context runtime methods and attributes
        dynamodb: A boto3 DynamoDB resource object. If not provided, a new one
                  will be created.
        s3_client: A boto3 S3 client object. If not provided, a new one will
                   be created.
    """
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')
    if not s3_client:
        s3_client = boto3.client('s3')
    """
    Generates a Nextflow samplesheet by combining experimental context from DynamoDB
    with core sample metadata from S3 object tags.
    """
    print(f"Received event: {event}")
    
    # Extract experiment_id from the Lambda event payload
    try:
        body = json.loads(event.get('body', '{}'))
        experiment_id = body.get('experiment_id')
        if not experiment_id:
            raise ValueError("experiment_id not found in request body")
    except (json.JSONDecodeError, ValueError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps(f'Error parsing request: {str(e)}')
        }

    # Get table and bucket names from environment variables
    table_name = os.environ.get('DYNAMODB_TABLE')
    bucket_name = os.environ.get('S3_BUCKET')

    if not table_name or not bucket_name:
        return {
            'statusCode': 500,
            'body': json.dumps('Error: DYNAMODB_TABLE or S3_BUCKET environment variables not set.')
        }

    table = dynamodb.Table(table_name)

    # Query DynamoDB for all samples in the experiment
    try:
        response = table.query(
            KeyConditionExpression='experiment_id = :eid',
            ExpressionAttributeValues={':eid': experiment_id}
        )
        items = response.get('Items', [])
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error querying DynamoDB: {str(e)}')
        }

    if not items:
        return {
            'statusCode': 404,
            'body': json.dumps(f'No samples found for experiment_id: {experiment_id}')
        }

    # Prepare CSV output
    output = StringIO()
    # Define header based on expected data
    header = ['sample', 'fastq_1', 'fastq_2', 'experimental_group', 'treatment'] # Add other fields as needed
    writer = csv.DictWriter(output, fieldnames=header, extrasaction='ignore')
    writer.writeheader()

    # Process each sample
    for item in items:
        try:
            s3_object_key = item.get('s3_object_key')
            if not s3_object_key:
                continue

            # Fetch core metadata from S3 object tags
            tags_response = s3_client.get_object_tagging(
                Bucket=bucket_name,
                Key=s3_object_key
            )
            s3_tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagSet', [])}

            # Combine data from DynamoDB and S3 tags
            row_data = {
                'sample': item.get('sample_id'),
                'fastq_1': f's3://{bucket_name}/{s3_object_key}',
                'fastq_2': s3_tags.get('fastq_2', ''), # Assumes fastq_2 path is in tags if it exists
                'experimental_group': item.get('experimental_group'),
                'treatment': item.get('treatment')
            }
            writer.writerow(row_data)

        except Exception as e:
            print(f"Skipping sample {item.get('sample_id')} due to error: {str(e)}")
            continue

    # Return the CSV content
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/csv'},
        'body': output.getvalue()
    }
