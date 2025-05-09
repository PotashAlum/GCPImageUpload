# setup.py
from setuptools import setup, find_packages

setup(
    name="team-image-management-api",
    version="1.0.0",
    description="A secure API for team-based image management with hierarchical access control",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.105.0",
        "uvicorn>=0.24.0",
        "motor>=3.6.0",
        "pydantic>=2.4.2",
        "google-cloud-storage>=2.12.0",
        "python-multipart>=0.0.6",
        "aiofiles>=23.2.1",
        "pillow>=10.0.0",
        "python-jose>=3.3.0",
        "passlib>=1.7.4",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
            "pytest-mock>=3.10.0",
            "mongomock>=4.1.2",
        ]
    },
    python_requires=">=3.11",
)