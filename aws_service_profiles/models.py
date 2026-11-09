"""Data models for AWS service metadata."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ActionAnnotations:
    """Represents AWS action annotations (access level and plane properties)."""
    is_list: bool = False
    is_write: bool = False
    is_permission_management: bool = False
    is_tagging_only: bool = False
    is_data_plane: bool = False

    @property
    def access_level(self) -> str:
        """Compute the human-readable IAM access level from annotation properties."""
        if self.is_permission_management:
            return "Permissions management"
        if self.is_tagging_only:
            return "Tagging"
        if self.is_write:
            return "Write"
        if self.is_list:
            return "List"
        return "Read"

    @property
    def plane(self) -> str:
        """Return 'Data Plane' or 'Control Plane'."""
        return "Data Plane" if self.is_data_plane else "Control Plane"


@dataclass
class AuthorizedActionRef:
    """Represents an IAM action authorized/invoked by an API Operation."""
    name: str
    service: str
    context: Optional[Dict[str, str]] = None


@dataclass
class SDKMethodRef:
    """Represents an SDK method mapping for an API Operation (e.g., Boto3)."""
    name: str
    method: str
    package: str


@dataclass
class ServiceOperation:
    """Represents an AWS service API Operation with its authorized IAM actions and SDK methods."""
    name: str
    authorized_actions: List[AuthorizedActionRef] = field(default_factory=list)
    sdk: List[SDKMethodRef] = field(default_factory=list)


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
    annotations: Optional[ActionAnnotations] = None
    supported_by: Optional[Dict[str, bool]] = None


@dataclass
class AWSService:
    """Represents an AWS service with its complete metadata."""
    name: str
    url: str
    service_name: Optional[str] = None
    version: Optional[str] = None
    modified: Optional[int] = None
    actions: Optional[List[ServiceAction]] = None
    resources: Optional[List[ServiceResource]] = None
    condition_keys: Optional[List[str]] = None
    operations: Optional[List[ServiceOperation]] = None
