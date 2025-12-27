"""EC2 configuration types."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class EC2Config:
    """Configuration for EC2 component."""
    instance_type: str = "t3.micro"
    ami_id: Optional[str] = None
    key_pair_name: Optional[str] = None
    associate_public_ip: bool = True
    enable_elastic_ip: bool = True
    tags: Optional[dict] = None

