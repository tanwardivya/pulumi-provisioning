"""IAM configuration types."""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class IAMConfig:
    """Configuration for IAM component."""
    role_name: str
    s3_bucket_arns: Optional[List[str]] = None
    rds_instance_arn: Optional[str] = None
    ecr_repository_arn: Optional[str] = None
    additional_policies: Optional[List[str]] = None
    tags: Optional[dict] = None

