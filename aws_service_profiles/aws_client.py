"""AWS API client for fetching service metadata."""

import functools
from typing import Dict, List, Optional, Any
import requests


AWS_SERVICES_S3_URL = 'https://servicereference.us-east-1.amazonaws.com/'


class AWSClient:
    """Client for interacting with AWS service reference API."""
    
    def __init__(self, base_url: str = AWS_SERVICES_S3_URL):
        self.base_url = base_url
    
    @functools.lru_cache(maxsize=1)
    def get_aws_services_urls(self) -> List[Dict[str, str]]:
        """Get list of all AWS services and their metadata URLs."""
        response = requests.get(self.base_url)
        list_of_services = response.json()
        return list_of_services
    
    def find_service(self, service_name: str) -> Optional[str]:
        """Find the metadata URL for a specific AWS service."""
        all_services = self.get_aws_services_urls()
        for service in all_services:
            if service['service'] == service_name:
                return service['url']
        return None
    
    @functools.lru_cache(maxsize=128)
    def find_all_service_metadata(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get all metadata for a specific AWS service."""
        service_url = self.find_service(service_name)
        if not service_url:
            return None
        
        response = requests.get(service_url)
        metadata = response.json()
        return metadata
    
    def get_action_metadata(self, service_name: str, action_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific action without fetching the entire service metadata."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return None
        
        service_metadata_actions = metadata.get("Actions", [])
        
        for action in service_metadata_actions:
            if action['Name'] == action_name:
                # Get condition keys specific to this action
                action_condition_keys = action.get('ActionConditionKeys', [])
                
                # Get resources for this action
                resources = []
                if "Resources" in action:
                    for resource in action['Resources']:
                        resource_name = resource['Name']
                        # Get resource details including its condition keys
                        resource_details = self.get_resource_details(service_name, resource_name)
                        if resource_details:
                            resources.append({
                                'name': resource_name,
                                'arn_formats': resource_details['arn_formats'],
                                'condition_keys': resource_details['context_keys']
                            })
                        else:
                            # Fallback if resource details not found
                            resources.append({
                                'name': resource_name,
                                'arn_formats': ['N/A'],
                                'condition_keys': []
                            })
                else:
                    resources = [{'name': '*', 'arn_formats': ['*'], 'condition_keys': []}]
                
                return {
                    'name': action_name,
                    'resources': resources,
                    'condition_keys': action_condition_keys
                }
        
        return None
    
    def get_all_actions_for_service(self, service_name: str) -> List[str]:
        """Pass a service and get all the actions that service supports."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []
        
        actions = []
        service_metadata_actions = metadata.get("Actions", [])
        
        for action in service_metadata_actions:
            actions.append(action['Name'])
        
        return actions
    
    def get_resources_for_service_action(self, service_name: str, action_name: str) -> List[str]:
        """Pass a service and an action and get all the resources supported by that action."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []
        
        service_metadata_actions = metadata.get("Actions", [])
        
        for action in service_metadata_actions:
            if action['Name'] == action_name:
                if "Resources" in action:
                    return [resource['Name'] for resource in action['Resources']]
                else:
                    return ['*']  # Action supports all resources
        
        return []
    
    def get_condition_keys_for_service(self, service_name: str) -> List[str]:
        """Get all condition keys available for a service."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []
        
        condition_keys = metadata.get("ConditionKeys", [])
        return [key['Name'] for key in condition_keys]
    
    def get_condition_keys_for_action(self, service_name: str, action_name: str) -> List[str]:
        """Get condition keys that are applicable to a specific action."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []
        
        service_metadata_actions = metadata.get("Actions", [])
        
        for action in service_metadata_actions:
            if action['Name'] == action_name:
                # Get condition keys specific to this action
                action_condition_keys = action.get('ActionConditionKeys', [])
                return action_condition_keys
        
        return []
    
    def get_resource_details(self, service_name: str, resource_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific resource including ARN and context keys."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return None
        
        service_metadata_resources = metadata.get("Resources", {})
        
        # Handle both dict and list formats
        if isinstance(service_metadata_resources, dict):
            if resource_name in service_metadata_resources:
                resource_data = service_metadata_resources[resource_name]
                arn_formats = resource_data.get('ARNFormats', [])
                # Handle ARNFormats as list or single value
                if isinstance(arn_formats, list):
                    arn_display = arn_formats if arn_formats else ['N/A']
                else:
                    arn_display = [arn_formats] if arn_formats else ['N/A']
                
                # Get condition keys specific to this resource
                resource_condition_keys = resource_data.get('ConditionKeys', [])
                
                return {
                    'name': resource_name,
                    'arn_formats': arn_display,
                    'context_keys': resource_condition_keys
                }
        elif isinstance(service_metadata_resources, list):
            for resource_data in service_metadata_resources:
                if resource_data.get('Name') == resource_name:
                    arn_formats = resource_data.get('ARNFormats', [])
                    # Handle ARNFormats as list or single value
                    if isinstance(arn_formats, list):
                        arn_display = arn_formats if arn_formats else ['N/A']
                    else:
                        arn_display = [arn_formats] if arn_formats else ['N/A']
                    
                    # Get condition keys specific to this resource
                    resource_condition_keys = resource_data.get('ConditionKeys', [])
                    
                    return {
                        'name': resource_name,
                        'arn_formats': arn_display,
                        'context_keys': resource_condition_keys
                    }
        
        return None
    
    def get_resources_with_details_for_service_action(self, service_name: str, action_name: str) -> List[Dict[str, Any]]:
        """Get resources with ARN and combined action+resource condition keys for a specific service action."""
        action_metadata = self.get_action_metadata(service_name, action_name)
        if action_metadata:
            return action_metadata['resources']
        return []
    
    def get_unique_resources_count_for_service(self, service_name: str) -> int:
        """Get the count of unique resources that a service supports."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return 0
        
        service_metadata_resources = metadata.get("Resources", {})
        
        # Handle both dict and list formats
        if isinstance(service_metadata_resources, dict):
            return len(service_metadata_resources)
        elif isinstance(service_metadata_resources, list):
            return len(service_metadata_resources)
        
        return 0
    
    def get_all_unique_resources_for_service(self, service_name: str) -> List[Dict[str, Any]]:
        """Get all unique resources that a service supports with their details."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []
        
        service_metadata_resources = metadata.get("Resources", {})
        detailed_resources = []
        
        # Handle both dict and list formats
        if isinstance(service_metadata_resources, dict):
            for resource_name, resource_data in service_metadata_resources.items():
                arn_formats = resource_data.get('ARNFormats', [])
                # Handle ARNFormats as list or single value
                if isinstance(arn_formats, list):
                    arn_display = arn_formats if arn_formats else ['N/A']
                else:
                    arn_display = [arn_formats] if arn_formats else ['N/A']
                
                # Get condition keys specific to this resource
                resource_condition_keys = resource_data.get('ConditionKeys', [])
                
                detailed_resources.append({
                    'name': resource_name,
                    'arn_formats': arn_display,
                    'context_keys': resource_condition_keys
                })
        elif isinstance(service_metadata_resources, list):
            for resource_data in service_metadata_resources:
                arn_formats = resource_data.get('ARNFormats', [])
                # Handle ARNFormats as list or single value
                if isinstance(arn_formats, list):
                    arn_display = arn_formats if arn_formats else ['N/A']
                else:
                    arn_display = [arn_formats] if arn_formats else ['N/A']
                
                # Get condition keys specific to this resource
                resource_condition_keys = resource_data.get('ConditionKeys', [])
                
                detailed_resources.append({
                    'name': resource_data.get('Name', 'Unknown'),
                    'arn_formats': arn_display,
                    'context_keys': resource_condition_keys
                })
        
        return detailed_resources
    
    def get_all_unique_context_keys_for_service(self, service_name: str) -> List[str]:
        """Get all unique context keys for a service across actions, resources, and service-level keys."""
        metadata = self.find_all_service_metadata(service_name)
        if not metadata:
            return []
        
        all_context_keys = set()
        
        # Get service-level condition keys
        service_keys = self.get_condition_keys_for_service(service_name)
        all_context_keys.update(service_keys)
        
        # Get action-specific condition keys
        service_actions = metadata.get("Actions", [])
        for action in service_actions:
            action_keys = action.get('ActionConditionKeys', [])
            all_context_keys.update(action_keys)
        
        # Get resource-specific condition keys
        service_resources = metadata.get("Resources", {})
        if isinstance(service_resources, dict):
            for resource_data in service_resources.values():
                resource_keys = resource_data.get('ConditionKeys', [])
                all_context_keys.update(resource_keys)
        elif isinstance(service_resources, list):
            for resource_data in service_resources:
                resource_keys = resource_data.get('ConditionKeys', [])
                all_context_keys.update(resource_keys)
        
        return sorted(list(all_context_keys))
    
    @functools.lru_cache(maxsize=1)
    def _get_all_unique_context_keys_across_aws_cached(self) -> Dict[str, List[str]]:
        """Cached version of context keys retrieval across all AWS services."""
        all_services = self.get_aws_services_urls()
        context_keys_by_service = {}
        
        for service in all_services:
            service_name = service['service']
            try:
                service_keys = self.get_all_unique_context_keys_for_service(service_name)
                if service_keys:  # Only include services that have context keys
                    context_keys_by_service[service_name] = service_keys
            except Exception:
                # Skip services that fail to load metadata
                continue
        
        return context_keys_by_service
    
    def get_all_unique_context_keys_across_aws(self, show_progress: bool = False) -> Dict[str, List[str]]:
        """Get all unique context keys across all AWS services with service attribution."""
        # Check if we already have cached data
        try:
            # Try to get from cache first
            return self._get_all_unique_context_keys_across_aws_cached()
        except:
            # If cache is empty, compute with optional progress indicator
            all_services = self.get_aws_services_urls()
            context_keys_by_service = {}
            
            if show_progress:
                try:
                    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
                    from rich.console import Console
                    console = Console()
                    
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        TaskProgressColumn(),
                        console=console,
                    ) as progress:
                        task = progress.add_task("Fetching context keys from AWS services...", total=len(all_services))
                        
                        for service in all_services:
                            service_name = service['service']
                            try:
                                service_keys = self.get_all_unique_context_keys_for_service(service_name)
                                if service_keys:  # Only include services that have context keys
                                    context_keys_by_service[service_name] = service_keys
                            except Exception:
                                # Skip services that fail to load metadata
                                pass
                            progress.update(task, advance=1)
                except ImportError:
                    # Fallback to no progress indicator if rich is not available
                    return self._get_all_unique_context_keys_across_aws_cached()
            else:
                return self._get_all_unique_context_keys_across_aws_cached()
            
            return context_keys_by_service
    
    @functools.lru_cache(maxsize=1)
    def get_all_unique_context_keys_flattened(self) -> List[str]:
        """Get a flattened list of all unique context keys across all AWS services."""
        all_keys = set()
        context_keys_by_service = self.get_all_unique_context_keys_across_aws()
        
        for service_keys in context_keys_by_service.values():
            all_keys.update(service_keys)
        
        return sorted(list(all_keys))
    
    def separate_global_and_service_context_keys(self, context_keys: List[str]) -> Dict[str, List[str]]:
        """Separate context keys into AWS global (aws:) and service-specific keys."""
        global_keys = []
        service_keys = []
        
        for key in context_keys:
            if key.startswith('aws:'):
                global_keys.append(key)
            else:
                service_keys.append(key)
        
        return {
            'global_keys': sorted(global_keys),
            'service_keys': sorted(service_keys)
        }
    
    def get_separated_context_keys_for_service(self, service_name: str) -> Dict[str, List[str]]:
        """Get context keys for a service separated into global and service-specific."""
        all_keys = self.get_all_unique_context_keys_for_service(service_name)
        return self.separate_global_and_service_context_keys(all_keys)
    
    def get_global_context_keys_for_service(self, service_name: str) -> List[str]:
        """Get only the AWS global context keys (aws:) for a service."""
        separated = self.get_separated_context_keys_for_service(service_name)
        return separated['global_keys']
    
    def get_service_specific_context_keys_for_service(self, service_name: str) -> List[str]:
        """Get only the service-specific context keys (non-aws:) for a service."""
        separated = self.get_separated_context_keys_for_service(service_name)
        return separated['service_keys']
    
    @functools.lru_cache(maxsize=1)
    def get_all_global_context_keys_across_aws(self) -> List[str]:
        """Get all unique AWS global context keys (aws:) across all services."""
        all_keys = self.get_all_unique_context_keys_flattened()
        global_keys = [key for key in all_keys if key.startswith('aws:')]
        return sorted(global_keys)
    
    @functools.lru_cache(maxsize=1)
    def get_all_service_specific_context_keys_across_aws(self) -> Dict[str, List[str]]:
        """Get all service-specific context keys across all AWS services (non-aws: prefix)."""
        context_keys_by_service = self.get_all_unique_context_keys_across_aws()
        service_specific_by_service = {}
        
        for service, keys in context_keys_by_service.items():
            service_keys = [key for key in keys if not key.startswith('aws:')]
            if service_keys:  # Only include services with service-specific keys
                service_specific_by_service[service] = sorted(service_keys)
        
        return service_specific_by_service
    
    @functools.lru_cache(maxsize=1)
    def get_all_service_specific_context_keys_flattened(self) -> List[str]:
        """Get a flattened list of all unique service-specific context keys across AWS."""
        service_keys_by_service = self.get_all_service_specific_context_keys_across_aws()
        all_service_keys = set()
        
        for keys in service_keys_by_service.values():
            all_service_keys.update(keys)
        
        return sorted(list(all_service_keys))