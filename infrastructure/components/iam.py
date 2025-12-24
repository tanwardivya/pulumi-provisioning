"""IAM component - roles and policies for EC2."""
import pulumi
import pulumi_aws as aws
from infrastructure.components.base import BaseComponent
from infrastructure.types.iam_config import IAMConfig


class IAMComponent(BaseComponent):
    """Reusable IAM component for EC2 instance roles."""
    
    def __init__(self, name: str, config: IAMConfig, s3_bucket_arns=None, rds_instance_arn=None, ecr_repository_arn=None, opts=None):
        super().__init__(name, "custom:components:IAM", opts)
        
        # Use provided parameters or fall back to config
        s3_arns = s3_bucket_arns or config.s3_bucket_arns
        rds_arn = rds_instance_arn or config.rds_instance_arn
        ecr_arn = ecr_repository_arn or config.ecr_repository_arn
        
        # Build policy document for EC2 role
        policy_statements = []
        
        # S3 access policy
        if s3_arns:
            s3_resources = []
            for bucket_arn in s3_arns:
                s3_resources.append(bucket_arn)
                s3_resources.append(f"{bucket_arn}/*")
            
            policy_statements.append({
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket",
                ],
                "Resource": s3_resources,
            })
        
        # RDS access policy (for connection, not direct RDS management)
        if rds_arn:
            policy_statements.append({
                "Effect": "Allow",
                "Action": [
                    "rds-db:connect",
                ],
                "Resource": rds_arn,
            })
        
        # ECR access policy (for pulling images)
        if ecr_arn:
            policy_statements.append({
                "Effect": "Allow",
                "Action": [
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                "Resource": "*",
            })
            policy_statements.append({
                "Effect": "Allow",
                "Action": [
                    "ecr:DescribeRepositories",
                    "ecr:DescribeImages",
                ],
                "Resource": ecr_arn,
            })
        
        # Create IAM role
        assume_role_policy = aws.iam.get_policy_document(
            statements=[aws.iam.GetPolicyDocumentStatementArgs(
                effect="Allow",
                principals=[aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                    type="Service",
                    identifiers=["ec2.amazonaws.com"],
                )],
                actions=["sts:AssumeRole"],
            )]
        )
        
        self.role = aws.iam.Role(
            f"{name}-role",
            assume_role_policy=assume_role_policy.json,
            tags=config.tags or {},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Attach inline policy if we have statements
        if policy_statements:
            policy_doc = aws.iam.get_policy_document(statements=policy_statements)
            
            self.policy = aws.iam.RolePolicy(
                f"{name}-policy",
                role=self.role.id,
                policy=policy_doc.json,
                opts=pulumi.ResourceOptions(parent=self)
            )
        
        # Attach additional managed policies if provided
        if config.additional_policies:
            for i, policy_arn in enumerate(config.additional_policies):
                aws.iam.RolePolicyAttachment(
                    f"{name}-policy-attach-{i}",
                    role=self.role.id,
                    policy_arn=policy_arn,
                    opts=pulumi.ResourceOptions(parent=self)
                )
        
        # Create instance profile
        self.instance_profile = aws.iam.InstanceProfile(
            f"{name}-instance-profile",
            role=self.role.name,
            tags=config.tags or {},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Register outputs
        self.register_outputs({
            "role_arn": self.role.arn,
            "role_name": self.role.name,
            "instance_profile_arn": self.instance_profile.arn,
            "instance_profile_name": self.instance_profile.name,
        })
    
    @property
    def role_arn(self):
        return self.role.arn
    
    @property
    def instance_profile_name(self):
        return self.instance_profile.name

