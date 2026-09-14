from setuptools import find_packages, setup

setup(
    name="sqlhawk",
    version="0.1.0",
    description="Multi-language SQL injection detection scanner for authorized security testing.",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "colorama>=0.4.6",
        "arabic-reshaper>=3.0.0",
        "python-bidi>=0.4.2",
    ],
    entry_points={
        "console_scripts": [
            "sqlhawk=sqlhawk.cli:main",
        ],
    },
    python_requires=">=3.10",
)
