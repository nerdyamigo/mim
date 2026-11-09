# AWS Service Profiles CLI (`mim`)

> A powerful CLI tool for exploring AWS service IAM actions, API operations, SDK mappings, resources, and condition keys

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AWS Service Profiles CLI** (`mim`) is a command-line tool that helps AWS developers, DevOps engineers, and security professionals explore and understand AWS services in detail. It provides comprehensive information about AWS service IAM actions, access levels, control/data plane classifications, API operations & SDK mappings, resources, ARN formats, and IAM condition keys.

## 🚀 Features

- **📋 Complete Service Catalog**: Browse all 450+ AWS services with display names (`serviceName`) and upstream modification dates (`modified`)
- **🔍 Action Discovery & Filtering**: List actions with `Access Level` (`Read`, `Write`, `List`, `Tagging`, `Permissions management`) and `Plane` (`Control Plane`, `Data Plane`) filtering
- **⚙️ API Operations & SDK Mappings**: Inspect service API `Operations`, their `AuthorizedActions`, and `SDK` client methods (`Boto3`, `AWS SDK for Java v2`, etc.)
- **🛡️ IAM Feature Support (`SupportedBy`)**: View whether actions support `IAM Access Analyzer Policy Generation` and `IAM Action Last Accessed`
- **🏗️ Resource Information**: View resources, ARN formats, and both resource-level and action-scoped condition keys
- **🔑 Context Key Analysis**: Separate AWS global (`aws:`) from service-specific condition keys with data types (`ARN`, `ArrayOfString`, `String`, etc.)
- **🔄 Metadata Update & Local Disk Cache**: Persistent disk cache (`~/.cache/mim`) with `mim --update` (`mim update`), `--clear-cache`, and `--check-schema`
- **📊 Multiple Output Formats**: Table, JSON, YAML, and text formats with case-insensitive lookups and substring search (`-s` / `--search`)

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/nerdyamigo/mim.git
cd mim

# Install in development mode (with test dependencies)
pip install -e ".[dev]"

# Verify installation
mim --help
```

## 🎯 Quick Start

```bash
# Sync / update local AWS metadata cache and see newly added or modified services
mim --update

# List all AWS services (or filter by keyword)
mim --list-services
mim --list-services --search bedrock

# Get detailed overview of a service (actions breakdown, planes, operations, resources, keys)
mim s3 info

# List all actions for a service (with Access Level and Plane columns)
mim s3

# Filter actions by Access Level and Plane
mim s3 --access-level Write --plane data

# Inspect a specific action (case-insensitive or shorthand syntax)
mim s3 --action GetObject
mim s3:GetObject

# Explore API Operations and SDK method mappings
mim s3 --operations
mim s3 --operation CopyObject
```

## 📖 Usage Guide

### Metadata Updates & Schema Monitoring

```bash
# Refresh the local metadata index and cached services from AWS
mim --update
mim update

# Refresh and pre-cache a specific service
mim s3 --update

# Clear the local metadata cache (~/.cache/mim)
mim --clear-cache

# Check upstream AWS Service Reference API for schema changes against baseline
mim --check-schema
```

### Service Discovery

```bash
# List all available AWS services
mim --list-services

# Search services by code or display name
mim --list-services -s lambda

# Get comprehensive service summary
mim s3 info
mim ec2 info
```

### Actions & Filtering

```bash
# List all actions for a service
mim s3

# Filter actions by access level (Read, Write, List, Tagging, Permissions)
mim s3 --access-level Write
mim s3 --access-level Permissions

# Filter actions by plane (control or data)
mim s3 --plane data
mim s3 --plane control

# Substring search across actions
mim s3 -s Multipart

# Wildcard matching
mim s3 "Get*"
mim s3 "Put*" --format json

# Get full details for a specific action (annotations, SupportedBy, operations, resources, keys)
mim s3 --action GetObject
mim s3 GetObject
mim s3:GetObject
```

### API Operations & SDK Mappings

```bash
# List all API Operations for a service
mim s3 --operations
mim s3 --operations -s Multipart

# Get details for a specific API Operation (Authorized IAM Actions & SDK methods)
mim s3 --operation AbortMultipartUpload
mim ec2 --operation RunInstances
```

### Resources

```bash
# List all resources for a service
mim s3 --resources

# Get details for a specific resource (case-insensitive)
mim s3 --resource bucket
mim ec2 --resource instance
```

### Context Keys (IAM Condition Keys)

```bash
# All context keys for a service
mim s3 --context-keys
mim s3 --context-keys -s Tag

# Only AWS global context keys (aws:)
mim s3 --global-context-keys

# Only service-specific context keys (s3:, ec2:, etc.)
mim s3 --service-context-keys

# AWS-wide context key analysis
mim --list-all-context-keys
mim --list-global-context-keys
mim --list-service-context-keys
```

### Querying Multiple Service:Action Pairs (`-sa`)

```bash
# Query multiple service:action pairs in parallel
mim -sa s3:GetObject,s3:PutBucketPolicy,ec2:RunInstances

# With wildcards and output formats
mim -sa "s3:Get*,ec2:Describe*" --format json
mim -sa s3:GetObject,s3:PutObject --format yaml
```

## 🛠️ Development & Testing

```bash
# Run the test suite
pytest -v

# Run the schema monitor directly
python scripts/schema_monitor.py --sample-size 15
python scripts/schema_monitor.py --create-baseline --sample-size 15
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
