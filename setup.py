from setuptools import setup, find_packages

setup(
    name="orbitalis",
    version="0.1.0",
    description="Satellite conjunction analysis and orbit visualization tool",
    author="Shashank Pathak",
    author_email="your@email.com",
    packages=find_packages(),  # auto-discovers packages like orbitalis/
    include_package_data=True,
    install_requires=[
        "pandas",
        "numpy",
        "scipy",
        "streamlit",
        "sgp4",
        # add more if needed
    ],
    entry_points={
        "console_scripts": [
            "orbitalis-run=orbitalis.run_pipeline:main",  # Create this
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.8',
)
