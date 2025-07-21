#!/usr/bin/env python3
# launcher.py

import boto3
import argparse
import json
import os
from datetime import datetime

class NextflowLauncher:
    def __init__(self, region='us-east-1'):
        self.batch_client = boto3.client('batch', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        
    def submit_workflow(self, workflow_url, params_file, bucket_name, job_queue, job_definition, experiment_id=None, lambda_function_name=None, job_name=None):
        if not job_name:
            job_name = f"nextflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        with open(params_file, 'r') as f:
            params_data = json.load(f)

        if experiment_id:
            if not lambda_function_name:
                raise ValueError("Lambda function name must be provided when using experiment_id")

            print(f"Invoking Lambda {lambda_function_name} for experiment: {experiment_id}")
            
            # The payload for the Lambda function must be structured correctly
            payload = {
                'body': json.dumps({'experiment_id': experiment_id})
            }

            response = self.lambda_client.invoke(
                FunctionName=lambda_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            response_payload = json.loads(response['Payload'].read().decode('utf-8'))
            
            if response_payload.get('statusCode') != 200:
                raise Exception(f"Lambda function returned an error: {response_payload.get('body')}")

            samplesheet_content = response_payload.get('body')
            samplesheet_path = 'samplesheet.csv'
            with open(samplesheet_path, 'w', newline='') as f:
                f.write(samplesheet_content)

            print(f"Successfully generated {samplesheet_path} from Lambda response.")

            samplesheet_key = f"samplesheets/{job_name}.csv"
            print(f"Uploading samplesheet to s3://{bucket_name}/{samplesheet_key}")
            self.s3_client.upload_file(samplesheet_path, bucket_name, samplesheet_key)
            
            params_data['input'] = f's3://{bucket_name}/{samplesheet_key}'
        
        params_key = f"params/{job_name}.json"
        print(f"Uploading params to s3://{bucket_name}/{params_key}")
        self.s3_client.put_object(
            Body=json.dumps(params_data, indent=4),
            Bucket=bucket_name,
            Key=params_key
        )
        
        params_s3_path = f's3://{bucket_name}/{params_key}'

        print(f"Submitting job '{job_name}' to queue '{job_queue}' with definition '{job_definition}'")
        response = self.batch_client.submit_job(
            jobName=job_name,
            jobQueue=job_queue,
            jobDefinition=job_definition,
            parameters={
                'workflow': workflow_url,
                'params': params_s3_path
            },
            containerOverrides={
                'vcpus': 1,
                'memory': 1024, # in MiB
                'environment': [
                    {'name': 'NXF_MODE', 'value': 'batch'},
                    {'name': 'NXF_WORK', 'value': f's3://{bucket_name}/work'}
                ]
            }
        )
        
        return response['jobId']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Submit a Nextflow workflow to AWS Batch.')
    parser.add_argument('--workflow', required=True, help='URL of the Nextflow workflow git repository.')
    parser.add_argument('--params', required=True, help='Path to the parameters JSON file.')
    parser.add_argument('--experiment-id', required=False, help='Experiment ID to generate a samplesheet for.')
    parser.add_argument('--lambda-function-name', required=False, help='Name of the Lambda function to generate the samplesheet.')
    parser.add_argument('--name', required=False, help='Name for the job.')
    parser.add_argument('--bucket', required=True, help='S3 bucket for Nextflow work directory and parameters.')
    parser.add_argument('--queue', required=True, help='AWS Batch Job Queue name.')
    parser.add_argument('--definition', default='nextflow-runner', help='AWS Batch Job Definition name.')

    args = parser.parse_args()
    
    launcher = NextflowLauncher()
    job_id = launcher.submit_workflow(
        args.workflow, 
        args.params, 
        args.bucket,
        args.queue,
        args.definition,
        experiment_id=args.experiment_id,
        lambda_function_name=args.lambda_function_name,
        job_name=args.name
    )
    print(f"Successfully submitted job with ID: {job_id}")
