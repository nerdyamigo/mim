"""CLI integration tests using Click CliRunner."""

import json
import yaml
import pytest
from click.testing import CliRunner
from aws_service_profiles import cli as cli_module


@pytest.fixture
def cli_runner(mock_aws_client, monkeypatch):
    """Configure Click CliRunner with AWSClient patched to mock_aws_client."""
    monkeypatch.setattr(cli_module, "AWSClient", lambda *a, **kw: mock_aws_client)
    return CliRunner()


def test_cli_list_services_and_search(cli_runner):
    """Test --list-services with --search filter and --count."""
    res = cli_runner.invoke(cli_module.cli, ["--list-services"])
    assert res.exit_code == 0
    assert "Amazon S3" in res.output
    assert "Amazon EC2" in res.output
    assert "Amazon Bedrock" in res.output

    res_search = cli_runner.invoke(cli_module.cli, ["--list-services", "--search", "bedrock"])
    assert res_search.exit_code == 0
    assert "bedrock" in res_search.output
    assert "ec2" not in res_search.output

    res_count = cli_runner.invoke(cli_module.cli, ["--list-services", "--count"])
    assert res_count.exit_code == 0
    assert "Total AWS services" in res_count.output
    assert "3" in res_count.output


def test_cli_service_info(cli_runner):
    """Test 'mim s3 info' shows new summary fields (Version, Access Levels, Operations, Planes)."""
    res = cli_runner.invoke(cli_module.cli, ["s3", "info"])
    assert res.exit_code == 0
    assert "Amazon S3" in res.output
    assert "v1.5" in res.output
    assert "API Operations: 3" in res.output
    assert "Control Plane: 4" in res.output
    assert "Data Plane: 3" in res.output
    assert "Read: 1, Write: 3" in res.output


def test_cli_actions_filtering(cli_runner):
    """Test listing actions with --access-level, --plane, and --search filters."""
    res = cli_runner.invoke(
        cli_module.cli, ["s3", "--access-level", "Write", "--plane", "data"]
    )
    assert res.exit_code == 0
    assert "AbortMultipartUpload" in res.output
    assert "PutObject" in res.output
    assert "GetObject" not in res.output
    assert "CreateBucket" not in res.output

    res_search = cli_runner.invoke(cli_module.cli, ["s3", "-s", "bucket"])
    assert res_search.exit_code == 0
    assert "CreateBucket" in res_search.output
    assert "PutBucketPolicy" in res_search.output
    assert "GetObject" not in res_search.output


def test_cli_action_details_and_shorthand(cli_runner):
    """Test 'mim s3 --action GetObject', 'mim s3:GetObject', and 'mim s3 \"Put*\"'."""
    res_flag = cli_runner.invoke(cli_module.cli, ["s3", "--action", "getobject"])
    assert res_flag.exit_code == 0
    assert "GetObject" in res_flag.output
    assert "Read" in res_flag.output
    assert "Data Plane" in res_flag.output

    res_shorthand = cli_runner.invoke(cli_module.cli, ["s3:GetObject", "--format", "json"])
    assert res_shorthand.exit_code == 0
    parsed = json.loads(res_shorthand.output)
    assert isinstance(parsed, list)
    assert parsed[0]["action"] == "GetObject"
    assert parsed[0]["access_level"] == "Read"

    res_wildcard = cli_runner.invoke(cli_module.cli, ["s3", "Put*", "--format", "json"])
    assert res_wildcard.exit_code == 0
    wildcard_data = json.loads(res_wildcard.output)
    assert wildcard_data["service"] == "s3"
    assert set(wildcard_data["actions"]) == {
        "PutBucketPolicy",
        "PutBucketTagging",
        "PutObject",
    }


