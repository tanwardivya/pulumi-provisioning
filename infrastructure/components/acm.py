"""ACM component - SSL/TLS certificates."""
import pulumi
import pulumi_aws as aws
from infrastructure.components.base import BaseComponent


class ACMComponent(BaseComponent):
    """Reusable ACM component for SSL certificates."""
    
    def __init__(self, name: str, domain_name: str, zone_id=None, opts=None):
        super().__init__(name, "custom:components:ACM", opts)
        
        # Create certificate
        self.certificate = aws.acm.Certificate(
            f"{name}-cert",
            domain_name=domain_name,
            validation_method="DNS",
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # If zone_id provided, create validation records automatically
        if zone_id:
            # Get certificate validation options
            cert_validation = aws.acm.CertificateValidation(
                f"{name}-cert-validation",
                certificate_arn=self.certificate.arn,
                validation_record_fqdns=[record.fqdn for record in self.certificate.domain_validation_options],
                opts=pulumi.ResourceOptions(parent=self)
            )
            self.certificate_validation = cert_validation
        
        # Register outputs
        self.register_outputs({
            "certificate_arn": self.certificate.arn,
            "certificate_domain": self.certificate.domain_name,
        })
    
    @property
    def certificate_arn(self):
        return self.certificate.arn

