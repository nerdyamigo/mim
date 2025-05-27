"""Service helper functions for providing detailed service information."""

import click
from typing import Optional, Dict, Any
from .aws_client import AWSClient


class ServiceHelper:
    """Helper class for providing service-specific information and help."""
    
    def __init__(self, client: AWSClient):
        self.client = client
    
    def is_valid_service(self, service_name: str) -> bool:
        """Check if a service name is valid."""
        try:
            services = self.client.get_aws_services_urls()
            service_names = [service['service'] for service in services]
            return service_name in service_names
        except Exception:
            return False
    
    def get_service_summary(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get a summary of service information for help display."""
        if not self.is_valid_service(service_name):
            return None
        
        try:
            # Get counts for different types of information
            actions = self.client.get_all_actions_for_service(service_name)
            resources = self.client.get_all_unique_resources_for_service(service_name)
            context_keys = self.client.get_all_unique_context_keys_for_service(service_name)
            global_keys = self.client.get_global_context_keys_for_service(service_name)
            service_keys = self.client.get_service_specific_context_keys_for_service(service_name)
            
            return {
                'service_name': service_name,
                'actions_count': len(actions),
                'resources_count': len(resources),
                'total_context_keys': len(context_keys),
                'global_context_keys': len(global_keys),
                'service_context_keys': len(service_keys),
                'sample_actions': actions[:5] if actions else [],
                'sample_resources': [r['name'] for r in resources[:5]] if resources else [],
                'sample_context_keys': context_keys[:5] if context_keys else []
            }
        except Exception:
            return None
    
    def format_service_help(self, service_name: str) -> str:
        """Format service-specific help text."""
        summary = self.get_service_summary(service_name)
        if not summary:
            return f"Service '{service_name}' not found or unavailable."
        
        help_text = f"""
Service: {summary['service_name'].upper()}

📊 Available Data:
  • Actions: {summary['actions_count']}
  • Resources: {summary['resources_count']}
  • Context Keys: {summary['total_context_keys']} (AWS Global: {summary['global_context_keys']}, Service-Specific: {summary['service_context_keys']})

🔍 Sample Actions:
"""
        
        for action in summary['sample_actions']:
            help_text += f"  • {action}\n"
        
        if summary['actions_count'] > 5:
            help_text += f"  ... and {summary['actions_count'] - 5} more\n"
        
        if summary['sample_resources']:
            help_text += f"\n🏗️  Sample Resources:\n"
            for resource in summary['sample_resources']:
                help_text += f"  • {resource}\n"
            
            if summary['resources_count'] > 5:
                help_text += f"  ... and {summary['resources_count'] - 5} more\n"
        
        if summary['sample_context_keys']:
            help_text += f"\n🔑 Sample Context Keys:\n"
            for key in summary['sample_context_keys']:
                help_text += f"  • {key}\n"
            
            if summary['total_context_keys'] > 5:
                help_text += f"  ... and {summary['total_context_keys'] - 5} more\n"
        
        help_text += f"""
💡 Common Usage Examples:
  mim {service_name}                        # List all actions
  mim {service_name} --context-keys         # Show all context keys
  mim {service_name} --global-context-keys  # Show AWS global keys only
  mim {service_name} --service-context-keys # Show service-specific keys only
  mim {service_name} --resources            # Show all resources
  mim {service_name} --count                # Show counts only
"""
        
        if summary['sample_actions']:
            sample_action = summary['sample_actions'][0]
            help_text += f"  mim {service_name} {sample_action}        # Get resources for specific action\n"
            help_text += f"  mim {service_name} --action {sample_action} # Get action details\n"
        
        help_text += f"""
📋 Output Formats:
  --format table    # Structured table (default)
  --format json     # Machine-readable JSON
  --format yaml     # Human-readable YAML
  --format text     # Simple text list
"""
        
        return help_text
    
    def get_similar_services(self, invalid_service: str, max_suggestions: int = 5) -> list:
        """Get similar service names for typo suggestions."""
        try:
            services = self.client.get_aws_services_urls()
            service_names = [service['service'] for service in services]
            
            # Simple similarity based on common substrings
            suggestions = []
            invalid_lower = invalid_service.lower()
            
            for service in service_names:
                service_lower = service.lower()
                # Check for substring matches or similar starts
                if (invalid_lower in service_lower or 
                    service_lower.startswith(invalid_lower[:3]) or
                    any(part in service_lower for part in invalid_lower.split('-') if len(part) > 2)):
                    suggestions.append(service)
            
            return suggestions[:max_suggestions]
        except Exception:
            return []


def validate_service_name(ctx, param, value):
    """Click callback to validate service names and provide helpful suggestions."""
    if value is None:
        return value
    
    # Skip validation for global operations
    if any(ctx.params.get(flag) for flag in [
        'list_services', 'list_all_context_keys', 
        'list_global_context_keys', 'list_service_context_keys'
    ]):
        return value
    
    try:
        client = AWSClient()
        helper = ServiceHelper(client)
        
        if not helper.is_valid_service(value):
            suggestions = helper.get_similar_services(value)
            error_msg = f"Invalid service name: '{value}'"
            
            if suggestions:
                error_msg += f"\n\nDid you mean one of these?\n"
                for suggestion in suggestions:
                    error_msg += f"  • {suggestion}\n"
                error_msg += f"\nUse 'mim --list-services' to see all available services."
            else:
                error_msg += f"\n\nUse 'mim --list-services' to see all available services."
            
            raise click.BadParameter(error_msg)
    except Exception:
        # If validation fails due to network issues, allow it to proceed
        pass
    
    return value