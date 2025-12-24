"""RDS configuration types."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RDSConfig:
    """Configuration for RDS component."""
    db_name: str
    engine: str = "postgres"
    engine_version: Optional[str] = None
    instance_class: str = "db.t3.micro"
    allocated_storage: int = 20
    storage_type: str = "gp3"
    multi_az: bool = False
    backup_retention_period: int = 7
    skip_final_snapshot: bool = False
    tags: Optional[dict] = None

