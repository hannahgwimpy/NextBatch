import argparse
import boto3
import docker
import yaml
import base64
import os

# Set up argument parser
parser = argparse.ArgumentParser(description="Build and push Docker containers to ECR based on a manifest file.")
parser.add_argument("--account-id", required=True, help="Your AWS Account ID.")
parser.add_argument("--region", required=True, help="The AWS region for the ECR repository.")
parser.add_argument("--manifest", default="containers.yaml", help="Path to the container manifest file.")
args = parser.parse_args()

# Initialize clients
# Assumes AWS credentials are configured in the environment (e.g., via aws configure)
ecr_client = boto3.client("ecr", region_name=args.region)
try:
    docker_client = docker.from_env()
except docker.errors.DockerException:
    print("Error: Docker is not running or not installed. Please start Docker and try again.")
    exit(1)

def get_ecr_login():
    """Gets ECR login credentials."""
    try:
        response = ecr_client.get_authorization_token()
        auth_data = response["authorizationData"][0]
        token = auth_data["authorizationToken"]
        username, password = base64.b64decode(token).decode("utf-8").split(":")
        registry = auth_data["proxyEndpoint"]
        return username, password, registry
    except Exception as e:
        print(f"Error getting ECR credentials: {e}")
        exit(1)

def ensure_ecr_repo(repo_name):
    """Ensures the ECR repository exists."""
    try:
        ecr_client.create_repository(repositoryName=repo_name, imageScanningConfiguration={'scanOnPush': True})
        print(f"Created ECR repository: {repo_name}")
    except ecr_client.exceptions.RepositoryAlreadyExistsException:
        print(f"ECR repository {repo_name} already exists.")
    except Exception as e:
        print(f"Error creating ECR repository: {e}")
        exit(1)

def main():
    # Load the container manifest
    manifest_path = os.path.join(os.path.dirname(__file__), '..', args.manifest)
    try:
        with open(manifest_path, "r") as f:
            manifest = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Manifest file not found at {manifest_path}")
        exit(1)

    repo_name = manifest["repository"]
    containers = manifest["containers"]

    # 1. Ensure the ECR repository exists
    ensure_ecr_repo(repo_name)

    # 2. Log in to ECR
    print("\nLogging in to ECR...")
    username, password, registry = get_ecr_login()
    docker_client.login(username=username, password=password, registry=registry)
    print("Login successful.")

    # 3. Build and push each container
    for container in containers:
        name = container["name"]
        dockerfile = container["dockerfile"]
        tags = container["tags"]
        
        print(f"\n--- Building container: {name} ---")
        
        dockerfile_path = os.path.join(os.path.dirname(__file__), '..', dockerfile)
        if not os.path.exists(dockerfile_path):
            print(f"Error: Dockerfile not found at {dockerfile_path} for container {name}")
            continue

        try:
            # Build the image
            image, build_logs = docker_client.images.build(
                path=os.path.dirname(dockerfile_path),
                dockerfile=dockerfile,
                tag=f"{repo_name}/{name}:latest" # Initial local tag
            )
            print(f"Successfully built {name} from {dockerfile}")

            # Tag and push for each tag in the manifest
            for tag in tags:
                ecr_tag = f"{args.account-id}.dkr.ecr.{args.region}.amazonaws.com/{repo_name}:{name}-{tag}"
                print(f"Tagging image as: {ecr_tag}")
                image.tag(ecr_tag)
                
                print(f"Pushing {ecr_tag}...")
                # The push logs can be verbose, so we just confirm completion
                docker_client.images.push(ecr_tag)
                print(f"Successfully pushed {ecr_tag}")

        except docker.errors.BuildError as e:
            print(f"\nError building {name}: {e}")
            for line in e.build_log:
                if 'stream' in line:
                    print(line['stream'].strip())
        except docker.errors.APIError as e:
            print(f"\nDocker API error for {name}: {e}")
        except Exception as e:
            print(f"\nAn unexpected error occurred for {name}: {e}")

if __name__ == "__main__":
    main()
