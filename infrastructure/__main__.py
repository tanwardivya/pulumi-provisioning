"""Main Pulumi program - orchestrates all infrastructure components."""
import pulumi
from infrastructure.components.networking import NetworkingComponent
from infrastructure.components.s3 import S3BucketComponent
from infrastructure.components.rds import RDSComponent
from infrastructure.components.iam import IAMComponent
from infrastructure.components.ec2 import EC2Component
from infrastructure.components.ecr import ECRComponent
from infrastructure.components.route53 import Route53Component
from infrastructure.components.acm import ACMComponent
from infrastructure.config import get_config


# Load configuration
config = get_config()
stack = pulumi.get_stack()
env = config["environment"]

# Create networking infrastructure
networking = NetworkingComponent(
    f"{stack}-networking",
    config["networking"]
)

# Create S3 bucket
s3 = S3BucketComponent(
    f"{stack}-storage",
    config["s3"]
)

# Create ECR repository
ecr = ECRComponent(
    f"{stack}-ecr",
    config["ecr"]
)

# Create RDS database
rds = RDSComponent(
    f"{stack}-database",
    config["rds"],
    subnet_ids=networking.private_subnet_ids,
    security_group_id=networking.rds_security_group.id
)

# Create IAM role for EC2
iam = IAMComponent(
    f"{stack}-iam",
    config["iam"],
    s3_bucket_arns=[s3.bucket_arn],
    rds_instance_arn=rds.db_instance.arn,  # Direct Output, no need for apply
    ecr_repository_arn=ecr.repository_arn
)

# User data script for EC2 (install Docker, Nginx, pull from ECR, etc.)
ecr_repo_url = ecr.url
s3_bucket_name = s3.bucket_name
rds_endpoint = rds.address
rds_db_name = config["rds"].db_name
stack_name = stack

user_data = pulumi.Output.all(ecr_repo_url, s3_bucket_name, rds_endpoint).apply(
    lambda args: f"""#!/bin/bash
set -e

yum update -y
yum install -y docker nginx aws-cli
systemctl start docker
systemctl enable docker
systemctl start nginx
systemctl enable nginx
usermod -aG docker ec2-user

# Get AWS region from instance metadata
AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin {args[0]}

# Get DB password from Parameter Store (should be created separately for security)
# For now, using a placeholder - update this to use Parameter Store
DB_PASSWORD=$(aws ssm get-parameter --name /pulumi/{stack_name}/db_password --with-decryption --query 'Parameter.Value' --output text 2>/dev/null || echo '')

# Stop existing container if running
docker stop fastapi-app 2>/dev/null || true
docker rm fastapi-app 2>/dev/null || true

# Pull latest image from ECR
docker pull {args[0]}:latest || docker pull {args[0]}:test || echo "Image pull failed, will use cached image"

# Run FastAPI container
docker run -d --name fastapi-app --restart unless-stopped -p 8000:8000 \\
  -e AWS_REGION=$AWS_REGION \\
  -e S3_BUCKET_NAME={args[1]} \\
  -e DB_HOST={args[2]} \\
  -e DB_PORT=5432 \\
  -e DB_NAME={rds_db_name} \\
      -e DB_USER=dbadmin \\
  -e DB_PASSWORD=$DB_PASSWORD \\
  {args[0]}:latest || echo "Container start failed - check logs: docker logs fastapi-app"
"""
)

# Create EC2 instance
ec2 = EC2Component(
    f"{stack}-server",
    config["ec2"],
    subnet_id=networking.public_subnets[0].id,
    security_group_id=networking.ec2_security_group.id,
    iam_instance_profile_name=iam.instance_profile_name,
    user_data=user_data
)

# Optional: Route53 and ACM (if domain configured)
domain_name = pulumi.Config().get("domainName")
if domain_name:
    route53 = Route53Component(
        f"{stack}-dns",
        domain_name
    )
    
    # Create A record
    route53.create_a_record(
        domain_name,
        ec2.public_ip
    )
    
    # Create SSL certificate
    acm = ACMComponent(
        f"{stack}-ssl",
        domain_name,
        zone_id=route53.zone_id
    )

# Export outputs
pulumi.export("vpc_id", networking.vpc_id)
pulumi.export("s3_bucket_name", s3.bucket_name)
pulumi.export("rds_endpoint", rds.endpoint)
pulumi.export("rds_address", rds.address)
pulumi.export("ecr_repository_url", ecr.url)
pulumi.export("ecr_repository_name", ecr.repository_name)
pulumi.export("ec2_public_ip", ec2.public_ip)
pulumi.export("ec2_instance_id", ec2.instance_id)

if domain_name:
    pulumi.export("domain_name", domain_name)
    pulumi.export("route53_zone_id", route53.zone_id)

