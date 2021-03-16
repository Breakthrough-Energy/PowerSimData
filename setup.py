from setuptools import find_packages, setup

install_requires = [
    "numpy",
    "pandas",
    "paramiko",
    "scipy",
    "tqdm",
    "psycopg2",
    "requests",
]

setup(
    name="powersimdata",
    version="0.4",
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
        ]
    },
    zip_safe=False,
    install_requires=install_requires,
)
