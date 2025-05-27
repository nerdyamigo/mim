"""Data models for AWS service metadata."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ServiceResource:
    """Represents an AWS service resource with its metadata."""
    name: str
    arn_formats: List[str]
    context_keys: List[str]


@dataclass
class ServiceAction:
    """Represents an AWS service action with its metadata."""
    name: str
    resources: List[str]
    condition_keys: List[str]


@dataclass
class AWSService:
    """Represents an AWS service with its complete metadata."""
    name: str
    url: str
    actions: Optional[List[ServiceAction]] = None
    resources: Optional[List[ServiceResource]] = None
    condition_keys: Optional[List[str]] = None