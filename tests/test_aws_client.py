"""Unit tests for AWSClient and data models."""

import json
import requests
from aws_service_profiles.aws_client import AWSClient
from aws_service_profiles.models import ActionAnnotations


def test_action_annotations_properties():
    """Verify ActionAnnotations access_level and plane properties."""
    read_data = ActionAnnotations(is_data_plane=True)
    assert read_data.access_level == "Read"
    assert read_data.plane == "Data Plane"

    write_ctrl = ActionAnnotations(is_write=True, is_data_plane=False)
    assert write_ctrl.access_level == "Write"
    assert write_ctrl.plane == "Control Plane"

    list_ctrl = ActionAnnotations(is_list=True)
    assert list_ctrl.access_level == "List"

    perm_ctrl = ActionAnnotations(is_permission_management=True)
    assert perm_ctrl.access_level == "Permissions management"

    tag_ctrl = ActionAnnotations(is_tagging_only=True)
    assert tag_ctrl.access_level == "Tagging"


def test_case_insensitive_service_lookup(mock_aws_client):
    """Verify service lookup works case-insensitively."""
    assert mock_aws_client.find_service("s3") is not None
    assert mock_aws_client.find_service("S3") is not None
    assert mock_aws_client.find_service("nonexistent") is None

    entry = mock_aws_client.find_service_entry("S3")
    assert entry is not None
    assert entry["service"] == "s3"
    assert entry["serviceName"] == "Amazon S3"


def test_get_all_actions_with_metadata_and_filters(mock_aws_client):
    """Verify action metadata extraction and filtering by access_level and plane."""
    all_actions = mock_aws_client.get_all_actions_with_metadata_for_service("s3")
    assert len(all_actions) == 7

    data_plane_actions = mock_aws_client.get_all_actions_with_metadata_for_service(
        "s3", plane="data"
    )
    assert [a["name"] for a in data_plane_actions] == [
        "GetObject",
        "PutObject",
        "AbortMultipartUpload",
    ]

    write_data_actions = mock_aws_client.get_all_actions_with_metadata_for_service(
        "s3", access_level="Write", plane="data"
    )
    assert [a["name"] for a in write_data_actions] == [
        "PutObject",
        "AbortMultipartUpload",
    ]

    perm_actions = mock_aws_client.get_all_actions_with_metadata_for_service(
        "s3", access_level="permissions"
    )
    assert [a["name"] for a in perm_actions] == ["PutBucketPolicy"]


def test_get_action_metadata_with_full_condition_keys_new_fields(mock_aws_client):
    """Verify action metadata includes access_level, plane, SupportedBy, and Operations."""
    details = mock_aws_client.get_action_metadata_with_full_condition_keys("s3", "getobject")
    assert details is not None
    assert details["name"] == "GetObject"
    assert details["access_level"] == "Read"
    assert details["plane"] == "Data Plane"
    assert details["annotations"]["IsDataPlane"] is True
    assert details["supported_by"]["IAM Access Analyzer Policy Generation"] is True
    assert details["supported_by"]["IAM Action Last Accessed"] is False
    assert len(details["operations"]) == 1
    assert details["operations"][0]["Name"] == "CopyObject"

    # EC2 RunInstances has action-scoped condition keys on 'instance' resource
    ec2_details = mock_aws_client.get_action_metadata_with_full_condition_keys(
        "ec2", "RunInstances"
    )
    assert ec2_details is not None
    instance_res = next(
        r for r in ec2_details["resources"] if r["name"] == "instance"
    )
    ck_names = [ck["Name"] for ck in instance_res["condition_keys"]]
    assert "ec2:PlacementGroupStrategy" in ck_names
    assert "ec2:InstanceType" in ck_names


def test_operations_lookup(mock_aws_client):
    """Verify service operations list and single operation details lookup."""
    ops = mock_aws_client.get_operations_for_service("s3")
    assert len(ops) == 3
    assert ops[0]["Name"] == "AbortMultipartUpload"

    op_detail = mock_aws_client.get_operation_details("s3", "abortmultipartupload")
    assert op_detail is not None
    assert op_detail["name"] == "AbortMultipartUpload"
    assert len(op_detail["sdk"]) == 2

    ec2_op = mock_aws_client.get_operation_details("ec2", "RunInstances")
    assert ec2_op is not None
    assert any("Context" in a for a in ec2_op["authorized_actions"])


def test_resource_details_with_full_condition_keys(mock_aws_client):
    """Verify resource lookup returns structured condition keys and ARN formats."""
    res = mock_aws_client.get_resource_details_with_full_condition_keys("s3", "BUCKET")
    assert res is not None
    assert res["name"] == "bucket"
    assert res["arn_formats"] == ["arn:${Partition}:s3:::${BucketName}"]
    assert any(ck["Name"] == "s3:ResourceAccount" for ck in res["context_keys"])


def test_cache_management_and_update_experience(tmp_path, monkeypatch):
    """Verify disk caching, update_metadata_cache diffing, and clear_cache."""
    cache_dir = tmp_path / "mim_cache"
    client = AWSClient(cache_dir=cache_dir, use_disk_cache=True)
    client._ensure_cache_dirs()

    old_index = [
        {
            "service": "s3",
            "serviceName": "Amazon S3",
            "url": "https://servicereference.us-east-1.amazonaws.com/v1/s3/s3.json",
            "modified": 1700000000,
        }
    ]
    client.index_cache_file.write_text(json.dumps(old_index), encoding="utf-8")
    client._service_cache_file("s3").write_text(
        json.dumps({"Name": "s3", "Actions": []}), encoding="utf-8"
    )

    new_index = [
        {
            "service": "s3",
            "serviceName": "Amazon S3",
            "url": "https://servicereference.us-east-1.amazonaws.com/v1/s3/s3.json",
            "modified": 1793502266,
        },
        {
            "service": "bedrock",
            "serviceName": "Amazon Bedrock",
            "url": "https://servicereference.us-east-1.amazonaws.com/v1/bedrock/bedrock.json",
            "modified": 1793488500,
        },
    ]

    class DummyResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self._payload

    def fake_requests_get(url, timeout=30):
        if url.endswith("s3.json"):
            return DummyResponse({"Name": "s3", "ServiceName": "Amazon S3", "Actions": []})
        return DummyResponse(new_index)

    monkeypatch.setattr(requests, "get", fake_requests_get)

    summary = client.update_metadata_cache()
    assert summary["total_services"] == 2
    assert summary["new_services"] == ["bedrock"]
    assert summary["modified_services"] == ["s3"]
    assert summary["refreshed_services"] == ["s3"]

    status = client.get_cache_status()
    assert status["index_cached"] is True
    assert status["cached_services_count"] == 1

    removed = client.clear_cache()
    assert removed >= 2
    assert client.get_cache_status()["index_cached"] is False
