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
# Log everything to a file for debugging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
set -x

echo "=== Starting user data script ==="
date

# Install packages (don't fail on update)
yum update -y || true
yum install -y docker nginx aws-cli || exit 1

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

# Start and enable Nginx
systemctl start nginx || true
systemctl enable nginx

# Get AWS region from instance metadata
AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
echo "AWS Region: $AWS_REGION"

# Login to ECR (retry up to 3 times)
echo "Logging into ECR..."
ECR_LOGIN_SUCCESS=false
for i in $(seq 1 3); do
    if aws ecr get-login-password --region $AWS_REGION 2>/dev/null | docker login --username AWS --password-stdin {args[0]} 2>/dev/null; then
        echo "ECR login successful"
        ECR_LOGIN_SUCCESS=true
        break
    fi
    echo "ECR login attempt $i failed, retrying..."
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

# Pull latest image from ECR (try multiple tags)
echo "Pulling Docker image from ECR..."
IMAGE_PULLED=false
for tag in latest test main; do
    if docker pull {args[0]}:$tag 2>/dev/null; then
        echo "Successfully pulled image with tag: $tag"
        IMAGE_TAG=$tag
        IMAGE_PULLED=true
        break
    fi
done

if [ "$IMAGE_PULLED" = false ]; then
    echo "ERROR: Failed to pull image from ECR. Available images:"
    aws ecr list-images --repository-name pulumi-provisioning-test --region $AWS_REGION || true
    echo "Container will not start without an image"
    exit 1
fi

# Run FastAPI container
echo "Starting FastAPI container..."
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
    exit 1
fi

# Create systemd service for automatic container updates
echo "Creating systemd service for automatic container updates..."
cat > /etc/systemd/system/fastapi-updater.service << 'SERVICE_EOF'
[Unit]
Description=FastAPI Container Auto-Updater
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/fastapi-update.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Create update script
cat > /usr/local/bin/fastapi-update.sh << 'SCRIPT_EOF'
#!/bin/bash
set -e

ECR_REPO_URL="{args[0]}"
AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
S3_BUCKET="{args[1]}"
RDS_ADDRESS="{args[2]}"
DB_NAME="{rds_db_name}"
DB_USER=dbadmin

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URL

# Get DB password from Parameter Store
DB_PASSWORD=$(aws ssm get-parameter --name /pulumi/{stack_name}/db_password --with-decryption --query 'Parameter.Value' --output text 2>/dev/null || echo '')

# Pull latest image
docker pull $ECR_REPO_URL:latest || docker pull $ECR_REPO_URL:test || true

# Restart container if it's not running
if ! docker ps | grep -q fastapi-app; then
    echo "Container not running, starting it..."
    docker stop fastapi-app 2>/dev/null || true
    docker rm fastapi-app 2>/dev/null || true
    docker run -d --name fastapi-app --restart unless-stopped -p 8000:8000 \
      -e AWS_REGION=$AWS_REGION \
      -e S3_BUCKET_NAME=$S3_BUCKET \
      -e DB_HOST=$RDS_ADDRESS \
      -e DB_PORT=5432 \
      -e DB_NAME=$DB_NAME \
      -e DB_USER=$DB_USER \
      -e DB_PASSWORD="$DB_PASSWORD" \
      $ECR_REPO_URL:latest || $ECR_REPO_URL:test
fi
SCRIPT_EOF

chmod +x /usr/local/bin/fastapi-update.sh

# Create manual deployment script (can be run via SSH)
cat > /usr/local/bin/deploy-app.sh << 'DEPLOY_EOF'
#!/bin/bash
set -e

echo "=== FastAPI Deployment Script ==="
date

ECR_REPO_URL="{args[0]}"
AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)
S3_BUCKET="{args[1]}"
RDS_ADDRESS="{args[2]}"
DB_NAME="{rds_db_name}"
DB_USER=dbadmin

echo "ECR Repository: $ECR_REPO_URL"
echo "AWS Region: $AWS_REGION"

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URL || exit 1

# Get DB password from Parameter Store
echo "Getting DB password from Parameter Store..."
DB_PASSWORD=$(aws ssm get-parameter --name /pulumi/{stack_name}/db_password --with-decryption --query 'Parameter.Value' --output text 2>/dev/null || echo '')
if [ -z "$DB_PASSWORD" ]; then
    echo "WARNING: DB password not found in Parameter Store"
fi

# Pull latest image (try latest, then test)
echo "Pulling latest Docker image..."
IMAGE_PULLED=false
for tag in latest test; do
    if docker pull $ECR_REPO_URL:$tag 2>/dev/null; then
        echo "Successfully pulled image with tag: $tag"
        IMAGE_TAG=$tag
        IMAGE_PULLED=true
        break
    fi
done

if [ "$IMAGE_PULLED" = false ]; then
    echo "ERROR: Failed to pull image from ECR"
    exit 1
fi

# Stop and remove existing container
echo "Stopping existing container..."
docker stop fastapi-app 2>/dev/null || true
docker rm fastapi-app 2>/dev/null || true

# Start new container
echo "Starting new container with image: $ECR_REPO_URL:$IMAGE_TAG"
docker run -d --name fastapi-app --restart unless-stopped -p 8000:8000 \
  -e AWS_REGION=$AWS_REGION \
  -e S3_BUCKET_NAME=$S3_BUCKET \
  -e DB_HOST=$RDS_ADDRESS \
  -e DB_PORT=5432 \
  -e DB_NAME=$DB_NAME \
  -e DB_USER=$DB_USER \
  -e DB_PASSWORD="$DB_PASSWORD" \
  -e IMAGE_TAG=$IMAGE_TAG \
  -e IMAGE_URI=$ECR_REPO_URL:$IMAGE_TAG \
  $ECR_REPO_URL:$IMAGE_TAG

