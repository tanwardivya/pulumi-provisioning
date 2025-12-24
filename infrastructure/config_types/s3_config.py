"""S3 bucket configuration types."""
from dataclasses import dataclass
from typing import Optional, List, Dict


@dataclass
class S3BucketConfig:
    """Configuration for S3 bucket component."""
    name: str
    versioning_enabled: bool = True
    encryption_enabled: bool = True
    public_access_block: bool = True
    lifecycle_rules: Optional[List[Dict]] = None
    cors_rules: Optional[List[Dict]] = None
    tags: Optional[dict] = None

