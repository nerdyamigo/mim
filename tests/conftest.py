"""Shared pytest fixtures for AWS Service Profiles CLI tests."""

import json
import pytest
from typing import Dict, Any, List
from aws_service_profiles.aws_client import AWSClient


MOCK_SERVICES_INDEX: List[Dict[str, Any]] = [
    {
        "service": "s3",
        "serviceName": "Amazon S3",
        "url": "https://servicereference.us-east-1.amazonaws.com/v1/s3/s3.json",
        "modified": 1793502266,
    },
    {
        "service": "ec2",
        "serviceName": "Amazon EC2",
        "url": "https://servicereference.us-east-1.amazonaws.com/v1/ec2/ec2.json",
        "modified": 1793488702,
    },
    {
        "service": "bedrock",
        "serviceName": "Amazon Bedrock",
        "url": "https://servicereference.us-east-1.amazonaws.com/v1/bedrock/bedrock.json",
        "modified": 1793488500,
    },
]


MOCK_S3_METADATA: Dict[str, Any] = {
    "Name": "s3",
    "ServiceName": "Amazon S3",
    "Version": "v1.5",
    "Actions": [
        {
            "Name": "GetObject",
            "ActionConditionKeys": [
                "s3:ExistingObjectTag/<key>",
                "s3:RequestObjectTagKeys",
                "aws:RequestTag/${TagKey}",
            ],
            "Annotations": {
                "Properties": {
                    "IsDataPlane": True,
                    "IsList": False,
                    "IsPermissionManagement": False,
                    "IsTaggingOnly": False,
                    "IsWrite": False,
                }
            },
            "Resources": [
                {"Name": "object"},
            ],
            "SupportedBy": {
                "IAM Access Analyzer Policy Generation": True,
                "IAM Action Last Accessed": False,
            },
        },
        {
            "Name": "PutObject",
            "ActionConditionKeys": [
                "s3:x-amz-acl",
                "aws:RequestTag/${TagKey}",
            ],
            "Annotations": {
                "Properties": {
                    "IsDataPlane": True,
                    "IsList": False,
                    "IsPermissionManagement": False,
                    "IsTaggingOnly": False,
                    "IsWrite": True,
                }
            },
            "Resources": [
                {"Name": "object"},
            ],
            "SupportedBy": {
                "IAM Access Analyzer Policy Generation": True,
                "IAM Action Last Accessed": False,
            },
        },
        {
            "Name": "AbortMultipartUpload",
            "ActionConditionKeys": [
                "s3:AccessPointNetworkOrigin",
                "s3:ResourceAccount",
            ],
            "Annotations": {
                "Properties": {
                    "IsDataPlane": True,
                    "IsList": False,
                    "IsPermissionManagement": False,
                    "IsTaggingOnly": False,
                    "IsWrite": True,
                }
            },
            "Resources": [
                {"Name": "object"},
                {"Name": "accesspointobject"},
            ],
            "SupportedBy": {
                "IAM Access Analyzer Policy Generation": False,
                "IAM Action Last Accessed": False,
            },
        },
        {
            "Name": "CreateBucket",
            "ActionConditionKeys": [
                "s3:LocationConstraint",
            ],
            "Annotations": {
                "Properties": {
                    "IsDataPlane": False,
                    "IsList": False,
                    "IsPermissionManagement": False,
                    "IsTaggingOnly": False,
                    "IsWrite": True,
                }
            },
            "Resources": [
                {"Name": "bucket"},
            ],
            "SupportedBy": {
                "IAM Access Analyzer Policy Generation": True,
                "IAM Action Last Accessed": True,
            },
        },
        {
            "Name": "ListAllMyBuckets",
            "Annotations": {
                "Properties": {
                    "IsDataPlane": False,
                    "IsList": True,
                    "IsPermissionManagement": False,
                    "IsTaggingOnly": False,
                    "IsWrite": False,
                }
            },
            "SupportedBy": {
                "IAM Access Analyzer Policy Generation": True,
                "IAM Action Last Accessed": True,
            },
        },
        {
            "Name": "PutBucketPolicy",
            "Annotations": {
                "Properties": {
                    "IsDataPlane": False,
                    "IsList": False,
                    "IsPermissionManagement": True,
                    "IsTaggingOnly": False,
                    "IsWrite": False,
                }
            },
            "Resources": [
                {"Name": "bucket"},
            ],
            "SupportedBy": {
                "IAM Access Analyzer Policy Generation": True,
                "IAM Action Last Accessed": True,
            },
        },
        {
            "Name": "PutBucketTagging",
            "Annotations": {
                "Properties": {
                    "IsDataPlane": False,
                    "IsList": False,
                    "IsPermissionManagement": False,
                    "IsTaggingOnly": True,
                    "IsWrite": False,
                }
            },
            "Resources": [
                {"Name": "bucket"},
            ],
            "SupportedBy": {
                "IAM Access Analyzer Policy Generation": True,
                "IAM Action Last Accessed": True,
            },
        },
    ],
    "Resources": [
        {
            "Name": "bucket",
            "ARNFormats": ["arn:${Partition}:s3:::${BucketName}"],
            "ConditionKeys": ["s3:ResourceAccount", "aws:ResourceTag/${TagKey}"],
        },
        {
            "Name": "object",
            "ARNFormats": ["arn:${Partition}:s3:::${BucketName}/${ObjectName}"],
            "ConditionKeys": ["s3:ExistingObjectTag/<key>", "s3:ResourceAccount"],
        },
        {
            "Name": "accesspointobject",
            "ARNFormats": [
                "arn:${Partition}:s3:${Region}:${Account}:accesspoint/${AccessPointName}/object/${ObjectName}"
            ],
            "ConditionKeys": ["s3:DataAccessPointArn"],
        },
    ],
    "ConditionKeys": [
        {"Name": "aws:RequestTag/${TagKey}", "Types": ["String"]},
        {"Name": "aws:ResourceTag/${TagKey}", "Types": ["String"]},
        {"Name": "s3:AccessPointNetworkOrigin", "Types": ["String"]},
        {"Name": "s3:DataAccessPointArn", "Types": ["ARN"]},
        {"Name": "s3:ExistingObjectTag/<key>", "Types": ["String"]},
        {"Name": "s3:LocationConstraint", "Types": ["String"]},
        {"Name": "s3:RequestObjectTagKeys", "Types": ["ArrayOfString"]},
        {"Name": "s3:ResourceAccount", "Types": ["String"]},
        {"Name": "s3:x-amz-acl", "Types": ["String"]},
    ],
    "Operations": [
        {
            "Name": "AbortMultipartUpload",
            "AuthorizedActions": [
                {"Name": "AbortMultipartUpload", "Service": "s3"},
            ],
            "SDK": [
                {"Name": "S3", "Method": "abort_multipart_upload", "Package": "Boto3"},
                {"Name": "S3", "Method": "abortMultipartUpload", "Package": "AWS SDK for Java v2"},
            ],
        },
        {
            "Name": "CopyObject",
            "AuthorizedActions": [
                {"Name": "GetObject", "Service": "s3"},
                {"Name": "PutObject", "Service": "s3"},
            ],
            "SDK": [
                {"Name": "S3", "Method": "copy_object", "Package": "Boto3"},
            ],
        },
        {
            "Name": "CreateBucket",
            "AuthorizedActions": [
                {"Name": "CreateBucket", "Service": "s3"},
            ],
            "SDK": [
                {"Name": "S3", "Method": "create_bucket", "Package": "Boto3"},
            ],
        },
    ],
}


