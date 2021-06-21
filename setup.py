from setuptools import find_packages, setup

install_requires = [
    "networkx",
    "numpy",
    "pandas",
    "paramiko",
    "scipy",
    "tqdm",
    "requests",
    "fsspec",
]

setup(
    name="powersimdata",
    version="0.4.3",
    description="Power Simulation Data",
    url="https://github.com/Breakthrough-Energy/powersimdata",
    author="Kaspar Mueller",
    author_email="kaspar@breakthroughenergy.org",
    packages=find_packages(),
    package_data={
        "powersimdata": [
            "network/*/data/*.csv",
            "design/investment/data/*.csv",
            "design/investment/data/*/*",
            "utility/templates/*.csv",
        ]
    },
    zip_safe=False,
    install_requires=install_requires,
)
