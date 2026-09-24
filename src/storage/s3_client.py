"""A thin, well-tested wrapper around boto3's S3 client.

This exists as a separate project from Khula-Sizwe deliberately: it is the
cloud storage layer, usable by Khula-Sizwe or any other project, rather than
cloud code buried inside one specific pipeline. Khula-Sizwe's own ingestion
scripts can import this module to push their output to S3, but this project
has no dependency on Khula-Sizwe at all - the relationship runs one way.
"""

from __future__ import annotations

from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from src.storage.utils import get_logger

LOG = get_logger("storage.s3_client")


def get_client(region: str):
    """Create a boto3 S3 client for the given region.

    Credentials are picked up from the environment (AWS_ACCESS_KEY_ID /
    AWS_SECRET_ACCESS_KEY) or a configured AWS CLI profile - never hardcoded
    here, since committing credentials to a repo is a real, common way
    student AWS accounts get compromised and run up charges.
    """
    return boto3.client("s3", region_name=region)


def bucket_exists(bucket: str, client) -> bool:
    try:
        client.head_bucket(Bucket=bucket)
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code in {"404", "NoSuchBucket"}:
            return False
        raise


def object_exists(bucket: str, key: str, client) -> bool:
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code in {"404", "NoSuchKey"}:
            return False
        raise


def upload_file(local_path: str | Path, bucket: str, key: str, client) -> None:
    local_path = Path(local_path)
    if not local_path.exists():
        raise FileNotFoundError(f"Cannot upload, file does not exist: {local_path}")

    try:
        client.upload_file(str(local_path), bucket, key)
        LOG.info("Uploaded %s -> s3://%s/%s", local_path, bucket, key)
    except NoCredentialsError as exc:
        raise RuntimeError(
            "No AWS credentials found. Set AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY, or configure the AWS CLI (aws configure)."
        ) from exc


def download_file(bucket: str, key: str, local_path: str | Path, client) -> None:
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        client.download_file(bucket, key, str(local_path))
        LOG.info("Downloaded s3://%s/%s -> %s", bucket, key, local_path)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code in {"404", "NoSuchKey"}:
            raise FileNotFoundError(f"No such object: s3://{bucket}/{key}") from exc
        raise


def list_objects(bucket: str, prefix: str, client) -> list[str]:
    

    paginator = client.get_paginator("list_objects_v2")
    keys: list[str] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys
