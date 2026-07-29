from setuptools import setup, find_packages

setup(
    name="cloakapi",
    version="1.0.0",
    author="CloakAPI Team",
    description="حوّل كودك إلى API محمي ومستضاف فورياً",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28.0",
        "cryptography>=41.0.0",
    ],
    entry_points={
        "console_scripts": [
            "cloakapi=cloak_sdk.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
