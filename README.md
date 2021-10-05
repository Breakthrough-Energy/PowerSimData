![logo](https://raw.githubusercontent.com/Breakthrough-Energy/docs/master/source/_static/img/BE_Sciences_RGB_Horizontal_Color.svg)

[![PyPI](https://img.shields.io/pypi/v/powersimdata?color=purple)](https://pypi.org/project/powersimdata/)
[![codecov](https://codecov.io/gh/Breakthrough-Energy/PowerSimData/branch/develop/graph/badge.svg?token=5A20TCV5XL)](https://codecov.io/gh/Breakthrough-Energy/PowerSimData)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Tests](https://github.com/Breakthrough-Energy/PowerSimData/workflows/Pytest/badge.svg)
[![Documentation](https://github.com/Breakthrough-Energy/docs/actions/workflows/publish.yml/badge.svg)](https://breakthrough-energy.github.io/docs/)
![GitHub contributors](https://img.shields.io/github/contributors/Breakthrough-Energy/PowerSimData?logo=GitHub)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/Breakthrough-Energy/PowerSimData?logo=GitHub)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/Breakthrough-Energy/PowerSimData/develop?logo=GitHub)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Breakthrough-Energy/PowerSimData?logo=GitHub)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code of Conduct](https://img.shields.io/badge/code%20of-conduct-ff69b4.svg?style=flat)](https://breakthrough-energy.github.io/docs/communication/code_of_conduct.html)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4538590.svg)](https://doi.org/10.5281/zenodo.4538590)


# PowerSimData
**PowerSimData** is part of a Python software ecosystem developed by [Breakthrough
Energy Sciences](https://science.breakthroughenergy.org/) to carry out power flow study
in the U.S. electrical grid.


## Main Features
Here are a few things that **PowerSimData** can do:
* Provide a flexible modeling tool to create complex scenarios
* Perform investment cost studies
* Run power flow study using interface to external simulation engine
* Manage data throughout the lifecycle of a simulation

A detailed tutorial can be found on our [docs].


## Where to get it
* Clone or Fork the source code on [GitHub](https://github.com/Breakthrough-Energy/PowerSimData)
* Get latest release from PyPi: `pip install powersimdata`


## Dependencies
**PowerSimData** relies on several Python packages all available on
[PyPi](https://pypi.org/). The list can be found in the ***requirements.txt*** or
***Pipfile*** files both located at the root of this package.


## Installation
To take full advantage of our software, we recommend that you clone/fork
**[plug](https://github.com/Breakthrough-Energy/plug)** and follow the information
therein to get our containerized framework up and running. A client/server installation
is also possible and outlined in our [Installation
Guide](https://breakthrough-energy.github.io/docs/user/installation_guide.html). Either
way, you will need a powerful solver, e.g. Gurobi, to run complex scenarios.

Only a limited set of features are available when solely installing **PowerSimData**. If you choose this option, we recommend that you use `pipenv`:
```sh
pipenv sync
pipenv shell
```
since the dependencies will be installed in an isolated environment. It is of course
possible to install the dependencies using the requirements file:
```sh
pip install -r requirements.txt
```


## License
[MIT](LICENSE)


## Documentation
[Code documentation][docstrings] in form of Python docstrings along with an overview of
the [package][docs] are available on our [website][website].


## Communication Channels
[Sign up](https://science.breakthroughenergy.org/#get-updates) to our email list and
our Slack workspace to get in touch with us.


## Contributing
All contributions (bug report, documentation, feature development, etc.) are welcome. An
overview on how to contribute to this project can be found in our [Contribution
Guide](https://breakthrough-energy.github.io/docs/dev/contribution_guide.html).



[docs]: https://breakthrough-energy.github.io/docs/powersimdata/index.html
[docstrings]: https://breakthrough-energy.github.io/docs/powersimdata.html
[website]: https://breakthrough-energy.github.io/docs/
