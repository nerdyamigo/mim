"""Setup script for AWS Service Profiles CLI."""

from setuptools import setup, find_packages


def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "AWS Service Profiles CLI - A tool for exploring AWS service metadata."


setup(
    name="aws-service-profiles",
    version="0.2.0",
    author="AWS Service Profiles",
    author_email="",
    description="A CLI tool for exploring AWS service actions, API operations, resources, and IAM condition keys",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/nerdyamigo/mim",
    packages=find_packages(exclude=["tests*"]),
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
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mim=aws_service_profiles.cli:cli",
        ],
    },
    keywords="aws iam policies context-keys operations service-profiles cli",
    project_urls={
        "Bug Reports": "https://github.com/nerdyamigo/mim/issues",
        "Source": "https://github.com/nerdyamigo/mim",
    },
)
