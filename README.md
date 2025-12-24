# AWS CI/CD Pipeline with Pulumi, GitHub Actions, and FastAPI

Production-ready CI/CD pipeline for deploying FastAPI applications on AWS infrastructure using Pulumi for Infrastructure as Code, GitHub Actions for CI/CD, Docker for containerization, and Nginx as a reverse proxy.

## Architecture

- **Infrastructure**: EC2, S3, RDS (PostgreSQL), VPC, IAM, Route53, ACM
- **Application**: FastAPI service with S3 and RDS operations
- **CI/CD**: GitHub Actions with OIDC authentication
- **Containerization**: Docker
- **Reverse Proxy**: Nginx with SSL/TLS
- **Environments**: Separate test and production stacks
- **Package Management**: uv (fast Python package manager)

## Project Structure

```
pulumi-provisioning/
├── app/                    # FastAPI application
│   ├── pyproject.toml     # FastAPI app dependencies
│   ├── main.py            # FastAPI app and endpoints
│   ├── config.py           # Configuration management
│   ├── models.py           # Database models
│   ├── s3_operations.py    # S3 utility functions
│   └── db_operations.py   # Database operations
├── infrastructure/         # Pulumi infrastructure code
│   ├── pyproject.toml     # Pulumi infrastructure dependencies
│   ├── __main__.py        # Main orchestrator
│   ├── config.py          # Configuration loader
│   ├── components/        # Reusable Pulumi components
│   │   ├── base.py        # Base component class
│   │   ├── networking.py  # VPCComponent
│   │   ├── s3.py          # S3BucketComponent
│   │   ├── rds.py         # RDSComponent
│   │   ├── ec2.py         # EC2Component
│   │   ├── iam.py         # IAMComponent
│   │   ├── route53.py     # Route53Component
│   │   ├── acm.py         # ACMComponent
│   │   └── ecr.py         # ECRComponent
│   └── types/             # Configuration type definitions
├── nginx/                  # Nginx configuration files
├── .github/workflows/      # GitHub Actions workflows
│   ├── test.yml           # Test environment deployment
│   ├── prod.yml            # Production deployment
│   └── destroy.yml         # Infrastructure destruction
├── Pulumi.yaml             # Pulumi project configuration
├── Pulumi.test.yaml        # Test stack configuration
├── Pulumi.prod.yaml        # Production stack configuration
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Local development
└── README.md               # This file
```

## Prerequisites