MOCK_EC2_METADATA: Dict[str, Any] = {
    "Name": "ec2",
    "ServiceName": "Amazon EC2",
    "Version": "v1.5",
    "Actions": [
        {
            "Name": "RunInstances",
            "ActionConditionKeys": ["ec2:InstanceType", "aws:RequestTag/${TagKey}"],
            "Annotations": {
                "Properties": {
                    "IsDataPlane": False,
                    "IsList": False,
                    "IsPermissionManagement": False,
                    "IsTaggingOnly": False,
                    "IsWrite": True,
                }
            },
            "Resources": [
                {
                    "Name": "instance",
                    "ConditionKeys": ["ec2:PlacementGroupStrategy"],
                },
                {"Name": "image"},
            ],
            "SupportedBy": {
                "IAM Access Analyzer Policy Generation": True,
                "IAM Action Last Accessed": True,
            },
        },
        {
            "Name": "DescribeInstances",
            "Annotations": {
                "Properties": {
                    "IsDataPlane": False,
                    "IsList": True,
                    "IsPermissionManagement": False,
                    "IsTaggingOnly": False,
                    "IsWrite": False,
                }
            },
            "SupportedBy": {
                "IAM Access Analyzer Policy Generation": True,
                "IAM Action Last Accessed": True,
            },
        },
    ],
    "Resources": [
        {
            "Name": "instance",
            "ARNFormats": ["arn:${Partition}:ec2:${Region}:${Account}:instance/${InstanceId}"],
            "ConditionKeys": ["ec2:InstanceType", "aws:ResourceTag/${TagKey}"],
        },
        {
            "Name": "image",
            "ARNFormats": ["arn:${Partition}:ec2:${Region}::image/${ImageId}"],
            "ConditionKeys": ["ec2:Owner"],
        },
    ],
    "ConditionKeys": [
        {"Name": "aws:RequestTag/${TagKey}", "Types": ["String"]},
        {"Name": "aws:ResourceTag/${TagKey}", "Types": ["String"]},
        {"Name": "ec2:InstanceType", "Types": ["String"]},
        {"Name": "ec2:Owner", "Types": ["String"]},
        {"Name": "ec2:PlacementGroupStrategy", "Types": ["String"]},
    ],
    "Operations": [
        {
            "Name": "RunInstances",
            "AuthorizedActions": [
                {"Name": "RunInstances", "Service": "ec2"},
                {
                    "Name": "CreateTags",
                    "Service": "ec2",
                    "Context": {
                        "Description": "When tags are specified in the request.",
                        "Conditions": ["When tags are passed"],
                    },
                },
            ],
            "SDK": [
                {"Name": "EC2", "Method": "run_instances", "Package": "Boto3"},
            ],
        }
    ],
}


@pytest.fixture
def mock_aws_client(tmp_path):
    """Provide an AWSClient pre-populated with local disk cache fixtures."""
    cache_dir = tmp_path / "cache"
    client = AWSClient(cache_dir=cache_dir, use_disk_cache=True)
    client._ensure_cache_dirs()

    client.index_cache_file.write_text(
        json.dumps(MOCK_SERVICES_INDEX, indent=2), encoding="utf-8"
    )
    client._service_cache_file("s3").write_text(
        json.dumps(MOCK_S3_METADATA, indent=2), encoding="utf-8"
    )
    client._service_cache_file("ec2").write_text(
        json.dumps(MOCK_EC2_METADATA, indent=2), encoding="utf-8"
    )
    client._service_cache_file("bedrock").write_text(
        json.dumps(
            {
                "Name": "bedrock",
                "ServiceName": "Amazon Bedrock",
                "Version": "v1.5",
                "Actions": [],
                "Resources": [],
                "ConditionKeys": [],
                "Operations": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return client
