# AWS Batch + Nextflow Infrastructure Template

This project provides a comprehensive template for running Nextflow workflows on AWS Batch. It includes infrastructure as code, container management scripts, a workflow launcher, and a monitoring dashboard.

## Project Structure

```
.
├── Dockerfile.base         # Base image for tool containers
├── Dockerfile.bwa            # Dockerfile for bwa
├── Dockerfile.gatk           # Dockerfile for gatk
├── Dockerfile.samtools       # Dockerfile for samtools
├── infrastructure
│   └── cloudformation-template.yaml # AWS resources (VPC, Batch, S3, EFS, IAM)
├── launcher.py             # Python script to submit workflows
├── monitor.py              # Flask app for monitoring jobs
├── nextflow-advanced.config # Advanced Nextflow features (retries, spot config)
├── nextflow.config         # Main Nextflow configuration for AWS Batch
├── params.json             # Example parameters file for a workflow
├── README.md               # This file
├── scripts
│   └── build-containers.sh   # Script to build and push Docker containers to ECR
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

1.  **Update Placeholders**: Before deploying, you may want to review `infrastructure/cloudformation-template.yaml` for any customizations.

2.  **Deploy the Stack**:

    ```bash
    aws cloudformation create-stack \
        --stack-name nextbatch \
        --template-body file://infrastructure/cloudformation-template.yaml \
        --capabilities CAPABILITY_IAM
    ```

3.  **Get Stack Outputs**: Once the stack is created, note the outputs, especially `WorkflowBucketName`, `BatchJobQueueArn`, and `NextflowJobRoleArn`. You will need these for the next steps.

    ```bash
    aws cloudformation describe-stacks --stack-name nextbatch --query "Stacks[0].Outputs"
    ```

### 2. Update Configuration Files

Update `nextflow.config` with the outputs from your CloudFormation stack:

-   `queue`: Set to your Batch Job Queue name (e.g., `nextbatch-job-queue`).
-   `jobRole`: Set to the `NextflowJobRoleArn`.
-   `workDir`: Update the bucket name to your `WorkflowBucketName`.

### 3. Build and Push Containers

The `scripts/build-containers.sh` script builds the Docker images and pushes them to Amazon ECR.

1.  **Update Placeholders**: Edit `scripts/build-containers.sh` and replace `YOUR_ACCOUNT_ID` with your AWS Account ID.

2.  **Run the script**:

    ```bash
    ./scripts/build-containers.sh
    ```

    This will create an ECR repository named `nextflow-containers` if it doesn't exist, and then build and push the base and tool-specific containers.

### 4. Run a Workflow

The `launcher.py` script provides a convenient way to submit Nextflow workflows to AWS Batch.

1.  **Update `params.json`**: Modify `params.json` with the actual S3 paths for your input data and desired output location.

2.  **Run the launcher**:

    ```bash
    python launcher.py \
        --workflow https://github.com/nf-core/rnaseq \
        --params params.json \
        --bucket <your-workflow-bucket-name> \
        --queue <your-batch-job-queue-name>
    ```

### 5. Monitor the Workflow

You can monitor the progress of your workflow in a few ways:

-   **Nextflow Log**: Use the job name to get logs:

    ```bash
    nextflow log <job-name>
    ```

-   **Monitoring Dashboard**: Run the Flask application:

    ```bash
    python monitor.py --queue <your-batch-job-queue-name>
    ```

    Then, open your browser to `http://127.0.0.1:5000/dashboard` to see a list of running jobs.

## Advanced Configuration

The `nextflow-advanced.config` file provides examples of more advanced features:

-   **Checkpointing**: Automatically saves progress to S3.
-   **Error Retries**: Implements a retry strategy for common spot instance termination errors.
-   **Dynamic Instance Selection**: Uses a larger instance type on retry.

To use these features, you can combine the configs when running Nextflow, or merge them into your main `nextflow.config` file.
