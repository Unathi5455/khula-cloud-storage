"""Sync a local directory tree to S3.

Usage:
    python -m src.storage.sync --local-dir ../Khula-Sizwe/data/raw --prefix raw
    python -m src.storage.sync --local-dir ../Khula-Sizwe/data/processed --prefix processed
"""

from __future__ import annotations

import argparse

from src.storage.s3_client import bucket_exists, get_client, upload_directory
from src.storage.utils import get_logger, load_config

LOG = get_logger("storage.sync")


def main() -> None:
    config = load_config()
    aws_cfg = config["aws"]

    parser = argparse.ArgumentParser(description="Sync a local directory to S3.")
    parser.add_argument("--local-dir", required=True, help="Local directory to upload.")
    parser.add_argument("--prefix", required=True, help="S3 key prefix, e.g. 'raw' or 'processed'.")
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Re-upload every file even if it already exists in S3.",
    )
    args = parser.parse_args()

    client = get_client(aws_cfg["region"])
    bucket = aws_cfg["bucket_name"]

    if bucket.startswith("CHANGE-ME"):
        raise SystemExit(
            "config/storage.yml still has the placeholder bucket name. "
            "Create a bucket in the AWS console and put its exact name in "
            "config/storage.yml before running this."
        )

    if not bucket_exists(bucket, client):
        raise SystemExit(
            f"Bucket '{bucket}' not found or not accessible. Confirm it "
            "exists in the console, the region matches config/storage.yml, "
            "and your credentials have access to it."
        )

    LOG.info("Syncing %s -> s3://%s/%s", args.local_dir, bucket, args.prefix)
    stats = upload_directory(
        args.local_dir, bucket, args.prefix, client,
        skip_existing=not args.no_skip_existing,
    )
    LOG.info("Done. Uploaded %s file(s), skipped %s already-present file(s).",
              stats["uploaded"], stats["skipped"])


if __name__ == "__main__":
    main()
