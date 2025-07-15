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
        
    def submit_workflow(self, workflow_url, params_file, bucket_name, job_queue, job_definition, job_name=None):
        if not job_name:
            job_name = f"nextflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Upload parameters to S3
        params_key = f"params/{job_name}.json"
        print(f"Uploading params file {params_file} to s3://{bucket_name}/{params_key}")
        self.s3_client.upload_file(
            params_file, 
            bucket_name, 
            params_key
        )
        
        params_s3_path = f's3://{bucket_name}/{params_key}'

        # Submit job
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
        args.name
    )
    print(f"Successfully submitted job with ID: {job_id}")
