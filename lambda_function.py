"""AWS Lambda entrypoint for the daily insider-buying pipeline.

Lambda's filesystem is read-only except for /tmp, so LOG_DIR is pointed there.
Trading state is not persisted here — check_close_positions reconstructs position
entry dates from Alpaca's order history. The signal log is analytics-only; if
SIGNALS_S3_BUCKET is set it is round-tripped through S3 (download, append during
the run, upload) so history accumulates across invocations.

Required environment variables:
    ALPACA_API_KEY, ALPACA_SECRET_KEY   Alpaca paper-trading credentials
    EDGAR_IDENTITY                       "Name email@example.com" for the SEC
Optional:
    SIGNALS_S3_BUCKET                    bucket for the persisted signal log
    SIGNALS_S3_KEY                       object key (default: signals_log.jsonl)
"""

import logging
import os
from pathlib import Path

# Route pipeline file writes to the only writable location on Lambda.
os.environ.setdefault("LOG_DIR", "/tmp/logs")
LOG_DIR = Path(os.environ["LOG_DIR"])
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Lambda pre-installs a root handler, so basicConfig is a no-op here (and, once
# the pipeline is imported, its basicConfig(filename=...) is a no-op too — records
# go to CloudWatch). Just make sure INFO is not filtered out.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger().setLevel(logging.INFO)
log = logging.getLogger("lambda")

import boto3
from botocore.exceptions import ClientError

S3_BUCKET = os.environ.get("SIGNALS_S3_BUCKET")
S3_KEY = os.environ.get("SIGNALS_S3_KEY", "signals_log.jsonl")
SIGNALS_LOG = LOG_DIR / "signals_log.jsonl"
_s3 = boto3.client("s3")


def _download_signal_log():
    if not S3_BUCKET:
        return
    try:
        _s3.download_file(S3_BUCKET, S3_KEY, str(SIGNALS_LOG))
        log.info("Downloaded s3://%s/%s", S3_BUCKET, S3_KEY)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            log.info("No existing signal log in S3 — starting fresh")
        else:
            raise


def _upload_signal_log():
    if not S3_BUCKET or not SIGNALS_LOG.exists():
        return
    _s3.upload_file(str(SIGNALS_LOG), S3_BUCKET, S3_KEY)
    log.info("Uploaded s3://%s/%s", S3_BUCKET, S3_KEY)


def handler(event, context):
    identity = os.environ.get("EDGAR_IDENTITY")
    if identity:
        from edgar import set_identity
        set_identity(identity)
    else:
        log.warning("EDGAR_IDENTITY not set — SEC requests may be rejected")

    _download_signal_log()
    try:
        from pipeline.run_daily import run
        run()
    finally:
        _upload_signal_log()

    return {"status": "complete"}
