from setuptools import find_packages, setup


setup(
    name="grb-sensitivity",
    version="0.1.0",
    description="Educational GRB detector sensitivity command-line tool",
    packages=find_packages(),
    install_requires=["numpy", "pandas", "matplotlib", "pyyaml"],
    extras_require={"test": ["pytest"]},
    entry_points={"console_scripts": ["grb-sens=grb_sensitivity.cli:main"]},
    python_requires=">=3.9",
)