- AWS Account with appropriate permissions
- Pulumi Cloud account (https://app.pulumi.com/)
- GitHub account
- Python 3.11+
- AWS CLI configured
- Pulumi CLI installed
- uv installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker (for local testing)

## Quick Start

### 1. Install uv (if not installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv

# Or via pip
pip install uv
```

### 2. Local Setup

```bash
# Clone repository
git clone <your-repo-url>
cd pulumi-provisioning

# Install FastAPI app dependencies
cd app
uv pip install -e ".[dev]"

# Install Pulumi infrastructure dependencies
cd ../infrastructure
uv pip install -e ".[dev]"

# Or install both from root (if using workspace)
cd ..
uv pip install -e "./app[dev]"
uv pip install -e "./infrastructure[dev]"

# Configure AWS (if not done)
aws configure --profile pulumi-dev

# Login to Pulumi
pulumi login
```

### 3. Configure Pulumi Stacks

#### Test Stack

**Option 1: Edit config file directly (Recommended)**
```bash
cd infrastructure
pulumi stack init test

# Edit Pulumi.test.yaml and add your config values
# Then set the secret password:
pulumi config set --secret dbPassword <your-db-password>
```

**Option 2: Use config commands**
```bash
cd infrastructure
pulumi stack init test
pulumi config set aws:region us-east-1
pulumi config set s3BucketName pulumi-provisioning-test-bucket
pulumi config set dbName pulumi_test_db
pulumi config set --secret dbPassword <your-db-password>
```

**Note:** You can edit `Pulumi.test.yaml` directly - Pulumi reads from this file automatically!

#### Production Stack

**Option 1: Edit config file directly (Recommended)**
```bash
cd infrastructure
pulumi stack init prod

# Edit Pulumi.prod.yaml and add your config values
# Then set the secret password:
pulumi config set --secret dbPassword <your-db-password>
```

**Option 2: Use config commands**
```bash
cd infrastructure
pulumi stack init prod
pulumi config set aws:region us-east-1
pulumi config set s3BucketName pulumi-provisioning-prod-bucket
pulumi config set dbName pulumi_prod_db
pulumi config set --secret dbPassword <your-db-password>
pulumi config set domainName yourdomain.com  # Optional
```

**Note:** You can edit `Pulumi.prod.yaml` directly - Pulumi reads from this file automatically!

### 4. Verify Before Deploying (Recommended)

**Always preview changes before deploying!** This is like a "dry-run" that shows what will be created without actually creating it.

```bash
# Quick verification script (checks setup + runs preview)
./verify-pulumi.sh

# Or manually:
cd infrastructure

# Select stack
pulumi stack select test

# Preview changes (shows what will be created/updated/deleted)
pulumi preview

# Preview with detailed diff
pulumi preview --diff

# Preview in JSON format (for automation)
pulumi preview --json
```

**What Preview Shows:**
- ✅ Resources that will be **created** (green `+`)
- 🔄 Resources that will be **updated** (yellow `~`)
- ❌ Resources that will be **deleted** (red `-`)
- No changes if everything matches current state

### 5. Deploy Infrastructure

```bash
cd infrastructure

# Select stack
pulumi stack select test

# Deploy (after reviewing preview)
pulumi up

# Or deploy without confirmation (for automation)
pulumi up --yes
```

### 5. Set Up GitHub Actions

1. **Create Pulumi Access Token**
   - Go to https://app.pulumi.com/account/tokens
   - Create token and copy it

2. **Add GitHub Secrets**
   - Go to GitHub repo → Settings → Secrets and variables → Actions
   - Add secrets:
     - `PULUMI_ACCESS_TOKEN`: Your Pulumi access token
     - `AWS_ROLE_ARN`: IAM role ARN for GitHub Actions (after OIDC setup)
     - `DB_PASSWORD`: Database password (for test/prod environments)
     - `DOMAIN_NAME`: (Optional) Your domain name for production

3. **Set Up AWS OIDC** (for GitHub Actions)
   - Create OIDC identity provider in AWS IAM
   - Create IAM role with trust policy for GitHub
   - Add role ARN to GitHub secrets

See [OIDC_SETUP.md](OIDC_SETUP.md) for complete step-by-step OIDC setup guide.

## Package Management with uv

This project uses separate `pyproject.toml` files for FastAPI app and Pulumi infrastructure:

### FastAPI Application

```bash
cd app

# Install all dependencies (including dev)
uv pip install -e ".[dev]"

# Install only runtime dependencies
uv pip install -e .

# Add a new dependency
uv add <package-name>

# Update dependencies
uv pip install --upgrade -e ".[dev]"
```

### Pulumi Infrastructure

```bash
cd infrastructure

# Install all dependencies (including dev)
uv pip install -e ".[dev]"

# Install only runtime dependencies
uv pip install -e .

# Add a new dependency
uv add <package-name>
```

## FastAPI Endpoints

- `GET /health` - Health check
- `GET /s3/list` - List S3 objects
- `POST /s3/upload` - Upload file to S3
- `GET /s3/download/{key}` - Download file from S3
- `DELETE /s3/delete/{key}` - Delete file from S3
- `GET /db/status` - Check database connection
- `POST /db/create` - Create database record
- `GET /db/read` - Read database records
- `GET /db/read/{id}` - Read single record

## CI/CD Workflows

### Test Environment
- **Trigger**: Push to `develop` or `test` branch
- **Actions**: Preview on PR, deploy on push
- **Stack**: `test`

### Production Environment
- **Trigger**: Push to `main`/`master` or manual dispatch
- **Actions**: Requires manual approval, deploys to production
- **Stack**: `prod`

### Destroy Workflow
- **Trigger**: Manual dispatch only
- **Actions**: Destroys infrastructure with confirmation

## Component-Based Infrastructure

All infrastructure is built using reusable Pulumi components:

- **NetworkingComponent**: VPC, subnets, gateways, security groups
- **S3BucketComponent**: Configurable S3 buckets
- **RDSComponent**: PostgreSQL databases
- **EC2Component**: Compute instances
- **IAMComponent**: IAM roles and policies
- **Route53Component**: DNS management
- **ACMComponent**: SSL certificates

Each component is configurable and reusable across environments.

## Local Development

### FastAPI Application

```bash
cd app
uv pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Pulumi Infrastructure

```bash
cd infrastructure
uv pip install -e ".[dev]"
pulumi preview
```

### Docker Development

```bash
# Run FastAPI with Docker Compose
docker-compose up
```

## Development Tools

The project includes development tools configured in `pyproject.toml`:

- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking
- **ruff**: Fast linting and formatting
- **pytest**: Testing

```bash
# Format code
black .

# Lint code
flake8 .
ruff check .

# Type check
mypy .

# Run tests
pytest
```

## Security

- OIDC authentication for GitHub Actions (no long-lived keys)
- IAM roles with least privilege
- Secrets managed via Pulumi secrets
- RDS in private subnets
- Security groups with restrictive rules
- SSL/TLS via ACM or Let's Encrypt

## Documentation

- [OIDC_SETUP.md](OIDC_SETUP.md) - AWS OIDC setup for GitHub Actions
- [SECURITY.md](SECURITY.md) - Security best practices
- [app/README.md](app/README.md) - FastAPI application documentation

## License

MIT
