"""S3 operations."""
import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from app.config import settings


def get_s3_client():
    """Get S3 client."""
    if not settings.s3_bucket_name:
        return None
    return boto3.client("s3", region_name=settings.aws_region)


def list_objects(prefix: Optional[str] = None) -> List[dict]:
    """List objects in S3 bucket."""
    s3_client = get_s3_client()
    if not s3_client:
        return []
    
    try:
        params = {"Bucket": settings.s3_bucket_name}
        if prefix:
            params["Prefix"] = prefix
        
        response = s3_client.list_objects_v2(**params)
        objects = []
        
        if "Contents" in response:
            for obj in response["Contents"]:
                objects.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                })
        
        return objects
    except ClientError as e:
        raise Exception(f"Error listing objects: {str(e)}")


def upload_file(file_content: bytes, key: str) -> dict:
    """Upload file to S3."""
    s3_client = get_s3_client()
    if not s3_client:
        raise Exception("S3 not configured")
    
    try:
        s3_client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
            Body=file_content
        )
        return {
            "key": key,
            "bucket": settings.s3_bucket_name,
            "status": "uploaded"
        }
    except ClientError as e:
        raise Exception(f"Error uploading file: {str(e)}")


def download_file(key: str) -> bytes:
    """Download file from S3."""
    s3_client = get_s3_client()
    if not s3_client:
        raise Exception("S3 not configured")
    
    try:
        response = s3_client.get_object(
            Bucket=settings.s3_bucket_name,
            Key=key
        )
        return response["Body"].read()
    except ClientError as e:
        raise Exception(f"Error downloading file: {str(e)}")


def delete_file(key: str) -> dict:
    """Delete file from S3."""
    s3_client = get_s3_client()
    if not s3_client:
        raise Exception("S3 not configured")
    
    try:
        s3_client.delete_object(
            Bucket=settings.s3_bucket_name,
            Key=key
        )
        return {
            "key": key,
            "status": "deleted"
        }
    except ClientError as e:
        raise Exception(f"Error deleting file: {str(e)}")

