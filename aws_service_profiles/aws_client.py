"""AWS API client for fetching service metadata and managing local disk cache."""

import functools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests


AWS_SERVICES_S3_URL = "https://servicereference.us-east-1.amazonaws.com/"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "mim"


def extract_access_level(annotations: Optional[Dict[str, Any]]) -> str:
    """Compute human-readable access level from AWS Annotations.Properties."""
    if not annotations or not isinstance(annotations, dict):
        return "Read"
    props = annotations.get("Properties", {})
    if not isinstance(props, dict):
        return "Read"
    if props.get("IsPermissionManagement"):
        return "Permissions management"
    if props.get("IsTaggingOnly"):
        return "Tagging"
    if props.get("IsWrite"):
        return "Write"
    if props.get("IsList"):
        return "List"
    return "Read"


def extract_annotation_properties(annotations: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract normalized annotation properties and computed access_level / plane."""
    props = {}
    if annotations and isinstance(annotations, dict):
        raw_props = annotations.get("Properties", {})
        if isinstance(raw_props, dict):
            props = dict(raw_props)
    is_data_plane = props.get("IsDataPlane")
    return {
        "IsList": bool(props.get("IsList", False)),
        "IsWrite": bool(props.get("IsWrite", False)),
        "IsPermissionManagement": bool(props.get("IsPermissionManagement", False)),
        "IsTaggingOnly": bool(props.get("IsTaggingOnly", False)),
        "IsDataPlane": bool(is_data_plane) if is_data_plane is not None else False,
        "access_level": extract_access_level(annotations),
        "plane": "Data Plane" if is_data_plane else "Control Plane",
    }


class AWSClient:
    """Client for interacting with AWS service reference API with optional disk caching."""

    def __init__(
        self,
        base_url: str = AWS_SERVICES_S3_URL,
        cache_dir: Optional[Path] = None,
        use_disk_cache: bool = True,
    ):
        self.base_url = base_url
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.use_disk_cache = use_disk_cache
        self.services_cache_dir = self.cache_dir / "services"

    def _ensure_cache_dirs(self) -> None:
        if self.use_disk_cache:
            self.services_cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def index_cache_file(self) -> Path:
        return self.cache_dir / "services_index.json"

    @property
    def sync_meta_file(self) -> Path:
        return self.cache_dir / "sync_meta.json"

    def _service_cache_file(self, service_name: str) -> Path:
        safe_name = service_name.replace("/", "_").lower()
        return self.services_cache_dir / f"{safe_name}.json"

    def clear_cache(self) -> int:
        """Clear both in-memory LRU caches and local disk cache files."""
        self.get_aws_services_urls.cache_clear()
        self.find_all_service_metadata.cache_clear()
        self._get_all_unique_context_keys_across_aws_cached.cache_clear()
        self.get_all_unique_context_keys_flattened.cache_clear()
        self.get_all_global_context_keys_across_aws.cache_clear()
        self.get_all_service_specific_context_keys_across_aws.cache_clear()
        self.get_all_service_specific_context_keys_flattened.cache_clear()

        removed_files = 0
        if self.cache_dir.exists():
            for p in self.services_cache_dir.glob("*.json"):
                try:
                    p.unlink()
                    removed_files += 1
                except OSError:
                    pass
            for meta_file in [self.index_cache_file, self.sync_meta_file]:
                if meta_file.exists():
                    try:
                        meta_file.unlink()
                        removed_files += 1
                    except OSError:
                        pass
        return removed_files

    def update_metadata_cache(
        self, service_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Fetch latest service index and optionally refresh specific or cached services on disk."""
        self._ensure_cache_dirs()

        old_index: List[Dict[str, Any]] = []
        if self.index_cache_file.exists():
            try:
                old_index = json.loads(self.index_cache_file.read_text(encoding="utf-8"))
            except Exception:
                old_index = []

        old_by_service = {
            item["service"]: item for item in old_index if isinstance(item, dict) and "service" in item
        }

        response = requests.get(self.base_url, timeout=30)
        response.raise_for_status()
        latest_index: List[Dict[str, Any]] = response.json()

        if self.use_disk_cache:
            self.index_cache_file.write_text(
                json.dumps(latest_index, indent=2), encoding="utf-8"
            )

        self.get_aws_services_urls.cache_clear()
        self.find_all_service_metadata.cache_clear()

        added_services: List[str] = []
        modified_services: List[str] = []
        latest_by_service: Dict[str, Dict[str, Any]] = {}

        for item in latest_index:
            svc = item.get("service")
            if not svc:
                continue
            latest_by_service[svc] = item
            if svc not in old_by_service:
                added_services.append(svc)
            else:
                old_mod = old_by_service[svc].get("modified")
                new_mod = item.get("modified")
                if old_mod is not None and new_mod is not None and old_mod != new_mod:
                    modified_services.append(svc)

        # Refresh requested services or any already-cached services that have been modified upstream
        services_to_refresh = set(service_names or [])
        if not service_names and self.services_cache_dir.exists():
            for cached_path in self.services_cache_dir.glob("*.json"):
                svc_key = cached_path.stem
                if svc_key in modified_services:
                    services_to_refresh.add(svc_key)

        refreshed_services: List[str] = []
        for svc in sorted(services_to_refresh):
            svc_entry = latest_by_service.get(svc.lower()) or latest_by_service.get(svc)
            if not svc_entry:
                continue
            try:
                resp = requests.get(svc_entry["url"], timeout=30)
                resp.raise_for_status()
                svc_data = resp.json()
                if self.use_disk_cache:
                    self._service_cache_file(svc_entry["service"]).write_text(
                        json.dumps(svc_data, indent=2), encoding="utf-8"
                    )
                refreshed_services.append(svc_entry["service"])
            except Exception:
                continue

        sync_timestamp = datetime.now(timezone.utc).isoformat()
        sync_summary = {
            "last_updated": sync_timestamp,
            "total_services": len(latest_index),
            "new_services_count": len(added_services),
            "new_services": sorted(added_services),
            "modified_services_count": len(modified_services),
            "modified_services": sorted(modified_services),
            "refreshed_services": refreshed_services,
        }
        if self.use_disk_cache:
            self.sync_meta_file.write_text(
                json.dumps(sync_summary, indent=2), encoding="utf-8"
            )

        return sync_summary

    def get_cache_status(self) -> Dict[str, Any]:
        """Return information about the local metadata cache."""
        cached_service_files = (
            list(self.services_cache_dir.glob("*.json"))
            if self.services_cache_dir.exists()
            else []
        )
        sync_meta: Dict[str, Any] = {}
        if self.sync_meta_file.exists():
            try:
                sync_meta = json.loads(self.sync_meta_file.read_text(encoding="utf-8"))
            except Exception:
                sync_meta = {}

        return {
            "cache_dir": str(self.cache_dir),
            "index_cached": self.index_cache_file.exists(),
            "cached_services_count": len(cached_service_files),
            "last_updated": sync_meta.get("last_updated"),
            "total_services": sync_meta.get("total_services"),
        }

    @functools.lru_cache(maxsize=1)
    def get_aws_services_urls(self) -> List[Dict[str, Any]]:
        """Get list of all AWS services and their metadata URLs (`service`, `serviceName`, `url`, `modified`)."""
        if self.use_disk_cache and self.index_cache_file.exists():
            try:
                return json.loads(self.index_cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        response = requests.get(self.base_url)
        list_of_services = response.json()

        if self.use_disk_cache:
            try:
                self._ensure_cache_dirs()
                self.index_cache_file.write_text(
                    json.dumps(list_of_services, indent=2), encoding="utf-8"
                )
            except Exception:
                pass

        return list_of_services

    def find_service_entry(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Find the service index entry (`service`, `serviceName`, `url`, `modified`) case-insensitively."""
        if not service_name:
            return None
        all_services = self.get_aws_services_urls()
        target_lower = service_name.lower()

        for service in all_services:
            if service.get("service", "").lower() == target_lower:
                return service
        return None

    def find_service(self, service_name: str) -> Optional[str]:
        """Find the metadata URL for a specific AWS service (case-insensitive)."""
        entry = self.find_service_entry(service_name)
        return entry["url"] if entry else None

    @functools.lru_cache(maxsize=128)
    def find_all_service_metadata(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get all metadata for a specific AWS service, using disk cache if fresh."""
        entry = self.find_service_entry(service_name)
        if not entry:
            return None

        canonical_name = entry.get("service", service_name)
        service_url = entry["url"]
        cache_file = self._service_cache_file(canonical_name)

        if self.use_disk_cache and cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        response = requests.get(service_url)
        metadata = response.json()

        if self.use_disk_cache:
            try:
                self._ensure_cache_dirs()
                cache_file.write_text(
                    json.dumps(metadata, indent=2), encoding="utf-8"
                )
            except Exception:
                pass

        return metadata

    def _find_action_dict(
        self, metadata: Dict[str, Any], action_name: str
    ) -> Optional[Dict[str, Any]]:
        """Find an action dictionary inside service metadata case-insensitively."""
        target_lower = action_name.lower()
        for action in metadata.get("Actions", []):
            if action.get("Name", "").lower() == target_lower:
                return action
        return None

    def _find_operation_dict(
        self, metadata: Dict[str, Any], operation_name: str
    ) -> Optional[Dict[str, Any]]:
        """Find an operation dictionary inside service metadata case-insensitively."""
        target_lower = operation_name.lower()
        for op in metadata.get("Operations", []):
            if op.get("Name", "").lower() == target_lower:
                return op
        return None

    def get_operations_for_service(self, service_name: str) -> List[Dict[str, Any]]:
        """Get all API Operations (`Name`, `AuthorizedActions`, `SDK`) for a service."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []
        return metadata.get("Operations", [])

    def get_operation_details(
        self, service_name: str, operation_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific API Operation."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return None
        op = self._find_operation_dict(metadata, operation_name)
        if not op:
            return None
        return {
            "name": op.get("Name", operation_name),
            "authorized_actions": op.get("AuthorizedActions", []),
            "sdk": op.get("SDK", []),
        }

    def get_operations_for_action(
        self, service_name: str, action_name: str
    ) -> List[Dict[str, Any]]:
        """Find all API Operations in a service that authorize or invoke a specific IAM action."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []
        target_lower = action_name.lower()
        matching_ops: List[Dict[str, Any]] = []
        for op in metadata.get("Operations", []):
            for auth_act in op.get("AuthorizedActions", []):
                if (
                    isinstance(auth_act, dict)
                    and auth_act.get("Name", "").lower() == target_lower
                ):
                    matching_ops.append(op)
                    break
        return matching_ops

    def get_action_metadata(
        self, service_name: str, action_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific action including annotations, supported_by, and resources."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return None

        action = self._find_action_dict(metadata, action_name)
        if not action:
            return None

        canonical_action_name = action["Name"]
        action_condition_keys = action.get("ActionConditionKeys", [])
        annotations_info = extract_annotation_properties(action.get("Annotations"))
        supported_by = action.get("SupportedBy", {})
        linked_operations = self.get_operations_for_action(
            service_name, canonical_action_name
        )

        resources = []
        if "Resources" in action and action["Resources"]:
            for resource in action["Resources"]:
                resource_name = resource["Name"]
                action_scoped_res_keys = resource.get("ConditionKeys", [])
                resource_details = self.get_resource_details(service_name, resource_name)
                if resource_details:
                    merged_keys = sorted(
                        list(
                            set(resource_details["context_keys"])
                            | set(action_scoped_res_keys)
                        )
                    )
                    resources.append(
                        {
                            "name": resource_name,
                            "arn_formats": resource_details["arn_formats"],
                            "condition_keys": merged_keys,
                        }
                    )
                else:
                    resources.append(
                        {
                            "name": resource_name,
                            "arn_formats": ["N/A"],
                            "condition_keys": sorted(list(set(action_scoped_res_keys))),
                        }
                    )
        else:
            resources = [{"name": "*", "arn_formats": ["*"], "condition_keys": []}]

        return {
            "name": canonical_action_name,
            "access_level": annotations_info["access_level"],
            "plane": annotations_info["plane"],
            "annotations": annotations_info,
            "supported_by": supported_by,
            "operations": linked_operations,
            "resources": resources,
            "condition_keys": action_condition_keys,
        }

    def get_action_metadata_with_full_condition_keys(
        self, service_name: str, action_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific action with full condition key metadata, annotations, and operations."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return None

        action = self._find_action_dict(metadata, action_name)
        if not action:
            return None

        canonical_action_name = action["Name"]
        key_lookup = self.get_condition_key_metadata_lookup(service_name)

        action_condition_key_names = action.get("ActionConditionKeys", [])
        action_condition_keys = []
        for key_name in action_condition_key_names:
            if key_name in key_lookup:
                action_condition_keys.append(key_lookup[key_name])
            else:
                action_condition_keys.append({"Name": key_name, "Types": ["Unknown"]})

        annotations_info = extract_annotation_properties(action.get("Annotations"))
        supported_by = action.get("SupportedBy", {})
        linked_operations = self.get_operations_for_action(
            service_name, canonical_action_name
        )

        resources = []
        if "Resources" in action and action["Resources"]:
            for resource in action["Resources"]:
                resource_name = resource["Name"]
                action_scoped_res_keys = resource.get("ConditionKeys", [])
                resource_details = self.get_resource_details_with_full_condition_keys(
                    service_name, resource_name
                )
                if resource_details:
                    existing_names = {
                        ck.get("Name")
                        for ck in resource_details["context_keys"]
                        if isinstance(ck, dict)
                    }
                    combined_context_keys = list(resource_details["context_keys"])
                    for extra_key in action_scoped_res_keys:
                        if extra_key not in existing_names:
                            if extra_key in key_lookup:
                                combined_context_keys.append(key_lookup[extra_key])
                            else:
                                combined_context_keys.append(
                                    {"Name": extra_key, "Types": ["Unknown"]}
                                )
                            existing_names.add(extra_key)

                    resources.append(
                        {
                            "name": resource_name,
                            "arn_formats": resource_details["arn_formats"],
                            "condition_keys": combined_context_keys,
                        }
                    )
                else:
                    fallback_keys = [
                        key_lookup.get(k, {"Name": k, "Types": ["Unknown"]})
                        for k in action_scoped_res_keys
                    ]
                    resources.append(
                        {
                            "name": resource_name,
                            "arn_formats": ["N/A"],
                            "condition_keys": fallback_keys,
                        }
                    )
        else:
            resources = [{"name": "*", "arn_formats": ["*"], "condition_keys": []}]

        return {
            "name": canonical_action_name,
            "access_level": annotations_info["access_level"],
            "plane": annotations_info["plane"],
            "annotations": annotations_info,
            "supported_by": supported_by,
            "operations": linked_operations,
            "resources": resources,
            "condition_keys": action_condition_keys,
        }

    def get_all_actions_for_service(
        self,
        service_name: str,
        access_level: Optional[str] = None,
        plane: Optional[str] = None,
    ) -> List[str]:
        """Pass a service and get all the actions that service supports, with optional filtering."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []

        actions = []
        service_metadata_actions = metadata.get("Actions", [])

        for action in service_metadata_actions:
            props = extract_annotation_properties(action.get("Annotations"))
            if access_level and not self._matches_access_level(
                props["access_level"], access_level
            ):
                continue
            if plane and not self._matches_plane(props["plane"], plane):
                continue
            actions.append(action["Name"])

        return actions

    def get_all_actions_with_metadata_for_service(
        self,
        service_name: str,
        access_level: Optional[str] = None,
        plane: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all actions for a service along with access level, plane, resource count, and condition key count."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []

        detailed_actions: List[Dict[str, Any]] = []
        for action in metadata.get("Actions", []):
            props = extract_annotation_properties(action.get("Annotations"))
            if access_level and not self._matches_access_level(
                props["access_level"], access_level
            ):
                continue
            if plane and not self._matches_plane(props["plane"], plane):
                continue

            resources = action.get("Resources", [])
            cond_keys = action.get("ActionConditionKeys", [])
            supported_by = action.get("SupportedBy", {})
            detailed_actions.append(
                {
                    "name": action["Name"],
                    "access_level": props["access_level"],
                    "plane": props["plane"],
                    "resources_count": len(resources),
                    "condition_keys_count": len(cond_keys),
                    "supported_by": supported_by,
                }
            )
        return detailed_actions

    @staticmethod
    def _matches_access_level(actual_level: str, requested_filter: str) -> bool:
        norm_actual = actual_level.lower()
        norm_req = requested_filter.strip().lower()
        if norm_req in ("permissions", "permission", "permissions-management", "permissions management"):
            return norm_actual == "permissions management"
        return norm_actual == norm_req

    @staticmethod
    def _matches_plane(actual_plane: str, requested_plane: str) -> bool:
        norm_req = requested_plane.strip().lower()
        if norm_req in ("data", "data-plane", "dataplane", "data plane"):
            return actual_plane == "Data Plane"
        if norm_req in ("control", "control-plane", "controlplane", "control plane"):
            return actual_plane == "Control Plane"
        return True

    def get_resources_for_service_action(
        self, service_name: str, action_name: str
    ) -> List[str]:
        """Pass a service and an action and get all the resources supported by that action."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []

        action = self._find_action_dict(metadata, action_name)
        if not action:
            return []

        if "Resources" in action and action["Resources"]:
            return [resource["Name"] for resource in action["Resources"]]
        return ["*"]

    def get_condition_keys_for_service(self, service_name: str) -> List[str]:
        """Get all condition keys available for a service."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []

        condition_keys = metadata.get("ConditionKeys", [])
        return [key["Name"] for key in condition_keys]

    def get_condition_keys_with_metadata_for_service(
        self, service_name: str
    ) -> List[Dict[str, Any]]:
        """Get all condition keys with full metadata for a service."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []

        condition_keys = metadata.get("ConditionKeys", [])
        return condition_keys

    def get_condition_key_metadata_lookup(
        self, service_name: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get a lookup dictionary of condition key names to their full metadata."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return {}

        condition_keys = metadata.get("ConditionKeys", [])
        lookup = {}
        for key in condition_keys:
            lookup[key["Name"]] = key
        return lookup

    def get_condition_keys_for_action(
        self, service_name: str, action_name: str
    ) -> List[str]:
        """Get condition keys that are applicable to a specific action."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []

        action = self._find_action_dict(metadata, action_name)
        if not action:
            return []
        return action.get("ActionConditionKeys", [])

    def get_condition_keys_with_metadata_for_action(
        self, service_name: str, action_name: str
    ) -> List[Dict[str, Any]]:
        """Get condition keys with full metadata for a specific action."""
        action_key_names = self.get_condition_keys_for_action(service_name, action_name)
        if not action_key_names:
            return []

        key_lookup = self.get_condition_key_metadata_lookup(service_name)

        result = []
        for key_name in action_key_names:
            if key_name in key_lookup:
                result.append(key_lookup[key_name])
            else:
                result.append({"Name": key_name, "Types": ["Unknown"]})

        return result

    def get_resource_details(
        self, service_name: str, resource_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific resource including ARN and context keys."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return None

        service_metadata_resources = metadata.get("Resources", [])
        target_lower = resource_name.lower()

        if isinstance(service_metadata_resources, list):
            for resource_data in service_metadata_resources:
                if resource_data.get("Name", "").lower() == target_lower:
                    arn_formats = resource_data.get("ARNFormats", [])
                    if isinstance(arn_formats, list):
                        arn_display = arn_formats if arn_formats else ["N/A"]
                    else:
                        arn_display = [arn_formats] if arn_formats else ["N/A"]

                    resource_condition_keys = resource_data.get("ConditionKeys", [])

                    return {
                        "name": resource_data.get("Name", resource_name),
                        "arn_formats": arn_display,
                        "context_keys": resource_condition_keys,
                    }
        elif isinstance(service_metadata_resources, dict):
            for res_key, resource_data in service_metadata_resources.items():
                if res_key.lower() == target_lower:
                    arn_formats = resource_data.get("ARNFormats", [])
                    if isinstance(arn_formats, list):
                        arn_display = arn_formats if arn_formats else ["N/A"]
                    else:
                        arn_display = [arn_formats] if arn_formats else ["N/A"]

                    resource_condition_keys = resource_data.get("ConditionKeys", [])

                    return {
                        "name": res_key,
                        "arn_formats": arn_display,
                        "context_keys": resource_condition_keys,
                    }

        return None

    def get_resource_details_with_full_condition_keys(
        self, service_name: str, resource_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific resource with full condition key metadata."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return None

        service_metadata_resources = metadata.get("Resources", [])
        key_lookup = self.get_condition_key_metadata_lookup(service_name)
        target_lower = resource_name.lower()

        if isinstance(service_metadata_resources, list):
            for resource_data in service_metadata_resources:
                if resource_data.get("Name", "").lower() == target_lower:
                    arn_formats = resource_data.get("ARNFormats", [])
                    if isinstance(arn_formats, list):
                        arn_display = arn_formats if arn_formats else ["N/A"]
                    else:
                        arn_display = [arn_formats] if arn_formats else ["N/A"]

                    resource_condition_key_names = resource_data.get(
                        "ConditionKeys", []
                    )
                    resource_condition_keys = []
                    for key_name in resource_condition_key_names:
                        if key_name in key_lookup:
                            resource_condition_keys.append(key_lookup[key_name])
                        else:
                            resource_condition_keys.append(
                                {"Name": key_name, "Types": ["Unknown"]}
                            )

                    return {
                        "name": resource_data.get("Name", resource_name),
                        "arn_formats": arn_display,
                        "context_keys": resource_condition_keys,
                    }
        elif isinstance(service_metadata_resources, dict):
            for res_key, resource_data in service_metadata_resources.items():
                if res_key.lower() == target_lower:
                    arn_formats = resource_data.get("ARNFormats", [])
                    if isinstance(arn_formats, list):
                        arn_display = arn_formats if arn_formats else ["N/A"]
                    else:
                        arn_display = [arn_formats] if arn_formats else ["N/A"]

                    resource_condition_key_names = resource_data.get(
                        "ConditionKeys", []
                    )
                    resource_condition_keys = []
                    for key_name in resource_condition_key_names:
                        if key_name in key_lookup:
                            resource_condition_keys.append(key_lookup[key_name])
                        else:
                            resource_condition_keys.append(
                                {"Name": key_name, "Types": ["Unknown"]}
                            )

                    return {
                        "name": res_key,
                        "arn_formats": arn_display,
                        "context_keys": resource_condition_keys,
                    }

        return None

    def get_resources_with_details_for_service_action(
        self, service_name: str, action_name: str
    ) -> List[Dict[str, Any]]:
        """Get resources with ARN and combined action+resource condition keys for a specific service action."""
        action_metadata = self.get_action_metadata(service_name, action_name)
        if action_metadata:
            return action_metadata["resources"]
        return []

    def get_unique_resources_count_for_service(self, service_name: str) -> int:
        """Get the count of unique resources that a service supports."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return 0

        service_metadata_resources = metadata.get("Resources", [])

        if isinstance(service_metadata_resources, list):
            return len(service_metadata_resources)
        elif isinstance(service_metadata_resources, dict):
            return len(service_metadata_resources)

        return 0

    def get_all_unique_resources_for_service(
        self, service_name: str
    ) -> List[Dict[str, Any]]:
        """Get all unique resources that a service supports with their details."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []

        service_metadata_resources = metadata.get("Resources", [])
        detailed_resources = []

        if isinstance(service_metadata_resources, list):
            for resource_data in service_metadata_resources:
                arn_formats = resource_data.get("ARNFormats", [])
                if isinstance(arn_formats, list):
                    arn_display = arn_formats if arn_formats else ["N/A"]
                else:
                    arn_display = [arn_formats] if arn_formats else ["N/A"]

                resource_condition_keys = resource_data.get("ConditionKeys", [])

                detailed_resources.append(
                    {
                        "name": resource_data.get("Name", "Unknown"),
                        "arn_formats": arn_display,
                        "context_keys": resource_condition_keys,
                    }
                )
        elif isinstance(service_metadata_resources, dict):
            for resource_name, resource_data in service_metadata_resources.items():
                arn_formats = resource_data.get("ARNFormats", [])
                if isinstance(arn_formats, list):
                    arn_display = arn_formats if arn_formats else ["N/A"]
                else:
                    arn_display = [arn_formats] if arn_formats else ["N/A"]

                resource_condition_keys = resource_data.get("ConditionKeys", [])

                detailed_resources.append(
                    {
                        "name": resource_name,
                        "arn_formats": arn_display,
                        "context_keys": resource_condition_keys,
                    }
                )

        return detailed_resources

    def get_all_unique_context_keys_for_service(self, service_name: str) -> List[str]:
        """Get all unique context keys for a service across actions, action-resources, resources, and service-level keys."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []

        all_context_keys = set()

        service_keys = self.get_condition_keys_for_service(service_name)
        all_context_keys.update(service_keys)

        service_actions = metadata.get("Actions", [])
        for action in service_actions:
            action_keys = action.get("ActionConditionKeys", [])
            all_context_keys.update(action_keys)
            for res in action.get("Resources", []):
                if isinstance(res, dict):
                    all_context_keys.update(res.get("ConditionKeys", []))

        service_resources = metadata.get("Resources", [])
        if isinstance(service_resources, list):
            for resource_data in service_resources:
                resource_keys = resource_data.get("ConditionKeys", [])
                all_context_keys.update(resource_keys)
        elif isinstance(service_resources, dict):
            for resource_data in service_resources.values():
                resource_keys = resource_data.get("ConditionKeys", [])
                all_context_keys.update(resource_keys)

        return sorted(list(all_context_keys))

    @functools.lru_cache(maxsize=1)
    def _get_all_unique_context_keys_across_aws_cached(self) -> Dict[str, List[str]]:
        """Cached version of context keys retrieval across all AWS services."""
        all_services = self.get_aws_services_urls()
        context_keys_by_service = {}

        for service in all_services:
            service_name = service["service"]
            try:
                service_keys = self.get_all_unique_context_keys_for_service(
                    service_name
                )
                if service_keys:
                    context_keys_by_service[service_name] = service_keys
            except Exception:
                continue

        return context_keys_by_service

    def get_all_unique_context_keys_across_aws(
        self, show_progress: bool = False
    ) -> Dict[str, List[str]]:
        """Get all unique context keys across all AWS services with service attribution."""
        if not show_progress:
            return self._get_all_unique_context_keys_across_aws_cached()

        try:
            all_services = self.get_aws_services_urls()
            context_keys_by_service = {}

            from rich.progress import (
                Progress,
                SpinnerColumn,
                TextColumn,
                BarColumn,
                TaskProgressColumn,
            )
            from rich.console import Console

            console = Console()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Fetching context keys from AWS services...",
                    total=len(all_services),
                )

                for service in all_services:
                    service_name = service["service"]
                    try:
                        service_keys = self.get_all_unique_context_keys_for_service(
                            service_name
                        )
                        if service_keys:
                            context_keys_by_service[service_name] = service_keys
                    except Exception:
                        pass
                    progress.update(task, advance=1)
            return context_keys_by_service
        except ImportError:
            return self._get_all_unique_context_keys_across_aws_cached()

    @functools.lru_cache(maxsize=1)
    def get_all_unique_context_keys_flattened(self) -> List[str]:
        """Get a flattened list of all unique context keys across all AWS services."""
        all_keys = set()
        context_keys_by_service = self.get_all_unique_context_keys_across_aws()

        for service_keys in context_keys_by_service.values():
            all_keys.update(service_keys)

        return sorted(list(all_keys))

    def separate_global_and_service_context_keys(
        self, context_keys: List[str]
    ) -> Dict[str, List[str]]:
        """Separate context keys into AWS global (aws:) and service-specific keys."""
        global_keys = []
        service_keys = []

        for key in context_keys:
            if key.startswith("aws:"):
                global_keys.append(key)
            else:
                service_keys.append(key)

        return {
            "global_keys": sorted(global_keys),
            "service_keys": sorted(service_keys),
        }

    def get_separated_context_keys_for_service(
        self, service_name: str
    ) -> Dict[str, List[str]]:
        """Get context keys for a service separated into global and service-specific."""
        all_keys = self.get_all_unique_context_keys_for_service(service_name)
        return self.separate_global_and_service_context_keys(all_keys)

    def get_global_context_keys_for_service(self, service_name: str) -> List[str]:
        """Get only the AWS global context keys (aws:) for a service."""
        separated = self.get_separated_context_keys_for_service(service_name)
        return separated["global_keys"]

    def get_service_specific_context_keys_for_service(
        self, service_name: str
    ) -> List[str]:
        """Get only the service-specific context keys (non-aws:) for a service."""
        separated = self.get_separated_context_keys_for_service(service_name)
        return separated["service_keys"]

    @functools.lru_cache(maxsize=1)
    def get_all_global_context_keys_across_aws(self) -> List[str]:
        """Get all unique AWS global context keys (aws:) across all services."""
        all_keys = self.get_all_unique_context_keys_flattened()
        global_keys = [key for key in all_keys if key.startswith("aws:")]
        return sorted(global_keys)

    @functools.lru_cache(maxsize=1)
    def get_all_service_specific_context_keys_across_aws(
        self,
    ) -> Dict[str, List[str]]:
        """Get all service-specific context keys across all AWS services (non-aws: prefix)."""
        context_keys_by_service = self.get_all_unique_context_keys_across_aws()
        service_specific_by_service = {}

        for service, keys in context_keys_by_service.items():
            service_keys = [key for key in keys if not key.startswith("aws:")]
            if service_keys:
                service_specific_by_service[service] = sorted(service_keys)

        return service_specific_by_service

    @functools.lru_cache(maxsize=1)
    def get_all_service_specific_context_keys_flattened(self) -> List[str]:
        """Get a flattened list of all unique service-specific context keys across AWS."""
        service_keys_by_service = (
            self.get_all_service_specific_context_keys_across_aws()
        )
        all_service_keys = set()

        for keys in service_keys_by_service.values():
            all_service_keys.update(keys)

        return sorted(list(all_service_keys))

    def get_condition_key_types_for_service(self, service_name: str) -> List[str]:
        """Get all unique condition key types used by a service."""
        condition_keys = self.get_condition_keys_with_metadata_for_service(service_name)
        all_types = set()

        for key in condition_keys:
            types = key.get("Types", [])
            all_types.update(types)

        return sorted(list(all_types))
