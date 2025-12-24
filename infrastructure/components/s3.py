"""S3 bucket component."""
import pulumi
import pulumi_aws as aws
from infrastructure.components.base import BaseComponent
from infrastructure.types.s3_config import S3BucketConfig


class S3BucketComponent(BaseComponent):
    """Reusable S3 bucket component."""
    
    def __init__(self, name: str, config: S3BucketConfig, opts=None):
        super().__init__(name, "custom:components:S3Bucket", opts)
        
        # Create S3 bucket
        self.bucket = aws.s3.Bucket(
            f"{name}-bucket",
            bucket=config.name,
            versioning=aws.s3.BucketVersioningArgs(
                enabled=config.versioning_enabled
            ) if config.versioning_enabled else None,
            server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
                rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
                    apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                        sse_algorithm="AES256"
                    )
                )
            ) if config.encryption_enabled else None,
            public_access_block_configuration=aws.s3.BucketPublicAccessBlockConfigurationArgs(
                block_public_acls=config.public_access_block,
                block_public_policy=config.public_access_block,
                ignore_public_acls=config.public_access_block,
                restrict_public_buckets=config.public_access_block,
            ) if config.public_access_block else None,
            lifecycle_rules=config.lifecycle_rules,
            cors_rules=config.cors_rules,
            tags=config.tags or {},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
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

