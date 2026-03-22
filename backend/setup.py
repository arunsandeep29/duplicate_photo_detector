from setuptools import setup, find_packages

setup(
    name="duplicate-photos",
    version="0.1.0",
    description="Duplicate JPEG finder and organizer",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/duplicate-photos",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "Flask==2.3.0",
        "Flask-CORS==4.0.0",
        "Pillow==10.0.0",
        "python-dotenv==1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.0",
            "pytest-cov==4.1.0",
            "black==23.9.0",
            "flake8==6.1.0",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
