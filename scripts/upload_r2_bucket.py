"""
Upload a local folder to a Cloudflare R2 bucket, preserving paths.

Usage:
    # Option A: rely on .env (default) — no exports needed
    python scripts/upload_r2_bucket.py --src ./r2-backup

    # Option B: point to a custom env file
    python scripts/upload_r2_bucket.py --src ./r2-backup --env-file .env.r2

    # Option C: explicit exports (will override .env)
    export CLOUDFLARE_R2_ENDPOINT_URL=...
    export CLOUDFLARE_R2_ACCESS_KEY_ID=...
    export CLOUDFLARE_R2_SECRET_ACCESS_KEY=...
    export CLOUDFLARE_R2_BUCKET=...
    python scripts/upload_r2_bucket.py --src ./r2-backup

Optional:
    --prefix assets/   # upload under a prefix inside the bucket

Dependencies: boto3 (pip install boto3)
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


REQUIRED_ENV_VARS = [
    "CLOUDFLARE_R2_ENDPOINT_URL",
    "CLOUDFLARE_R2_ACCESS_KEY_ID",
    "CLOUDFLARE_R2_SECRET_ACCESS_KEY",
    "CLOUDFLARE_R2_BUCKET",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Upload a local folder to a Cloudflare R2 bucket."
    )
    parser.add_argument(
        "--src",
        required=True,
        help="Local directory containing files to upload.",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Optional prefix to prepend to all uploaded keys (e.g. 'assets/').",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to a .env file with R2 settings (defaults to .env).",
    )
    return parser.parse_args()


def load_env_file(path: str) -> Dict[str, str]:
    """
    Minimal .env loader to avoid extra deps.
    Only lines like KEY=VALUE are parsed; comments/# and blank lines are ignored.
    Values can be quoted or unquoted.
    """
    env_path = Path(path)
    if not env_path.is_file():
        return {}

    parsed: Dict[str, str] = {}
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            parsed[key] = val
            os.environ.setdefault(key, val)
    return parsed


def get_env_config() -> dict:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        sys.exit(f"Missing required env vars: {', '.join(missing)}")

    return {
        "endpoint_url": os.environ["CLOUDFLARE_R2_ENDPOINT_URL"].strip(),
        "aws_access_key_id": os.environ["CLOUDFLARE_R2_ACCESS_KEY_ID"].strip(),
        "aws_secret_access_key": os.environ[
            "CLOUDFLARE_R2_SECRET_ACCESS_KEY"
        ].strip(),
        "bucket": os.environ["CLOUDFLARE_R2_BUCKET"].strip(),
    }


def make_s3_client(endpoint_url: str, access_key: str, secret_key: str):
    """
    Minimal boto3 client tailored for Cloudflare R2.
    """
    return boto3.client(
        "s3",
        region_name=os.environ.get("CLOUDFLARE_R2_REGION", "auto"),
        endpoint_url=endpoint_url.rstrip("/"),
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            signature_version="s3v4",
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
            s3={
                "addressing_style": "virtual",
                "payload_signing_enabled": False,
                "checksum_algorithm": None,
            },
        ),
    )
def iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def upload_all(s3_client, bucket: str, src_root: Path, prefix: str = ""):
    uploaded = 0
    total = 0
    src_root = src_root.resolve()
    for filepath in iter_files(src_root):
        total += 1
        rel_key = filepath.relative_to(src_root).as_posix()
        key = f"{prefix}{rel_key}" if prefix else rel_key
        try:
            with open(filepath, "rb") as fh:
                s3_client.put_object(Bucket=bucket, Key=key, Body=fh)
            uploaded += 1
            print(f"[ok] {filepath} -> s3://{bucket}/{key}")
        except (BotoCoreError, ClientError) as exc:
            print(f"[err] {filepath}: {exc}", file=sys.stderr)
    return uploaded, total


def main():
    args = parse_args()
    load_env_file(args.env_file)
    env = get_env_config()
    src_root = Path(args.src).resolve()
    if not src_root.is_dir():
        sys.exit(f"Source folder not found: {src_root}")

    print(
        f"Using endpoint={env['endpoint_url']} bucket={env['bucket']} region={os.environ.get('CLOUDFLARE_R2_REGION', 'auto')} signature=s3v4"
    )
    if "cloudflarestorage.com" not in env["endpoint_url"]:
        print(
            "Warning: endpoint does not look like an R2 S3 endpoint (expected *.r2.cloudflarestorage.com).",
            file=sys.stderr,
        )

    client = make_s3_client(
        endpoint_url=env["endpoint_url"],
        access_key=env["aws_access_key_id"],
        secret_key=env["aws_secret_access_key"],
    )

    uploaded, total = upload_all(
        client, bucket=env["bucket"], src_root=src_root, prefix=args.prefix
    )
    print(f"Finished: {uploaded}/{total} objects uploaded from {src_root}")


if __name__ == "__main__":
    main()
