#!/usr/bin/env python3
"""
AWS Service Reference API Schema Monitor

This script monitors the AWS Service Reference API for schema changes,
including new fields, field types, and structural modifications.
"""

import json
import requests
import hashlib
from typing import Dict, List, Set, Any, Tuple
from datetime import datetime
from pathlib import Path
import argparse
import sys


class SchemaMonitor:
    """Monitor AWS Service Reference API for schema changes."""
    
    def __init__(self):
        self.base_url = 'https://servicereference.us-east-1.amazonaws.com/'
        self.schema_dir = Path(__file__).parent.parent / 'schemas'
        self.schema_dir.mkdir(exist_ok=True)
        
    def get_services_list(self) -> List[Dict[str, str]]:
        """Get list of all AWS services."""
        try:
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching services list: {e}", file=sys.stderr)
            return []
    
    def get_service_metadata(self, service_url: str) -> Dict[str, Any]:
        """Get metadata for a specific service."""
        try:
            response = requests.get(service_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching metadata from {service_url}: {e}", file=sys.stderr)
            return {}
    
    def extract_schema_structure(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the schema structure from service metadata."""
        schema = {
            'top_level_fields': set(),
            'action_fields': set(),
            'resource_fields': set(),
            'condition_key_fields': set(),
            'data_types': set(),
            'field_combinations': set()
        }
        
        # Top-level fields
        schema['top_level_fields'] = set(metadata.keys())
        
        # Action fields
        actions = metadata.get('Actions', [])
        if actions and isinstance(actions, list):
            for action in actions:
                if isinstance(action, dict):
                    schema['action_fields'].update(action.keys())
                    # Track field combinations in actions
                    combo = tuple(sorted(action.keys()))
                    schema['field_combinations'].add(('action', combo))
        
        # Resource fields
        resources = metadata.get('Resources', [])
        if isinstance(resources, list):
            for resource in resources:
                if isinstance(resource, dict):
                    schema['resource_fields'].update(resource.keys())
                    # Track field combinations in resources
                    combo = tuple(sorted(resource.keys()))
                    schema['field_combinations'].add(('resource', combo))
        elif isinstance(resources, dict):
            for resource_data in resources.values():
                if isinstance(resource_data, dict):
                    schema['resource_fields'].update(resource_data.keys())
                    combo = tuple(sorted(resource_data.keys()))
                    schema['field_combinations'].add(('resource', combo))
        
        # Condition key fields
        condition_keys = metadata.get('ConditionKeys', [])
        if condition_keys and isinstance(condition_keys, list):
            for key in condition_keys:
                if isinstance(key, dict):
                    schema['condition_key_fields'].update(key.keys())
                    # Track data types
                    types = key.get('Types', [])
                    if isinstance(types, list):
                        schema['data_types'].update(types)
                    # Track field combinations in condition keys
                    combo = tuple(sorted(key.keys()))
                    schema['field_combinations'].add(('condition_key', combo))
        
        # Convert sets to sorted lists for JSON serialization
        for key in schema:
            if key != 'field_combinations':
                schema[key] = sorted(list(schema[key]))
            else:
                # Sort field combinations by context then fields
                combinations = [
                    {'context': context, 'fields': sorted(list(fields))} 
                    for context, fields in schema[key]
                ]
                schema[key] = sorted(combinations, key=lambda x: (x['context'], tuple(x['fields'])))
        
        return schema
    
    def analyze_services_sample(self, sample_size: int = 10) -> Dict[str, Any]:
        """Analyze a sample of services to understand overall schema."""
        services = self.get_services_list()
        if not services:
            return {}
        
        # Sample services for analysis
        import random
        sample_services = random.sample(services, min(sample_size, len(services)))
        
        global_schema = {
            'analyzed_services': [],
            'top_level_fields': set(),
            'action_fields': set(),
            'resource_fields': set(),
            'condition_key_fields': set(),
            'data_types': set(),
            'field_combinations': set(),
            'service_variations': {}
        }
        
        for service in sample_services:
            service_name = service['service']
            service_url = service['url']
            
            print(f"Analyzing {service_name}...")
            
            metadata = self.get_service_metadata(service_url)
            if not metadata:
                continue
            
            schema = self.extract_schema_structure(metadata)
            global_schema['analyzed_services'].append(service_name)
            
            # Aggregate fields
            for field_type in ['top_level_fields', 'action_fields', 'resource_fields', 'condition_key_fields', 'data_types']:
                global_schema[field_type].update(schema[field_type])
            
            # Store service-specific variations
            global_schema['service_variations'][service_name] = schema
        
        # Convert sets to lists for JSON serialization
        for key in ['top_level_fields', 'action_fields', 'resource_fields', 'condition_key_fields', 'data_types']:
            global_schema[key] = sorted(list(global_schema[key]))
        
        # Handle field_combinations set
        if 'field_combinations' in global_schema and isinstance(global_schema['field_combinations'], set):
            combinations = [
                {'context': context, 'fields': sorted(list(fields))} 
                for context, fields in global_schema['field_combinations']
            ]
            global_schema['field_combinations'] = sorted(combinations, key=lambda x: (x['context'], tuple(x['fields'])))
        
        return global_schema
    
    def save_baseline_schema(self, schema: Dict[str, Any], filename: str = 'baseline_schema.json'):
        """Save the baseline schema to file."""
        schema_file = self.schema_dir / filename
        schema['timestamp'] = datetime.utcnow().isoformat()
        schema['schema_hash'] = self.calculate_schema_hash(schema)
        
        with open(schema_file, 'w') as f:
            json.dump(schema, indent=2, fp=f)
        
        print(f"Baseline schema saved to {schema_file}")
        return schema_file
    
    def load_baseline_schema(self, filename: str = 'baseline_schema.json') -> Dict[str, Any]:
        """Load the baseline schema from file."""
        schema_file = self.schema_dir / filename
        if not schema_file.exists():
            return {}
        
        with open(schema_file, 'r') as f:
            return json.load(f)
    
    def calculate_schema_hash(self, schema: Dict[str, Any]) -> str:
        """Calculate a hash of the schema structure for change detection."""
        # Create a deterministic representation of the schema
        schema_copy = dict(schema)
        # Remove timestamp and hash fields for hash calculation
        schema_copy.pop('timestamp', None)
        schema_copy.pop('schema_hash', None)
        
        schema_str = json.dumps(schema_copy, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()
    
    def compare_schemas(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two schemas and return differences."""
        changes = {
            'has_changes': False,
            'new_fields': {},
            'removed_fields': {},
            'new_data_types': [],
            'removed_data_types': [],
            'new_field_combinations': [],
            'removed_field_combinations': []
        }
        
        # Compare field sets
        for field_type in ['top_level_fields', 'action_fields', 'resource_fields', 'condition_key_fields']:
            old_fields = set(old_schema.get(field_type, []))
            new_fields = set(new_schema.get(field_type, []))
            
            added = new_fields - old_fields
            removed = old_fields - new_fields
            
            if added:
                changes['new_fields'][field_type] = sorted(list(added))
                changes['has_changes'] = True
            
            if removed:
                changes['removed_fields'][field_type] = sorted(list(removed))
                changes['has_changes'] = True
        
        # Compare data types
        old_types = set(old_schema.get('data_types', []))
        new_types = set(new_schema.get('data_types', []))
        
        added_types = new_types - old_types
        removed_types = old_types - new_types
        
        if added_types:
            changes['new_data_types'] = sorted(list(added_types))
            changes['has_changes'] = True
        
        if removed_types:
            changes['removed_data_types'] = sorted(list(removed_types))
            changes['has_changes'] = True
        
        return changes
    
    def monitor_changes(self) -> Dict[str, Any]:
        """Monitor for changes since last baseline."""
        baseline = self.load_baseline_schema()
        if not baseline:
            print("No baseline schema found. Creating baseline...")
            current_schema = self.analyze_services_sample()
            self.save_baseline_schema(current_schema)
            return {'status': 'baseline_created', 'schema': current_schema}
        
        print("Analyzing current schema...")
        current_schema = self.analyze_services_sample()
        
        print("Comparing with baseline...")
        changes = self.compare_schemas(baseline, current_schema)
        
        if changes['has_changes']:
            # Save new schema with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            self.save_baseline_schema(current_schema, f'schema_{timestamp}.json')
            
            # Update baseline
            self.save_baseline_schema(current_schema)
        
        return {
            'status': 'analysis_complete',
            'changes': changes,
            'current_schema': current_schema,
            'baseline_timestamp': baseline.get('timestamp'),
            'current_timestamp': current_schema.get('timestamp')
        }


def format_changes_report(changes: Dict[str, Any]) -> str:
    """Format changes into a readable report."""
    if not changes.get('has_changes', False):
        return "✅ No schema changes detected."
    
    report = ["🔍 AWS Service Reference API Schema Changes Detected!", ""]
    
    # New fields
    if changes.get('new_fields'):
        report.append("🆕 **New Fields Detected:**")
        for field_type, fields in changes['new_fields'].items():
            report.append(f"  • {field_type}: {', '.join(fields)}")
        report.append("")
    
    # Removed fields
    if changes.get('removed_fields'):
        report.append("🗑️ **Removed Fields:**")
        for field_type, fields in changes['removed_fields'].items():
            report.append(f"  • {field_type}: {', '.join(fields)}")
        report.append("")
    
    # New data types
    if changes.get('new_data_types'):
        report.append(f"📊 **New Data Types:** {', '.join(changes['new_data_types'])}")
        report.append("")
    
    # Removed data types
    if changes.get('removed_data_types'):
        report.append(f"📉 **Removed Data Types:** {', '.join(changes['removed_data_types'])}")
        report.append("")
    
    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='Monitor AWS Service Reference API for schema changes')
    parser.add_argument('--create-baseline', action='store_true', 
                       help='Create a new baseline schema')
    parser.add_argument('--sample-size', type=int, default=10,
                       help='Number of services to sample for analysis (default: 10)')
    parser.add_argument('--output-format', choices=['text', 'json'], default='text',
                       help='Output format for results')
    
    args = parser.parse_args()
    
    monitor = SchemaMonitor()
    
    if args.create_baseline:
        print("Creating new baseline schema...")
        schema = monitor.analyze_services_sample(args.sample_size)
        monitor.save_baseline_schema(schema)
        print("✅ Baseline schema created successfully!")
        return
    
    # Monitor for changes
    result = monitor.monitor_changes()
    
    if args.output_format == 'json':
        print(json.dumps(result, indent=2))
    else:
        if result['status'] == 'baseline_created':
            print("✅ Baseline schema created successfully!")
        else:
            changes_report = format_changes_report(result['changes'])
            print(changes_report)
            
            # Exit with code 1 if changes detected (for CI/CD)
            if result['changes'].get('has_changes', False):
                sys.exit(1)


if __name__ == '__main__':
    main()