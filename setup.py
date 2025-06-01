from setuptools import setup, find_packages

setup(
    name="expense-tracker-mcp",
    version="0.1.0",
    packages=find_packages(include=["app", "app.*"]),
    install_requires=[
        "fastapi",
        "pydantic",
        "supabase",
        "httpx",
    ],
    python_requires=">=3.10",
    package_data={
        "app": ["py.typed"],
    },
) 