import boto3
import os
from botocore.client import Config

def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
        config=Config(signature_version="s3v4"),
        region_name="auto"
    )

def generate_download_url(key, expires=60):
    client = get_r2_client()
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": os.getenv("R2_BUCKET"),
            "Key": key
        },
        ExpiresIn=expires
    )