def test_cli_operations_and_operation_detail(cli_runner):
    """Test --operations and --operation flags."""
    res_ops = cli_runner.invoke(cli_module.cli, ["s3", "--operations"])
    assert res_ops.exit_code == 0
    assert "AbortMultipartUpload" in res_ops.output
    assert "CopyObject" in res_ops.output

    res_ops_search = cli_runner.invoke(
        cli_module.cli, ["s3", "--operations", "--search", "copy", "--format", "json"]
    )
    assert res_ops_search.exit_code == 0
    ops_json = json.loads(res_ops_search.output)
    assert ops_json["count"] == 1
    assert ops_json["operations"][0]["Name"] == "CopyObject"

    res_op = cli_runner.invoke(cli_module.cli, ["s3", "--operation", "copyobject"])
    assert res_op.exit_code == 0
    assert "CopyObject" in res_op.output
    assert "s3:GetObject" in res_op.output
    assert "s3:PutObject" in res_op.output


def test_cli_resources_and_resource_detail(cli_runner):
    """Test --resources and --resource flags."""
    res_list = cli_runner.invoke(cli_module.cli, ["s3", "--resources"])
    assert res_list.exit_code == 0
    assert "bucket" in res_list.output
    assert "object" in res_list.output

    res_detail = cli_runner.invoke(cli_module.cli, ["s3", "--resource", "bucket"])
    assert res_detail.exit_code == 0
    assert "bucket" in res_detail.output
    assert "arn:${Partition}:s3:::${BucketName}" in res_detail.output
    assert "s3:ResourceAccount (String)" in res_detail.output


def test_cli_context_keys(cli_runner):
    """Test --context-keys, --global-context-keys, and --service-context-keys."""
    res_ck = cli_runner.invoke(cli_module.cli, ["s3", "--context-keys", "-s", "Tag"])
    assert res_ck.exit_code == 0
    assert "s3:ExistingObjectTag/<key>" in res_ck.output

    res_global = cli_runner.invoke(cli_module.cli, ["s3", "--global-context-keys"])
    assert res_global.exit_code == 0
    assert "aws:RequestTag/${TagKey}" in res_global.output
    assert "s3:x-amz-acl" not in res_global.output

    res_service = cli_runner.invoke(cli_module.cli, ["s3", "--service-context-keys"])
    assert res_service.exit_code == 0
    assert "s3:x-amz-acl" in res_service.output
    assert "aws:RequestTag/${TagKey}" not in res_service.output


def test_cli_service_actions_batch(cli_runner):
    """Test -sa / --service-actions batch querying."""
    res = cli_runner.invoke(
        cli_module.cli,
        ["-sa", "s3:GetObject,ec2:RunInstances", "--format", "yaml"],
    )
    assert res.exit_code == 0
    parsed = yaml.safe_load(res.output)
    assert isinstance(parsed, list)
    assert len(parsed) == 2
    by_service = {item["service"]: item for item in parsed}
    assert by_service["s3"]["action"] == "GetObject"
    assert by_service["ec2"]["action"] == "RunInstances"


def test_cli_update_and_clear_cache(cli_runner, mock_aws_client, monkeypatch):
    """Test 'mim --update', 'mim update', and 'mim --clear-cache'."""
    monkeypatch.setattr(
        mock_aws_client,
        "update_metadata_cache",
        lambda *a, **kw: {
            "last_updated": "2026-11-09T06:00:00+00:00",
            "total_services": 3,
            "new_services_count": 0,
            "new_services": [],
            "modified_services_count": 1,
            "modified_services": ["s3"],
            "refreshed_services": ["s3"],
        },
    )

    res_update = cli_runner.invoke(cli_module.cli, ["--update"])
    assert res_update.exit_code == 0
    assert "AWS Service Reference Metadata Update Summary" in res_update.output
    assert "s3" in res_update.output

    res_update_word = cli_runner.invoke(cli_module.cli, ["update", "--format", "json"])
    assert res_update_word.exit_code == 0
    data = json.loads(res_update_word.output)
    assert data["modified_services"] == ["s3"]

    res_clear = cli_runner.invoke(cli_module.cli, ["--clear-cache"])
    assert res_clear.exit_code == 0
    assert "Cleared" in res_clear.output
