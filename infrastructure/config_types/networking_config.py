"""Networking configuration types."""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class NetworkingConfig:
    """Configuration for networking component."""
    vpc_cidr: str = "10.0.0.0/16"
    availability_zones: Optional[List[str]] = None
    enable_nat_gateway: bool = True
    tags: Optional[dict] = None

