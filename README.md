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

- [AWS CLI](https://aws.amazon.com/cli/) installed and configured with a profile (e.g., `saml`).
- An AWS account with permissions to deploy CloudFormation stacks. If your permissions are restricted, you will need to obtain existing IAM Role ARNs from your administrator.
- [Python 3](https://www.python.org/downloads/) and `boto3` installed (`pip install boto3`).

### Deploying the Infrastructure

The infrastructure is split into two CloudFormation stacks for modularity:
1.  **VPC Stack**: Creates the networking foundation.
2.  **Application Stack**: Deploys the AWS Batch, S3, EFS, and other application resources into the existing VPC.

Due to potential IAM restrictions in enterprise AWS accounts, the recommended deployment method is through the AWS Console.

#### Manual Deployment (AWS Console)

**Prerequisites:**
- You are logged into the correct AWS account and have assumed a role with sufficient permissions.
- You have identified the AWS Region you will be deploying to (e.g., `us-east-2`).

**Step 1: Deploy the VPC Stack**

1.  In the AWS CloudFormation console, click **Create stack** -> **With new resources (standard)**.
2.  Upload the `infrastructure/vpc-template.yml` file.
3.  Give the stack a name (e.g., `NextBatch-VPC`).
4.  On the parameters page, you **must** provide valid Availability Zone names for your chosen region (e.g., `us-east-2a`, `us-east-2b`).
5.  Proceed through the steps and create the stack.
6.  Once the status is `CREATE_COMPLETE`, go to the **Outputs** tab and copy the `VpcId` and all of the subnet IDs. You will need these for the next step.

**Step 2: Deploy the Application Stack**

1.  Create another stack, this time uploading the `infrastructure/cloudformation-template.yaml` file.
2.  Give the stack a name (e.g., `NextBatch-App`).
3.  On the parameters page, fill in the following values carefully:

    *   `pWorkflowBucketName`: Enter a **unique, all-lowercase** bucket name (e.g., `vh-nextbatch-workflow-data`). S3 bucket names cannot contain uppercase letters.

    *   `pBatchInstanceRoleArn`: **CRITICAL:** Provide the **Instance Profile ARN** (not the Role ARN) for your Batch compute instances. It will look like this: `arn:aws:iam::123456789012:instance-profile/your-instance-profile`.

    *   `pVpcId`: Do **not** paste text. Click inside the input box and **select the VPC** you created in Step 1 from the dropdown list.

    *   `pPublicSubnetIds`, `pPrivateSubnetIds`, `pPrivateDataSubnetIds`: For all three, do **not** paste text. Click inside each box and **select the corresponding subnets** from the VPC outputs from the dropdown lists.

4.  Proceed to the final page, acknowledge the IAM resource creation, and click **Create stack**.

### Configuration Parameters

The CloudFormation template is highly customizable through its parameters. Here is a reference for the key options:

| Parameter | Description | Default Value |
| --- | --- | --- |
| `pCreateEFS` | Set to `true` to create an EFS file system. This is **recommended** for use as Nextflow's scratch directory (`-work-dir`). | `true` |
| `pCreateFlowLogs` | Set to `true` to enable VPC Flow Logs for network monitoring. | `false` |
| `pBatchInstanceRoleArn` | Provide an existing IAM Role ARN for AWS Batch instances. If left blank, a new role will be created. | `""` |
| `pSpotFleetRoleArn` | Provide an existing IAM Role ARN for the EC2 Spot Fleet. If left blank, a new role will be created. | `""` |
| `pNextflowJobRoleArn` | Provide an existing IAM Role ARN for Nextflow jobs. If left blank, a new role will be created. | `""` |
| `pLambdaExecutionRoleArn` | Provide an existing IAM Role ARN for the Lambda function. If left blank, a new role will be created. | `""` |
| `pNumberOfAzs` | The number of Availability Zones to deploy subnets into. | `2` |
| `pAz1`, `pAz2`, ... | The specific Availability Zones to use (e.g., `us-east-1a`). **Required.** | `""` |
| `pVpcCidrPrefix` | The first two octets for the VPC's CIDR block (e.g., `10.10`). The VPC will be a `/16`. | `10.10` |
| `pInstanceTypes` | Instance types for the Batch compute environment. | `optimal` |
| `pMinVcpus`, `pDesiredVcpus`, `pMaxVcpus` | vCPU scaling parameters for the Batch compute environment. | `0`, `0`, `128` |

## Using the System

Once the infrastructure is deployed, you can use the provided Python scripts to manage data and launch workflows.

### 1. Upload Data with Metadata

Use `scripts/upload_with_metadata.py` to upload data to S3 and register its metadata in DynamoDB.

```bash
python scripts/upload_with_metadata.py \
    --file-path /path/to/your/sample.fastq.gz \
    --bucket <S3BucketName-from-outputs> \
    --table-name <DynamoDBTableName-from-outputs> \
    --experiment-id EXP001 \
    --core-metadata-json '{"sample_id": "SAM001"}'
```

### 2. Launch a Workflow

Use `launcher.py` to submit a Nextflow workflow, referencing the `experiment-id` to generate a samplesheet on the fly.

```bash
python launcher.py \
    --workflow nf-core/rnaseq \
    --experiment-id EXP001 \
    --lambda-function-name <LambdaFunctionName-from-outputs> \
    --bucket <S3BucketName-from-outputs> \
    --queue <BatchJobQueueArn-from-outputs>
```
