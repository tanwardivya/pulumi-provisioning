"""EC2 component - compute instances."""
import pulumi
import pulumi_aws as aws
from infrastructure.components.base import BaseComponent
from infrastructure.types.ec2_config import EC2Config


class EC2Component(BaseComponent):
    """Reusable EC2 component."""
    
    def __init__(
        self,
        name: str,
        config: EC2Config,
        subnet_id=None,
        security_group_id=None,
        iam_instance_profile_name=None,
        user_data=None,
        opts=None
    ):
        super().__init__(name, "custom:components:EC2", opts)
        
        # Get latest Amazon Linux 2023 AMI if not provided
        if not config.ami_id:
            ami = aws.ec2.get_ami(
                most_recent=True,
                owners=["amazon"],
                filters=[aws.ec2.GetAmiFilterArgs(
                    name="name",
                    values=["al2023-ami-*-x86_64"],
                )]
            )
            ami_id = ami.id
        else:
            ami_id = config.ami_id
        
        # Allocate Elastic IP if enabled
        self.elastic_ip = None
        if config.enable_elastic_ip:
            self.elastic_ip = aws.ec2.Eip(
                f"{name}-eip",
                domain="vpc",
                tags={**(config.tags or {}), "Name": f"{name}-eip"},
                opts=pulumi.ResourceOptions(parent=self)
            )
        
        # Create EC2 instance
        self.instance = aws.ec2.Instance(
            f"{name}-instance",
            ami=ami_id,
            instance_type=config.instance_type,
            subnet_id=subnet_id,
            vpc_security_group_ids=[security_group_id] if security_group_id else [],
            iam_instance_profile=iam_instance_profile_name,
            key_name=config.key_pair_name,
            associate_public_ip_address=config.associate_public_ip,
            user_data=user_data,
            tags={**(config.tags or {}), "Name": f"{name}-instance"},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Associate Elastic IP if created
        if self.elastic_ip:
            aws.ec2.EipAssociation(
                f"{name}-eip-assoc",
                instance_id=self.instance.id,
                allocation_id=self.elastic_ip.id,
                opts=pulumi.ResourceOptions(parent=self)
            )
        
        # Register outputs
        outputs = {
            "instance_id": self.instance.id,
            "public_ip": self.instance.public_ip,
            "private_ip": self.instance.private_ip,
        }
        
        if self.elastic_ip:
            outputs["elastic_ip"] = self.elastic_ip.public_ip
        
        self.register_outputs(outputs)
    
    @property
    def instance_id(self):
        return self.instance.id
    
    @property
    def public_ip(self):
        return self.instance.public_ip or (self.elastic_ip.public_ip if self.elastic_ip else None)
    
    @property
    def private_ip(self):
        return self.instance.private_ip

