"""RDS component - PostgreSQL database."""
import pulumi
import pulumi_aws as aws
from infrastructure.components.base import BaseComponent
from infrastructure.config_types.rds_config import RDSConfig


class RDSComponent(BaseComponent):
    """Reusable RDS component."""
    
    def __init__(
        self,
        name: str,
        config: RDSConfig,
        subnet_ids=None,
        security_group_id=None,
        opts=None
    ):
        super().__init__(name, "custom:components:RDS", opts)
        
        # Create DB subnet group
        self.db_subnet_group = aws.rds.SubnetGroup(
            f"{name}-subnet-group",
            subnet_ids=subnet_ids or [],
            tags=config.tags or {},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Get database password from Pulumi secrets
        db_password = pulumi.Config().require_secret("dbPassword")
        
        # Create RDS instance
        self.db_instance = aws.rds.Instance(
            f"{name}-db",
            engine=config.engine,
            engine_version=config.engine_version,
            instance_class=config.instance_class,
            allocated_storage=config.allocated_storage,
            storage_type=config.storage_type,
            db_name=config.db_name,
            username="admin",  # Can be made configurable
            password=db_password,
            db_subnet_group_name=self.db_subnet_group.name,
            vpc_security_group_ids=[security_group_id] if security_group_id else [],
            multi_az=config.multi_az,
            backup_retention_period=config.backup_retention_period,
            skip_final_snapshot=config.skip_final_snapshot,
            final_snapshot_identifier=f"{name}-final-snapshot" if not config.skip_final_snapshot else None,
            tags=config.tags or {},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Register outputs
        self.register_outputs({
            "db_endpoint": self.db_instance.endpoint,
            "db_address": self.db_instance.address,
            "db_port": self.db_instance.port,
            "db_name": self.db_instance.db_name,
            "db_instance_id": self.db_instance.id,
        })
    
    @property
    def endpoint(self):
        return self.db_instance.endpoint
    
    @property
    def address(self):
        return self.db_instance.address
    
    @property
    def port(self):
        return self.db_instance.port

