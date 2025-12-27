"""S3 bucket component."""
import pulumi
import pulumi_aws as aws
from infrastructure.components.base import BaseComponent
from infrastructure.config_types.s3_config import S3BucketConfig


class S3BucketComponent(BaseComponent):
    """Reusable S3 bucket component."""
    
    def __init__(self, name: str, config: S3BucketConfig, opts=None):
        super().__init__(name, "custom:components:S3Bucket", opts)
        
        # Create S3 bucket (without deprecated versioning/encryption args)
        self.bucket = aws.s3.Bucket(
            f"{name}-bucket",
            bucket=config.name,
            lifecycle_rules=config.lifecycle_rules,
            cors_rules=config.cors_rules,
            tags=config.tags or {},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Create versioning as separate resource (if enabled)
        if config.versioning_enabled:
            self.versioning = aws.s3.BucketVersioning(
                f"{name}-versioning",
                bucket=self.bucket.id,
                versioning_configuration=aws.s3.BucketVersioningVersioningConfigurationArgs(
                    status="Enabled"
                ),
                opts=pulumi.ResourceOptions(parent=self, depends_on=[self.bucket])
            )
        else:
            self.versioning = None
        
        # Create server-side encryption as separate resource (if enabled)
        if config.encryption_enabled:
            self.encryption = aws.s3.BucketServerSideEncryptionConfiguration(
                f"{name}-encryption",
                bucket=self.bucket.id,
                rules=[aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
                    apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                        sse_algorithm="AES256"
                    )
                )],
                opts=pulumi.ResourceOptions(parent=self, depends_on=[self.bucket])
            )
        else:
            self.encryption = None
        
        # Create public access block as separate resource (if enabled)
        if config.public_access_block:
            self.public_access_block = aws.s3.BucketPublicAccessBlock(
                f"{name}-public-access-block",
                bucket=self.bucket.id,
                block_public_acls=True,
                block_public_policy=True,
                ignore_public_acls=True,
                restrict_public_buckets=True,
                opts=pulumi.ResourceOptions(parent=self, depends_on=[self.bucket])
            )
        else:
            self.public_access_block = None
        
        # Register outputs
        self.register_outputs({
            "bucket_name": self.bucket.id,
            "bucket_arn": self.bucket.arn,
            "bucket_domain_name": self.bucket.bucket_domain_name,
        })
    
    @property
    def bucket_name(self):
        return self.bucket.id
    
    @property
    def bucket_arn(self):
        return self.bucket.arn

