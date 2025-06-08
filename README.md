# AWS Service Profiles CLI (`mim`)

> A powerful CLI tool for exploring AWS service actions, resources, and IAM condition keys

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AWS Service Profiles CLI** (`mim`) is a command-line tool that helps AWS developers, DevOps engineers, and security professionals explore and understand AWS services in detail. It provides comprehensive information about AWS service actions, resources, ARN formats, and IAM condition keys - essential for building precise IAM policies and understanding AWS service capabilities.

## 🚀 Features

- **📋 Complete Service Catalog**: Browse all available AWS services
- **🔍 Action Discovery**: List all actions available for any AWS service  
- **🏗️ Resource Information**: View resources, ARN formats, and relationships
- **🔑 Context Key Analysis**: Comprehensive IAM condition key exploration
- **🌐 Global vs Service-Specific Keys**: Separate AWS global (`aws:`) from service-specific condition keys
- **📊 Multiple Output Formats**: Table, JSON, YAML, and text formats
- **🎯 Service Discovery**: Get detailed service information and usage examples
- **💡 Intelligent Error Handling**: Helpful suggestions for typos and invalid inputs
- **⚡ Performance Optimized**: Built-in caching for fast repeated queries

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/your-username/aws-service-profiles.git
cd aws-service-profiles

# Install in development mode
pip install -e .

# Verify installation
mim --help
```

### Dependencies

The tool automatically installs the following dependencies:
- `click` - Command-line interface framework
- `requests` - HTTP library for AWS API calls
- `rich` - Beautiful terminal output
- `tabulate` - Table formatting
- `pyyaml` - YAML output support

## 🎯 Quick Start

### Basic Usage

```bash
# List all AWS services
mim --list-services

# Get detailed information about a service
mim s3 info

# List all actions for a service
mim s3

# Get service-specific context keys
mim s3 --context-keys
```

## 📖 Usage Guide

### Service Discovery

```bash
# List all available AWS services
mim --list-services

# Get comprehensive service information
mim s3 info
mim sagemaker info
mim ec2 info
```

### Actions

```bash
# List all actions for a service
mim s3
mim ec2 --format json

# Get action count only
mim sagemaker --count

# Get details for a specific action
mim s3 --action GetObject
mim s3 GetObject  # Alternative syntax
```

### Resources

```bash
# List all resources for a service
mim s3 --resources

# Get resources for a specific action
mim s3 GetObject
mim ec2 DescribeInstances

# Get details for a specific resource
mim s3 --resource bucket
```

### Context Keys (IAM Condition Keys)

```bash
# All context keys for a service
mim s3 --context-keys

# Only AWS global context keys (aws:)
mim s3 --global-context-keys

# Only service-specific context keys (s3:, ec2:, etc.)
mim s3 --service-context-keys

# AWS-wide context key analysis
mim --list-all-context-keys
mim --list-global-context-keys
mim --list-service-context-keys
```

### Output Formats

```bash
# Table format (default)
mim s3 --context-keys

# JSON format
mim s3 --context-keys --format json

# YAML format
mim s3 --context-keys --format yaml

# Simple text format
mim s3 --context-keys --format text

# Count only
mim s3 --context-keys --count
```

## 💡 Examples

### 1. Exploring S3 Service

```bash
# Get S3 service overview
mim s3 info
```

Output:
```
Service: S3

📊 Available Data:
  • Actions: 163
  • Resources: 12
  • Context Keys: 50 (AWS Global: 3, Service-Specific: 47)

🔍 Sample Actions:
  • AbortMultipartUpload
  • CreateBucket
  • GetObject
  • PutObject
  • DeleteObject
  ... and 158 more

💡 Common Usage Examples:
  mim s3                        # List all actions
  mim s3 --context-keys         # Show all context keys
  mim s3 GetObject              # Get resources for GetObject
```

### 2. Building IAM Policies

```bash
# Get all condition keys for S3
mim s3 --context-keys --format json > s3-condition-keys.json

# Get AWS global condition keys
mim --list-global-context-keys

# Get resources for a specific action
mim s3 GetObject --format yaml
```

### 3. Service Comparison

```bash
# Compare context key counts across services
mim s3 --context-keys --count
mim ec2 --context-keys --count
mim sagemaker --context-keys --count

# Get all service-specific keys across AWS
mim --list-service-context-keys --format json > all-service-keys.json
```

### 4. Resource Discovery

```bash
# List all S3 resources with ARN formats
mim s3 --resources

# Get specific resource details
mim s3 --resource bucket
mim ec2 --resource instance
```

### 5. Querying Multiple Service:Action Pairs

You can query multiple service:action pairs in a single command using comma-separated values:

```bash
# Query multiple service:action pairs
mim -sa s3:GetObject,s3:PutBucketPolicy,sagemaker:CreateTrainingJob

# With different output formats
mim -sa s3:GetObject,s3:PutObject --format json
mim -sa ec2:RunInstances,s3:CreateBucket --format yaml
mim -sa sagemaker:CreateTrainingJob,ec2:DescribeInstances --format text

# Get metadata for specific actions across different services
mim -sa s3:GetObject,s3:PutObject,ec2:RunInstances,sagemaker:CreateTrainingJob --format json

# Using wildcards (note: always quote the argument to prevent shell expansion)
mim -sa "s3:Get*" --format json
mim -sa "sagemaker:Create*" --format text
mim -sa "s3:Get*,s3:Put*,sagemaker:Create*" --format yaml
```

> **Note**: When using wildcards (`*` or `?`), always quote the `-sa` argument to prevent the shell from expanding the wildcards. For example, use `mim -sa "s3:Get*"` instead of `mim -sa s3:Get*`.

The tool will process all specified service:action pairs and return the combined results in your chosen format.

## 🔧 Advanced Usage

### Service Validation and Suggestions

The tool provides intelligent error handling:

```bash
# Typo in service name
mim s33
# Output: Did you mean one of these?
#   • s3

# Partial service name
mim sage
# Output: Did you mean one of these?
#   • sagemaker
```

### Caching and Performance

The tool uses intelligent caching to improve performance:
- Service lists are cached for the session
- Service metadata is cached (up to 128 services)
- AWS-wide context key analysis is cached
- Subsequent queries are significantly faster

### Working with Large Datasets

```bash
# Get counts for quick overview
mim --list-all-context-keys --count
# Output: Total unique context keys across all AWS services: 1,184

# Use JSON format for programmatic processing
mim --list-service-context-keys --format json | jq '.ec2 | length'

# Filter specific services
mim --list-services | grep -i compute
```

## 🛠️ Development

### Project Structure

```
aws-service-profiles/
├── aws_service_profiles/       # Main package
│   ├── __init__.py
│   ├── cli.py                  # CLI interface
│   ├── aws_client.py           # AWS API client
│   ├── formatters.py           # Output formatting
│   ├── models.py               # Data models
│   └── service_helper.py       # Service discovery
├── setup.py                    # Package configuration
├── requirements.txt            # Dependencies
├── README.md                   # This file
└── .gitignore                  # Git ignore rules
```

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests (when available)
pytest

# Run linting
flake8 aws_service_profiles/
```

## 📊 Data Source

This tool fetches data from AWS's official service reference API:
- **Source**: `https://servicereference.us-east-1.amazonaws.com/`
- **Data**: Official AWS service metadata including actions, resources, and condition keys
- **Updates**: Data is fetched in real-time, ensuring up-to-date information


## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


---

**Happy AWS exploring!** 🚀☁️