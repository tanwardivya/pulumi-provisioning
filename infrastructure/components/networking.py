"""Networking component - VPC, subnets, gateways, security groups."""
import pulumi
import pulumi_aws as aws
from infrastructure.components.base import BaseComponent
from infrastructure.config_types.networking_config import NetworkingConfig


class NetworkingComponent(BaseComponent):
    """Reusable networking component with VPC, subnets, and security groups."""
    
    def __init__(self, name: str, config: NetworkingConfig, opts=None):
        super().__init__(name, "custom:components:Networking", opts)
        
        # Get availability zones
        if config.availability_zones:
            azs = config.availability_zones
        else:
            azs_data = aws.get_availability_zones(state="available")
            azs = azs_data.names[:2]  # Use first 2 AZs
        
        # Create VPC
        self.vpc = aws.ec2.Vpc(
            f"{name}-vpc",
            cidr_block=config.vpc_cidr,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags={**(config.tags or {}), "Name": f"{name}-vpc"},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Create Internet Gateway
        self.internet_gateway = aws.ec2.InternetGateway(
            f"{name}-igw",
            vpc_id=self.vpc.id,
            tags={**(config.tags or {}), "Name": f"{name}-igw"},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Create public subnets
        self.public_subnets = []
        self.public_subnet_ids = []
        
        for i, az in enumerate(azs):
            subnet = aws.ec2.Subnet(
                f"{name}-public-subnet-{i+1}",
                vpc_id=self.vpc.id,
                cidr_block=f"10.0.{i+1}.0/24",
                availability_zone=az,
                map_public_ip_on_launch=True,
                tags={**(config.tags or {}), "Name": f"{name}-public-subnet-{i+1}"},
                opts=pulumi.ResourceOptions(parent=self)
            )
            self.public_subnets.append(subnet)
            self.public_subnet_ids.append(subnet.id)
        
        # Create private subnets
        self.private_subnets = []
        self.private_subnet_ids = []
        
        for i, az in enumerate(azs):
            subnet = aws.ec2.Subnet(
                f"{name}-private-subnet-{i+1}",
                vpc_id=self.vpc.id,
                cidr_block=f"10.0.{i+10}.0/24",
                availability_zone=az,
                tags={**(config.tags or {}), "Name": f"{name}-private-subnet-{i+1}"},
                opts=pulumi.ResourceOptions(parent=self)
            )
            self.private_subnets.append(subnet)
            self.private_subnet_ids.append(subnet.id)
        
        # Create NAT Gateway (if enabled)
        self.nat_gateway = None
        if config.enable_nat_gateway:
            # Allocate Elastic IP for NAT
            nat_eip = aws.ec2.Eip(
                f"{name}-nat-eip",
                domain="vpc",
                tags={**(config.tags or {}), "Name": f"{name}-nat-eip"},
                opts=pulumi.ResourceOptions(parent=self)
            )
            
            self.nat_gateway = aws.ec2.NatGateway(
                f"{name}-nat",
                allocation_id=nat_eip.id,
                subnet_id=self.public_subnets[0].id,
                tags={**(config.tags or {}), "Name": f"{name}-nat"},
                opts=pulumi.ResourceOptions(parent=self, depends_on=[self.internet_gateway])
            )
        
        # Create route tables
        # Public route table
        self.public_route_table = aws.ec2.RouteTable(
            f"{name}-public-rt",
            vpc_id=self.vpc.id,
            routes=[aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                gateway_id=self.internet_gateway.id,
            )],
            tags={**(config.tags or {}), "Name": f"{name}-public-rt"},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Associate public subnets with public route table
        for i, subnet in enumerate(self.public_subnets):
            aws.ec2.RouteTableAssociation(
                f"{name}-public-rta-{i+1}",
                subnet_id=subnet.id,
                route_table_id=self.public_route_table.id,
                opts=pulumi.ResourceOptions(parent=self)
            )
        
        # Private route table (with NAT if enabled)
        if config.enable_nat_gateway and self.nat_gateway:
            self.private_route_table = aws.ec2.RouteTable(
                f"{name}-private-rt",
                vpc_id=self.vpc.id,
                routes=[aws.ec2.RouteTableRouteArgs(
                    cidr_block="0.0.0.0/0",
                    nat_gateway_id=self.nat_gateway.id,
                )],
                tags={**(config.tags or {}), "Name": f"{name}-private-rt"},
                opts=pulumi.ResourceOptions(parent=self)
            )
            
            # Associate private subnets with private route table
            for i, subnet in enumerate(self.private_subnets):
                aws.ec2.RouteTableAssociation(
                    f"{name}-private-rta-{i+1}",
                    subnet_id=subnet.id,
                    route_table_id=self.private_route_table.id,
                    opts=pulumi.ResourceOptions(parent=self)
                )
        
        # Create security groups
        # EC2 security group
        self.ec2_security_group = aws.ec2.SecurityGroup(
            f"{name}-ec2-sg",
            vpc_id=self.vpc.id,
            description="Security group for EC2 instances",
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=22,
                    to_port=22,
                    cidr_blocks=["0.0.0.0/0"],
                    description="SSH"
                ),
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=80,
                    to_port=80,
                    cidr_blocks=["0.0.0.0/0"],
                    description="HTTP"
                ),
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=443,
                    to_port=443,
                    cidr_blocks=["0.0.0.0/0"],
                    description="HTTPS"
                ),
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=8000,
                    to_port=8000,
                    cidr_blocks=["0.0.0.0/0"],
                    description="FastAPI direct access"
                ),
            ],
            egress=[aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"],
            )],
            tags={**(config.tags or {}), "Name": f"{name}-ec2-sg"},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # RDS security group
        self.rds_security_group = aws.ec2.SecurityGroup(
            f"{name}-rds-sg",
            vpc_id=self.vpc.id,
            description="Security group for RDS instances",
            ingress=[
                aws.ec2.SecurityGroupIngressArgs(
                    protocol="tcp",
                    from_port=5432,
                    to_port=5432,
                    security_groups=[self.ec2_security_group.id],
                    description="PostgreSQL from EC2"
                ),
            ],
            egress=[aws.ec2.SecurityGroupEgressArgs(
                protocol="-1",
                from_port=0,
                to_port=0,
                cidr_blocks=["0.0.0.0/0"],
            )],
            tags={**(config.tags or {}), "Name": f"{name}-rds-sg"},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Register outputs
        self.register_outputs({
            "vpc_id": self.vpc.id,
            "public_subnet_ids": self.public_subnet_ids,
            "private_subnet_ids": self.private_subnet_ids,
            "ec2_security_group_id": self.ec2_security_group.id,
            "rds_security_group_id": self.rds_security_group.id,
        })
    
    @property
    def vpc_id(self):
        return self.vpc.id

