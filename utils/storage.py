import boto3
import os
from botocore.client import Config

def get_r2_client():
 return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY"],
        aws_secret_access_key=os.environ["R2_SECRET_KEY"],
        region_name="auto",
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
def upload_file(local_path, key):

    client = get_r2_client()
    bucket = os.getenv("R2_BUCKET")

    client.upload_file(local_path, bucket, key)

    public_url = os.getenv("R2_PUBLIC_URL")

    return f"{public_url}/{key}"