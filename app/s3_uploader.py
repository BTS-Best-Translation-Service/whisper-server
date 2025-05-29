import boto3
from botocore.exceptions import NoCredentialsError
from app.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_S3_BUCKET_NAME,
    AWS_S3_REGION,
)

#파일을 S3에 업로드하고 공개 URL을 반환
def upload_to_s3(file_path: str, s3_key: str) -> str:
    s3 = boto3.client(
        "s3",
        region_name=AWS_S3_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    try:
        s3.upload_file(file_path, AWS_S3_BUCKET_NAME, s3_key)
        s3_url = f"https://{AWS_S3_BUCKET_NAME}.s3.{AWS_S3_REGION}.amazonaws.com/{s3_key}"
        return s3_url
    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found.")