# Verify container is running
sleep 5
if docker ps | grep -q fastapi-app; then
    echo "✅ Container started successfully"
    echo "Container logs (last 20 lines):"
    docker logs fastapi-app | tail -20
else
    echo "❌ Container failed to start"
    echo "Container logs:"
    docker logs fastapi-app || true
    exit 1
fi

echo "=== Deployment completed ==="
date
DEPLOY_EOF

chmod +x /usr/local/bin/deploy-app.sh
echo "Manual deployment script created at /usr/local/bin/deploy-app.sh"

# Create image verification script
cat > /usr/local/bin/check-image-version.sh << 'CHECK_EOF'
#!/bin/bash
set -e

ECR_REPO_URL="{args[0]}"
AWS_REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)

echo "=== Image Version Check ==="
echo "ECR Repository: $ECR_REPO_URL"
echo "AWS Region: $AWS_REGION"
echo ""

# Check what's currently running
if docker ps --format "{{.Names}}" | grep -q "^fastapi-app$"; then
    CURRENT_IMAGE=$(docker inspect fastapi-app --format='{{.Config.Image}}' 2>/dev/null || echo "unknown")
    CURRENT_ID=$(docker inspect fastapi-app --format='{{.Id}}' 2>/dev/null || echo "unknown")
    echo "Container is running"
    echo "Current Image: $CURRENT_IMAGE"
    echo "Current Image ID: $CURRENT_ID"
else
    echo "ERROR: Container is NOT running"
    CURRENT_IMAGE="none"
fi

echo ""
echo "Checking ECR for latest images..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION 2>/dev/null | docker login --username AWS --password-stdin $ECR_REPO_URL 2>/dev/null || echo "WARNING: Could not login to ECR"

# Get latest image digest from ECR
echo ""
echo "Latest images in ECR:"
for tag in latest test; do
    IMAGE_URI="$ECR_REPO_URL:$tag"
    DIGEST=$(aws ecr describe-images --repository-name $(echo $ECR_REPO_URL | cut -d'/' -f2) --image-ids imageTag=$tag --region $AWS_REGION --query 'imageDetails[0].imageDigest' --output text 2>/dev/null || echo "not found")
    PUSHED=$(aws ecr describe-images --repository-name $(echo $ECR_REPO_URL | cut -d'/' -f2) --image-ids imageTag=$tag --region $AWS_REGION --query 'imageDetails[0].imagePushedAt' --output text 2>/dev/null || echo "unknown")
    
    if [ "$DIGEST" != "not found" ] && [ "$DIGEST" != "None" ]; then
        echo "  Tag: $tag"
        echo "    Digest: $DIGEST"
        echo "    Pushed: $PUSHED"
        
        # Check if we have this image locally
        if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^$IMAGE_URI$"; then
            LOCAL_DIGEST=$(docker inspect $IMAGE_URI --format='{{index .RepoDigests 0}}' 2>/dev/null | cut -d'@' -f2 || echo "unknown")
            if [ "$LOCAL_DIGEST" != "unknown" ] && echo "$LOCAL_DIGEST" | grep -q "sha256:"; then
                DIGEST_SHORT=$(echo "$LOCAL_DIGEST" | cut -c1-20)
                echo "    Local: Available (digest: $DIGEST_SHORT...)"
            else
                echo "    Local: Available but digest unknown"
            fi
        else
            echo "    Local: Not available"
        fi
    else
        echo "  Tag: $tag - Not found in ECR"
    fi
    echo ""
done

# Compare current running image with latest
if [ "$CURRENT_IMAGE" != "none" ] && [ "$CURRENT_IMAGE" != "unknown" ]; then
    echo "=== Comparison ==="
    LATEST_URI="$ECR_REPO_URL:latest"
    if echo "$CURRENT_IMAGE" | grep -q "$LATEST_URI"; then
        echo "Running latest image tag"
    else
        echo "WARNING: Running: $CURRENT_IMAGE"
        echo "   Latest available: $LATEST_URI"
        echo "   Consider running: sudo /usr/local/bin/deploy-app.sh"
    fi
fi

echo ""
echo "=== Quick Check Commands ==="
echo "Check running container: docker ps | grep fastapi-app"
echo "Check container image: docker inspect fastapi-app --format='{{.Config.Image}}'"
echo "Check container logs: docker logs fastapi-app --tail 50"
echo "Deploy latest: sudo /usr/local/bin/deploy-app.sh"
CHECK_EOF

chmod +x /usr/local/bin/check-image-version.sh
echo "Image verification script created at /usr/local/bin/check-image-version.sh"

# Create timer for periodic updates (every 5 minutes)
cat > /etc/systemd/system/fastapi-updater.timer << 'TIMER_EOF'
[Unit]
Description=FastAPI Container Auto-Updater Timer
Requires=fastapi-updater.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
TIMER_EOF

# Enable and start the timer
systemctl daemon-reload
systemctl enable fastapi-updater.timer
systemctl start fastapi-updater.timer

echo "=== User data script completed ==="
echo "Automatic container updater service installed and enabled"
date
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

