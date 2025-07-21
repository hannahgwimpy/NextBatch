# AWS Batch + Nextflow Infrastructure Template

A comprehensive template for running Nextflow workflows on AWS Batch. It includes infrastructure as code, container management, a workflow launcher with integrated metadata management, and a monitoring dashboard.

## Project Structure

```
.
├── Dockerfile.base         # Base image for tool containers
├── Dockerfile.bwa            # Dockerfile for bwa
├── Dockerfile.gatk           # Dockerfile for gatk
├── Dockerfile.samtools       # Dockerfile for samtools
├── infrastructure
│   └── cloudformation-template.yaml # AWS resources (VPC, Batch, S3, DynamoDB, Lambda)
├── lambda
│   └── handler.py          # Lambda function for generating samplesheets
├── launcher.py             # Python script to submit workflows
├── metadata
│   └── schemas             # JSON schemas for metadata
├── modules
│   └── local               # Local Nextflow modules
├── monitor.py              # Flask app for monitoring jobs
├── nextflow-advanced.config # Advanced Nextflow features (retries, spot config)
├── nextflow.config         # Main Nextflow configuration for AWS Batch
├── params.json             # Example parameters file for a workflow
├── README.md               # This file
├── scripts
│   ├── build_manager.py    # Script to build and push Docker containers to ECR
│   └── upload_with_metadata.py # Script to upload data with metadata
└── templates
    └── dashboard.html        # HTML template for the monitoring dashboard
```

## Getting Started

### Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) installed and configured.
- [Docker](https://www.docker.com/get-started) installed.
- [Python 3](https://www.python.org/downloads/) and `boto3`, `flask` libraries installed (`pip install boto3 flask`).
- An AWS account with appropriate permissions.

### 1. Deploy the Infrastructure

The CloudFormation template in the `infrastructure` directory will create all the necessary AWS resources.

(Instructions for deploying the infrastructure remain the same)

### 2. Update Configuration Files

(Instructions for updating configuration files remain the same)

### 3. Build and Push Containers

(Instructions for building and pushing containers remain the same)

## Metadata Management

This project features a robust, cloud-native metadata management system designed to ensure your data is standardized, queryable, and reusable across multiple experiments. The system uses DynamoDB to manage experimental contexts and attaches core, immutable metadata directly to your data files in S3.

### 1. Upload Data with Metadata

To register your data with the system, use the `scripts/upload_with_metadata.py` script. This tool uploads your file to S3, attaches its core metadata (e.g., sample ID, organism) as tags, and records its experimental context (e.g., treatment group, project ID) in DynamoDB.

**Example:**

```bash
python scripts/upload_with_metadata.py \
    --file-path /path/to/your/sample_A_R1.fastq.gz \
    --bucket your-nextflow-bucket-name \
    --key raw_data/sample_A_R1.fastq.gz \
    --table-name YourStackName-ExperimentContexts \
    --experiment-id EXP001 \
    --context-json '{"experimental_group": "treatment", "treatment": "drug_x"}' \
    --core-metadata-json '{"sample_id": "SAM001", "organism": "homo_sapiens"}'
```

### 2. Launch a Workflow with an Experiment ID

Use the `launcher.py` script to submit a Nextflow workflow. When you provide an `--experiment-id`, the launcher invokes an AWS Lambda function to dynamically generate the correct samplesheet from the metadata you've stored.

**Example:**

```bash
python launcher.py \
    --workflow https://github.com/nf-core/rnaseq \
    --params params.json \
    --experiment-id EXP001 \
    --lambda-function-name YourStackName-GenerateSamplesheet \
    --bucket your-nextflow-bucket-name \
    --queue YourStackName-job-queue
```

## Monitor the Workflow

(Instructions for monitoring the workflow remain the same)

## Advanced Configuration

(Instructions for advanced configuration remain the same)
