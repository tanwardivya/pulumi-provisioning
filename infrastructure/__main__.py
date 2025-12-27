"""Main Pulumi program - orchestrates all infrastructure components."""
import pulumi
import pulumi_aws as aws
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
    rds_instance_arn=pulumi.Output.all(rds.db_instance.arn).apply(lambda args: args[0]),
    ecr_repository_arn=ecr.repository_arn
)

# Store database password in SSM Parameter Store for EC2 instance to retrieve
# This allows the user_data script to get the password securely
db_password = pulumi.Config().require_secret("dbPassword")
ssm_db_password = aws.ssm.Parameter(
    f"{stack}-db-password",
    name=f"/pulumi/{stack}/db_password",
    type="SecureString",
    value=db_password,
    description=f"Database password for {stack} environment",
    tags=config["tags"],
    opts=pulumi.ResourceOptions(
        additional_secret_outputs=["value"]  # Mark value as secret
    )
)

# User data script for EC2 (install Docker, Nginx, pull from ECR, etc.)
ecr_repo_url = ecr.url
s3_bucket_name = s3.bucket_name
rds_endpoint = rds.address
rds_db_name = config["rds"].db_name
stack_name = stack

user_data = pulumi.Output.all(ecr_repo_url, s3_bucket_name, rds_endpoint).apply(
    lambda args: f"""#!/bin/bash
# Log everything to a file for debugging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
set -x

echo "=== Starting user data script ==="
date

# Install packages (don't fail on update)
yum update -y || true
yum install -y docker nginx aws-cli || exit 1

# Ensure SSM agent is installed and running (should be pre-installed on AL2023)
echo "Checking SSM agent status..."
if systemctl is-active --quiet amazon-ssm-agent; then
    echo "SSM agent is already running"
else
    echo "Starting SSM agent..."
    systemctl start amazon-ssm-agent || true
    systemctl enable amazon-ssm-agent || true
    # Wait a moment for agent to start
    sleep 5
fi

# Start and enable Docker
systemctl start docker || exit 1
systemctl enable docker
usermod -aG docker ec2-user

# Wait for Docker to be ready
echo "Waiting for Docker to be ready..."
for i in $(seq 1 30); do
    if docker info >/dev/null 2>&1; then
        echo "Docker is ready"
        break
    fi
    echo "Waiting for Docker... ($i/30)"
    sleep 2
done

# Configure Nginx for FastAPI reverse proxy
echo "Configuring Nginx..."
cat > /etc/nginx/conf.d/fastapi.conf << 'NGINX_EOF'
upstream fastapi_backend {{
    server 127.0.0.1:8000;
}}

# HTTP server - proxy to FastAPI (HTTPS can be added later with SSL)
server {{
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client body size limit
    client_max_body_size 100M;

    # Proxy settings
    location / {{
        proxy_pass http://fastapi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}

    # Health check endpoint
    location /health {{
        proxy_pass http://fastapi_backend/health;
        access_log off;
    }}
}}
NGINX_EOF

# Test Nginx configuration
nginx -t && systemctl restart nginx && systemctl enable nginx || echo "Nginx configuration failed"

# Get AWS region from instance metadata
AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)

# Login to ECR with retries
echo "Logging in to ECR..."
ECR_LOGIN_SUCCESS=false
for attempt in 1 2 3; do
    if aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin {args[0]} 2>/dev/null; then
        echo "ECR login successful (attempt $attempt)"
        ECR_LOGIN_SUCCESS=true
        break
    fi
    echo "ECR login failed (attempt $attempt/3), retrying..."
    sleep 5
done

if [ "$ECR_LOGIN_SUCCESS" = false ]; then
    echo "ERROR: Failed to login to ECR after 3 attempts"
    exit 1
fi

# Get DB password from Parameter Store
echo "Getting DB password from Parameter Store..."
DB_PASSWORD=$(aws ssm get-parameter --name /pulumi/{stack_name}/db_password --with-decryption --query 'Parameter.Value' --output text 2>/dev/null || echo '')
if [ -z "$DB_PASSWORD" ]; then
    echo "WARNING: DB password not found in Parameter Store, container may fail to connect"
fi

# Stop existing container if running
echo "Stopping any existing container..."
docker stop fastapi-app 2>/dev/null || true
docker rm fastapi-app 2>/dev/null || true

# Get specific image tag from SSM Parameter Store (if available)
echo "Getting image tag from SSM Parameter Store..."
SPECIFIC_TAG=$(aws ssm get-parameter --name /pulumi/{stack_name}/image_tag --query 'Parameter.Value' --output text --region $AWS_REGION 2>/dev/null || echo "")

# Pull image with retries and fallback tags
IMAGE_PULLED=false
MAX_RETRIES=3
RETRY_DELAY=10

for attempt in $(seq 1 $MAX_RETRIES); do
    echo "Attempt $attempt/$MAX_RETRIES to pull image..."
    
    # Try specific tag first if available
    if [ -n "$SPECIFIC_TAG" ]; then
        echo "Trying specific tag from SSM: $SPECIFIC_TAG"
        if docker pull {args[0]}:$SPECIFIC_TAG 2>/dev/null; then
            echo "Successfully pulled image with specific tag: $SPECIFIC_TAG"
            IMAGE_TAG=$SPECIFIC_TAG
            IMAGE_PULLED=true
            break
        fi
        echo "Specific tag not available yet, trying fallback tags..."
    fi
    
    # Fallback to latest, test, main
    for tag in latest test main; do
        if docker pull {args[0]}:$tag 2>/dev/null; then
            echo "Successfully pulled image with fallback tag: $tag"
            IMAGE_TAG=$tag
            IMAGE_PULLED=true
            break 2
        fi
    done
    
    if [ "$IMAGE_PULLED" = false ]; then
        if [ $attempt -lt $MAX_RETRIES ]; then
            echo "Image not available yet, waiting $RETRY_DELAY seconds before retry..."
            sleep $RETRY_DELAY
        fi
    fi
done

if [ "$IMAGE_PULLED" = false ]; then
    echo "WARNING: Failed to pull image from ECR after $MAX_RETRIES attempts"
    echo "Container will not start. Image will be pulled on next deployment."
    echo "Deployments are handled automatically by CI/CD pipeline."
else
    # Run FastAPI container
    echo "Starting FastAPI container with image tag: $IMAGE_TAG"
    docker run -d --name fastapi-app --restart unless-stopped -p 8000:8000 \\
      -e AWS_REGION=$AWS_REGION \\
      -e S3_BUCKET_NAME={args[1]} \\
      -e DB_HOST={args[2]} \\
      -e DB_PORT=5432 \\
      -e DB_NAME={rds_db_name} \\
      -e DB_USER=dbadmin \\
      -e DB_PASSWORD="$DB_PASSWORD" \\
      -e IMAGE_TAG=$IMAGE_TAG \\
      -e IMAGE_URI={args[0]}:$IMAGE_TAG \\
      {args[0]}:$IMAGE_TAG
    
    # Verify container is running
    sleep 5
    if docker ps | grep -q fastapi-app; then
        echo "✅ FastAPI container started successfully"
        docker logs fastapi-app | tail -20
    else
        echo "❌ FastAPI container failed to start"
        docker logs fastapi-app || true
    fi
fi

echo "=== User data script completed ==="
echo "Container updates are handled automatically by CI/CD pipeline via SSM"
date
"""
)

# Create EC2 instance
# Ensure SSM parameter exists before EC2 instance (so user_data can retrieve password)
ec2 = EC2Component(
    f"{stack}-server",
    config["ec2"],
    subnet_id=networking.public_subnets[0].id,
    security_group_id=networking.ec2_security_group.id,
    iam_instance_profile_name=iam.instance_profile_name,
    user_data=user_data,
    opts=pulumi.ResourceOptions(depends_on=[ssm_db_password])
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

