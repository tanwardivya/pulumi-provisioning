"""Route53 component - DNS and domain management."""
import pulumi
import pulumi_aws as aws
from infrastructure.components.base import BaseComponent


class Route53Component(BaseComponent):
    """Reusable Route53 component for DNS management."""
    
    def __init__(self, name: str, domain_name: str, opts=None):
        super().__init__(name, "custom:components:Route53", opts)
        
        # Create hosted zone
        self.hosted_zone = aws.route53.Zone(
            f"{name}-zone",
            name=domain_name,
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Register outputs
        self.register_outputs({
            "zone_id": self.hosted_zone.zone_id,
            "name_servers": self.hosted_zone.name_servers,
        })
    
    def create_a_record(self, record_name: str, ip_address: str, ttl: int = 300):
        """Create an A record pointing to an IP address."""
        return aws.route53.Record(
            f"{self.name}-a-{record_name}",
            zone_id=self.hosted_zone.zone_id,
            name=record_name,
            type="A",
            ttl=ttl,
            records=[ip_address],
            opts=pulumi.ResourceOptions(parent=self)
        )
    
    @property
    def zone_id(self):
        return self.hosted_zone.zone_id

