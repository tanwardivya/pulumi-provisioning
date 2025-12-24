"""Configuration management for Pulumi stacks."""
import pulumi
from infrastructure.types.networking_config import NetworkingConfig
from infrastructure.types.s3_config import S3BucketConfig
from infrastructure.types.rds_config import RDSConfig
from infrastructure.types.ec2_config import EC2Config
from infrastructure.types.iam_config import IAMConfig
from infrastructure.types.ecr_config import ECRConfig


def get_config():
    """Load and return configuration for current stack."""
    config = pulumi.Config()
    stack = pulumi.get_stack()
    
    # Get environment
    environment = config.get("environment") or stack
    
    # Base tags
    base_tags = {
        "Environment": environment,
        "ManagedBy": "Pulumi",
        "Project": config.get("projectName") or "pulumi-provisioning",
    }
    
    # Networking config
    networking_config = NetworkingConfig(
        vpc_cidr=config.get("vpcCidr") or "10.0.0.0/16",
        enable_nat_gateway=config.get_bool("enableNatGateway") if config.get("enableNatGateway") else True,
        tags=base_tags,
    )
    
    # S3 config
    s3_bucket_name = config.require("s3BucketName")
    s3_config = S3BucketConfig(
        name=s3_bucket_name,
        versioning_enabled=config.get_bool("s3Versioning") if config.get("s3Versioning") else True,
        encryption_enabled=config.get_bool("s3Encryption") if config.get("s3Encryption") else True,
        tags=base_tags,
    )
    
    # RDS config
    rds_config = RDSConfig(
        db_name=config.require("dbName"),
        engine=config.get("dbEngine") or "postgres",
        instance_class=config.get("dbInstanceClass") or "db.t3.micro",
        allocated_storage=config.get_int("dbAllocatedStorage") or 20,
        multi_az=config.get_bool("dbMultiAz") if config.get("dbMultiAz") else False,
        tags=base_tags,
    )
    
    # EC2 config
    ec2_config = EC2Config(
        instance_type=config.get("ec2InstanceType") or "t3.micro",
        associate_public_ip=config.get_bool("ec2AssociatePublicIp") if config.get("ec2AssociatePublicIp") else True,
        enable_elastic_ip=config.get_bool("ec2EnableElasticIp") if config.get("ec2EnableElasticIp") else True,
        tags=base_tags,
    )
    
    # IAM config
    iam_config = IAMConfig(
        role_name=f"pulumi-{environment}-ec2-role",
        tags=base_tags,
    )
    
    # ECR config
    ecr_repository_name = config.get("ecrRepositoryName") or f"pulumi-provisioning-{environment}"
    ecr_config = ECRConfig(
        repository_name=ecr_repository_name,
        image_scanning_enabled=config.get_bool("ecrImageScanning") if config.get("ecrImageScanning") else True,
        lifecycle_policy_enabled=config.get_bool("ecrLifecyclePolicy") if config.get("ecrLifecyclePolicy") else True,
        max_image_count=config.get_int("ecrMaxImageCount") or 10,
        tags=base_tags,
    )
    
    return {
        "environment": environment,
        "networking": networking_config,
        "s3": s3_config,
        "rds": rds_config,
        "ec2": ec2_config,
        "iam": iam_config,
        "ecr": ecr_config,
        "tags": base_tags,
    }

