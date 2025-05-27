"""Setup script for AWS Service Profiles CLI."""

from setuptools import setup, find_packages

# Read requirements from requirements.txt
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read the README file for long description
def read_readme():
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "AWS Service Profiles CLI - A tool for exploring AWS service metadata."

setup(
    name="aws-service-profiles",
    version="0.1.0",
    author="AWS Service Profiles",
    author_email="",
    description="A CLI tool for exploring AWS service actions, resources, and context keys",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/aws-service-profiles",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "mim=aws_service_profiles.cli:cli",
        ],
    },
    keywords="aws iam policies context-keys service-profiles cli",
    project_urls={
        "Bug Reports": "https://github.com/your-username/aws-service-profiles/issues",
        "Source": "https://github.com/your-username/aws-service-profiles",
    },
)