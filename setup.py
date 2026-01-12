"""
SolidWaste-Agent 安装配置
"""
from setuptools import setup, find_packages
import os

# 读取README文件
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

# 读取requirements.txt
def read_requirements():
    with open('requirements.txt', encoding='utf-8') as f:
        return [line.strip() for line in f 
                if line.strip() and not line.startswith('#')]

setup(
    name="solidwaste-agent",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="面向固体废物领域的多智能体协作框架",
    long_description=read_file('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/solidwaste-agent",
    packages=find_packages(exclude=['tests', 'tests.*', 'examples', 'docs']),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.1.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.4.0',
            'isort>=5.12.0',
        ],
        'storage': [
            'redis>=4.5.0',
            'pymongo>=4.3.0',
        ],
        'vectors': [
            'chromadb>=0.4.0',
            'sentence-transformers>=2.2.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'swagent=swagent.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        'swagent': [
            'prompts/templates/*.txt',
            'domain/data/*.json',
        ],
    },
    keywords=[
        'agent',
        'multi-agent',
        'llm',
        'solid-waste',
        'environmental',
        'sustainability',
        'ai',
        'automation',
    ],
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/solidwaste-agent/issues',
        'Source': 'https://github.com/yourusername/solidwaste-agent',
        'Documentation': 'https://github.com/yourusername/solidwaste-agent/docs',
    },
)
