from __future__ import annotations

import boto3
import pytest
from moto import mock_aws

from src.storage.s3_client import (
    bucket_exists,
    delete_object,
    download_file,
    list_objects,
    object_exists,
    upload_directory,
    upload_file,
)

REGION = "us-east-1"
BUCKET = "test-khula-sizwe-bucket"


@pytest.fixture
def s3_client():
    with mock_aws():
        client = boto3.client("s3", region_name=REGION)
        client.create_bucket(Bucket=BUCKET)
        yield client


def test_bucket_exists_true_for_real_bucket(s3_client):
    assert bucket_exists(BUCKET, s3_client) is True


def test_bucket_exists_false_for_missing_bucket(s3_client):
    assert bucket_exists("this-bucket-does-not-exist", s3_client) is False


def test_upload_file_then_object_exists(tmp_path, s3_client):
    local_file = tmp_path / "sample.txt"
    local_file.write_text("hello khula-sizwe")

    upload_file(local_file, BUCKET, "raw/sample.txt", s3_client)

    assert object_exists(BUCKET, "raw/sample.txt", s3_client) is True
    assert object_exists(BUCKET, "raw/does-not-exist.txt", s3_client) is False


def test_upload_file_raises_for_missing_local_file(s3_client):
    with pytest.raises(FileNotFoundError):
        upload_file("/nonexistent/path.txt", BUCKET, "raw/x.txt", s3_client)


def test_download_file_round_trip(tmp_path, s3_client):
    local_file = tmp_path / "upload_me.txt"
    local_file.write_text("round trip content")
    upload_file(local_file, BUCKET, "raw/round_trip.txt", s3_client)

    download_target = tmp_path / "downloaded" / "round_trip.txt"
    download_file(BUCKET, "raw/round_trip.txt", download_target, s3_client)

    assert download_target.read_text() == "round trip content"


def test_download_file_raises_clear_error_for_missing_key(tmp_path, s3_client):
    with pytest.raises(FileNotFoundError, match="No such object"):
        download_file(BUCKET, "raw/never-uploaded.txt", tmp_path / "out.txt", s3_client)


def test_list_objects_returns_all_matching_keys(tmp_path, s3_client):
    for i in range(3):
        f = tmp_path / f"file{i}.txt"
        f.write_text("x")
        upload_file(f, BUCKET, f"raw/file{i}.txt", s3_client)
    upload_file(tmp_path / "file0.txt", BUCKET, "processed/other.txt", s3_client)

    raw_keys = list_objects(BUCKET, "raw/", s3_client)
    assert sorted(raw_keys) == ["raw/file0.txt", "raw/file1.txt", "raw/file2.txt"]


def test_list_objects_paginates_beyond_default_page_size(s3_client):
    for i in range(1050):
        s3_client.put_object(Bucket=BUCKET, Key=f"raw/many/{i:04d}.txt", Body=b"x")

    keys = list_objects(BUCKET, "raw/many/", s3_client)
    assert len(keys) == 1050


def test_delete_object_removes_it(tmp_path, s3_client):
    f = tmp_path / "to_delete.txt"
    f.write_text("x")
    upload_file(f, BUCKET, "raw/to_delete.txt", s3_client)
    assert object_exists(BUCKET, "raw/to_delete.txt", s3_client) is True

    delete_object(BUCKET, "raw/to_delete.txt", s3_client)
    assert object_exists(BUCKET, "raw/to_delete.txt", s3_client) is False


def test_upload_directory_preserves_relative_structure(tmp_path, s3_client):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub" / "b.txt").write_text("b")

    stats = upload_directory(tmp_path, BUCKET, "raw", s3_client)

    assert stats == {"uploaded": 2, "skipped": 0}
    keys = sorted(list_objects(BUCKET, "raw/", s3_client))
    assert keys == ["raw/a.txt", "raw/sub/b.txt"]


def test_upload_directory_skips_already_uploaded_files(tmp_path, s3_client):
    (tmp_path / "a.txt").write_text("a")

    first = upload_directory(tmp_path, BUCKET, "raw", s3_client)
    second = upload_directory(tmp_path, BUCKET, "raw", s3_client)

    assert first == {"uploaded": 1, "skipped": 0}
    assert second == {"uploaded": 0, "skipped": 1}


def test_upload_directory_no_skip_existing_reuploads(tmp_path, s3_client):
    (tmp_path / "a.txt").write_text("a")

    upload_directory(tmp_path, BUCKET, "raw", s3_client)
    second = upload_directory(tmp_path, BUCKET, "raw", s3_client, skip_existing=False)

    assert second == {"uploaded": 1, "skipped": 0}


def test_upload_directory_raises_for_missing_local_dir(s3_client):
    with pytest.raises(FileNotFoundError):
        upload_directory("/nonexistent/dir", BUCKET, "raw", s3_client)
