from setuptools import setup, find_packages

setup(
    name="trading_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "dash",
        "plotly",
        "pandas",
        "numpy",
        "ccxt",
        "tensorflow",
        "scikit-learn",
        "python-dotenv",
        "aiohttp",
        "asyncio"
    ],
    author="Trading Bot Team",
    description="AI Smart Trading Bot for Cryptocurrency Trading",
    python_requires=">=3.8",
)
