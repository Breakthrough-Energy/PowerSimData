from setuptools import setup, find_packages

install_requires = [
    "geopy",
    "jsonpickle",
    "numpy",
    "pandas",
    "paramiko",
    "scipy",
    "tqdm",
]

setup(
    name="powersimdata",
    version="0.3",
    description="Power Simulation Data",
    url="https://github.com/intvenlab/powersimdata",
    author="Kaspar Mueller",
    author_email="kmueller@intven.com",
    packages=find_packages(),
    package_data={"powersimdata": ["input/data/*/*"]},
    zip_safe=False,
    install_requires=install_requires,
)
