Verification Code : WTC-NF3XK4KU

# Khula-Sizwe Cloud Storage

A standalone AWS S3 data lake project, built to demonstrate practical cloud
skills for the WeThinkCode Cloud Computing elective (AWS Educate: Intro to
the AWS Management Console, Intro to Cloud 101).

## Relationship to Khula-Sizwe

This project is **separate and standalone** - it has no code dependency on
Khula-Sizwe at all. The relationship runs one way: Khula-Sizwe's local
pipeline output (CHIRPS rainfall data, NASA POWER climate data, the
processed feature table) can be pushed to S3 using this project's sync
script, turning Khula-Sizwe's conceptual "data lake" (currently just a local
folder) into a real cloud data lake.

Kept separate deliberately: a focused, reusable storage project is a
stronger demonstration of cloud skills on its own than cloud code buried
inside one specific pipeline. This project would work the same way for any
other local-folder-of-data project, not just Khula-Sizwe.

## What this demonstrates

- **AWS Management Console**: creating and configuring an S3 bucket
- **Cloud storage fundamentals**: uploading, downloading, listing, and
  deleting objects programmatically via `boto3`
- **Defensive engineering**: credential-error handling, pagination beyond
  S3's 1000-key response cap, idempotent re-runs (skip already-uploaded
  files rather than re-uploading everything every time)

## Setup

### 1. Create the S3 bucket (AWS Management Console)

1. Log into the AWS Educate console.
2. Go to S3 -> Create bucket.
3. Bucket names are **globally unique across all of AWS** - `khula-sizwe-data-lake`
   is almost certainly already taken by someone else. Use something like
   `khula-sizwe-data-lake-unathi-<a few random digits>`.
4. Region: pick `us-east-1` unless you've confirmed `af-south-1` (Cape Town)
   is enabled on your Educate account - some student accounts restrict which
   regions are available.
5. Leave "Block all public access" **checked** (the default) - this data has
   no reason to be publicly readable.
6. Create the bucket, then put its exact name in `config/storage.yml`.

### 2. Set up credentials

This project never hardcodes AWS credentials in code, since committing
credentials to a repo is one of the most common ways student AWS accounts
get compromised and run up unexpected charges.

Configure the AWS CLI once, locally:
```bash
aws configure
```
It will ask for an Access Key ID and Secret Access Key - get these from
your AWS Educate account (IAM -> Users -> Security credentials, or the
Educate-provided starter credentials if your account uses those instead of
full IAM). Once configured, boto3 picks these up automatically - nothing
else to do.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the tests (no AWS account needed for this part)

```bash
pytest tests/ -q
```

All 13 tests run against a fully mocked S3 (via the `moto` library) - no
real AWS account, credentials, or cost required. This is how the code was
verified correct before you ever touch a real bucket.

### 5. Sync real data to S3

Once the bucket exists and your bucket name is in `config/storage.yml`:

```bash
python -m src.storage.sync --local-dir ../Khula-Sizwe/data/raw --prefix raw
python -m src.storage.sync --local-dir ../Khula-Sizwe/data/processed --prefix processed
```

Adjust `--local-dir` to wherever your Khula-Sizwe checkout actually lives.
Re-running the same command later only uploads files that changed or are
new - already-uploaded files are skipped automatically.

## Project structure
