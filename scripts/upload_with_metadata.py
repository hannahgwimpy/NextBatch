import argparse
import json
import boto3
import os

def upload_with_metadata(file_path, bucket, key, table_name, experiment_id, context_json, core_metadata_json):
    """
    Uploads a file to S3, attaches core metadata as tags, and records the
    experimental context in a DynamoDB table.

    :param file_path: Path to the local file to upload.
    :param bucket: Name of the S3 bucket.
    :param key: S3 object key (path in the bucket).
    :param table_name: Name of the DynamoDB table for experimental contexts.
    :param experiment_id: The ID of the experiment this sample belongs to.
    :param context_json: A JSON string of the experimental context (e.g., '{"treatment": "drug_a"}').
    :param core_metadata_json: A JSON string of the core metadata to be stored as S3 tags.
    """
    s3_client = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    # 1. Parse metadata
    try:
        context_data = json.loads(context_json)
        core_metadata = json.loads(core_metadata_json)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON provided. {e}")
        return

    # 2. Upload file to S3
    print(f"Uploading {file_path} to s3://{bucket}/{key}...")
    try:
        s3_client.upload_file(file_path, bucket, key)
        print("Upload successful.")
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return

    # 3. Attach core metadata as S3 tags
    print("Attaching core metadata as S3 tags...")
    try:
        tag_set = [{'Key': k, 'Value': str(v)} for k, v in core_metadata.items()]
        s3_client.put_object_tagging(
            Bucket=bucket,
            Key=key,
            Tagging={'TagSet': tag_set}
        )
        print("Tagging successful.")
    except Exception as e:
        print(f"Error attaching S3 tags: {e}")
        return

    # 4. Record experimental context in DynamoDB
    print(f"Recording experimental context in DynamoDB table {table_name}...")
    try:
        item = {
            'experiment_id': experiment_id,
            'sample_id': core_metadata.get('sample_id', os.path.basename(key)),
            's3_object_key': key
        }
        item.update(context_data)

        table.put_item(Item=item)
        print("DynamoDB record created successfully.")
    except Exception as e:
        print(f"Error writing to DynamoDB: {e}")
        return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Upload a file to S3 with associated metadata.')
    parser.add_argument('--file-path', required=True, help='Path to the local file.')
    parser.add_argument('--bucket', required=True, help='S3 bucket name.')
    parser.add_argument('--key', required=True, help='S3 object key.')
    parser.add_argument('--table-name', required=True, help='DynamoDB table name for contexts.')
    parser.add_argument('--experiment-id', required=True, help='Experiment ID.')
    parser.add_argument('--context-json', required=True, help='JSON string for experimental context.')
    parser.add_argument('--core-metadata-json', required=True, help='JSON string for core metadata (S3 tags).')

    args = parser.parse_args()

    upload_with_metadata(
        args.file_path,
        args.bucket,
        args.key,
        args.table_name,
        args.experiment_id,
        args.context_json,
        args.core_metadata_json
    )
