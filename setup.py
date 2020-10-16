from setuptools import find_packages, setup

install_requires = [
    "numpy",
    "pandas",
    "paramiko",
    "scipy",
    "tqdm",
    "psycopg2",
]

setup(
    name="powersimdata",
    version="0.3",
    description="Power Simulation Data",
    url="https://github.com/Breakthrough-Energy/powersimdata",
    author="Kaspar Mueller",
    author_email="kaspar.mueller@breakthroughenergy.org",
    packages=find_packages(),
    package_data={"powersimdata": ["network/*/data/*.csv"]},
    zip_safe=False,
    install_requires=install_requires,
)
