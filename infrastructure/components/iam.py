"""IAM component - roles and policies for EC2."""
import pulumi
import pulumi_aws as aws
from infrastructure.components.base import BaseComponent
from infrastructure.config_types.iam_config import IAMConfig


class IAMComponent(BaseComponent):
    """Reusable IAM component for EC2 instance roles."""
    
    def __init__(self, name: str, config: IAMConfig, s3_bucket_arns=None, rds_instance_arn=None, ecr_repository_arn=None, opts=None):
        super().__init__(name, "custom:components:IAM", opts)
        
        # Use provided parameters or fall back to config
        s3_arns = s3_bucket_arns or config.s3_bucket_arns
        rds_arn = rds_instance_arn or config.rds_instance_arn
        ecr_arn = ecr_repository_arn or config.ecr_repository_arn
        
        # Collect all ARN outputs to resolve them together
        # Note: RDS IAM authentication is skipped (requires special ARN format conversion)
        arn_outputs = []
        if s3_arns:
            arn_outputs.extend(s3_arns)
        # RDS ARN not included - RDS IAM auth requires special ARN format (rds-db:connect)
        # Connection will use username/password instead
        if ecr_arn:
            arn_outputs.append(ecr_arn)
        
        # Build policy document after ARNs are resolved
        def build_policy_document(*resolved_arns):
            import json
            policy_statements = []
            arn_index = 0
            
            # S3 access policy
            if s3_arns and len(s3_arns) > 0:
                s3_resources = []
                for _ in s3_arns:
                    if arn_index < len(resolved_arns):
                        bucket_arn = resolved_arns[arn_index]
                        # Validate ARN is not None/empty and is a string
                        if bucket_arn and isinstance(bucket_arn, str) and bucket_arn.strip():
                            s3_resources.append(bucket_arn.strip())
                            s3_resources.append(f"{bucket_arn.strip()}/*")
                        arn_index += 1
                
                if s3_resources:  # Only add statement if we have resources
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
            
            # ECR access policy (for pulling images)
            # ECR ARN should be at index = len(s3_arns) since we skipped RDS
            if ecr_arn:
                ecr_index = len(s3_arns) if s3_arns else 0
                if ecr_index < len(resolved_arns):
                    ecr_resource = resolved_arns[ecr_index]
                    # Validate ARN is not None/empty and is a string
                    if ecr_resource and isinstance(ecr_resource, str) and ecr_resource.strip():
                        policy_statements.append({
                            "Effect": "Allow",
                            "Action": [
                                "ecr:GetAuthorizationToken",
                            ],
                            "Resource": ["*"],
                        })
                        policy_statements.append({
                            "Effect": "Allow",
                            "Action": [
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:GetDownloadUrlForLayer",
                                "ecr:BatchGetImage",
                                "ecr:DescribeRepositories",
                                "ecr:DescribeImages",
                                "ecr:ListImages",
                            ],
                            "Resource": [ecr_resource.strip()],
                        })
            
            # SSM Parameter Store access (for DB password and other secrets)
            policy_statements.append({
                "Effect": "Allow",
                "Action": [
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:DescribeParameters",
                ],
                "Resource": [
                    "arn:aws:ssm:*:*:parameter/pulumi/*"
                ],
            })
            
            # Build policy document - must have at least one statement
            # AWS IAM policies require at least one statement
            if not policy_statements:
                # This should not happen if ARNs are provided
                # Return a minimal valid policy as fallback
                policy_doc = {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": ["s3:ListBucket"],
                        "Resource": ["*"]
                    }]
                }
            else:
                policy_doc = {
                    "Version": "2012-10-17",
                    "Statement": policy_statements
                }
            
            # Validate JSON before returning
            try:
                policy_json = json.dumps(policy_doc)
                # Validate it can be parsed back
                parsed = json.loads(policy_json)
                # Ensure Statement is a list and not empty
                if not isinstance(parsed.get("Statement"), list) or len(parsed.get("Statement", [])) == 0:
                    raise ValueError("Policy Statement must be a non-empty list")
                return policy_json
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                # If JSON is invalid, return a minimal valid policy as fallback
                fallback_policy = {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Action": ["s3:ListBucket"],
                        "Resource": ["*"]
                    }]
                }
                return json.dumps(fallback_policy)
        
        # Resolve all ARNs and build policy
        if arn_outputs:
            policy_json = pulumi.Output.all(*arn_outputs).apply(build_policy_document)
        else:
            # No policy statements needed
            policy_json = None
        
        # Create IAM role with assume role policy
        import json
        assume_role_policy_json = json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }]
        })
        
        self.role = aws.iam.Role(
            f"{name}-role",
            assume_role_policy=assume_role_policy_json,
            tags=config.tags or {},
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Attach inline policy if we have statements
        # Only create policy if we have valid JSON (not None)
        if policy_json:
            # policy_json is a Pulumi Output, so we need to apply
            # We'll create the policy resource directly - if policy_json is None, 
            # the policy will be empty but valid, which AWS will reject
            # So we ensure build_policy_document never returns None when we have ARNs
            self.policy = aws.iam.RolePolicy(
                f"{name}-policy",
                role=self.role.id,
                policy=policy_json,
                opts=pulumi.ResourceOptions(parent=self)
            )
        else:
            self.policy = None
        
        # Attach ECR read-only managed policy (for pulling Docker images)
        if ecr_arn:
            aws.iam.RolePolicyAttachment(
                f"{name}-ecr-policy",
                role=self.role.id,
                policy_arn="arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
                opts=pulumi.ResourceOptions(parent=self)
            )
        
        # Attach SSM managed instance core policy (required for SSM agent to register)
        aws.iam.RolePolicyAttachment(
            f"{name}-ssm-policy",
            role=self.role.id,
            policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
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

