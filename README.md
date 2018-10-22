[![Build Status](https://travis-ci.org/smomni/cranio.svg?branch=master)](https://travis-ci.org/smomni/cranio)
[![Coverage Status](https://codecov.io/gh/smomni/cranio/branch/master/graph/badge.svg)](https://codecov.io/gh/smomni/cranio)
[![Documentation Status](https://readthedocs.org/projects/cranio/badge/?version=latest)](https://cranio.readthedocs.io/en/latest/?badge=latest)
[![Waffle.io - Columns and their card count](https://badge.waffle.io/smomni/cranio.svg?columns=all)](https://waffle.io/smomni/cranio)
[![Maintainability](https://api.codeclimate.com/v1/badges/c14e1d3a9202d71024a3/maintainability)](https://codeclimate.com/github/smomni/cranio/maintainability)

# Cranio

Cranio is a Python library used for force measurements, data analysis and visualization in 
posterior calvarial vault osteodistraction (PCVO). 
The methods implemented in this library are based on a whitepaper by Ritvanen et al. (2017).


## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Hardware

The craniodistractor measurements are taken with a [Imada HTG2-4](https://imada.com/products/htg2-digital-torque-gauge/) 
digital torque gauge. The gauge features a remote torque sensor with a Jacob's chuck.

![Imada HTG2-4 digital torque gauge with Jacob's chuck (left) and USB serial interface (right).](docs/imada.jpg)

### Prerequisites

* OS: Windows, Linux, OS X (tested on Windows 10 and Linux)
* Python 3.x

### Installing

The source code is currently hosted on GitHub at https://github.com/smomni/cranio.

You can use git clone and pip to install from sources:

```bash
git clone https://github.com/smomni/cranio
cd cranio
pip install -e .
```

To start the measurement software:

```bash
python -m run
```

## Running the tests

The tests can be run using pytest as the test runner:

```bash
pytest tests
```

## Workflow

* File issues for features. They can be small or big, as long as they are solveable. You should be able to tell when something is done from reading the issue. Too open ended and it cannot be closed.

* Develop created issues

* Commits should touch one thing, preferably, with a label that matches the code. For example, a change that reads "reformat foo" shouldn't add new features, etc.

* Open a pull request (PR) for review from the branch to master

* Try to keep the commits on a PR branch below a dozen

* Keep the PR open for 24 hours to give people the chance to comment and look at it

* Review the changes

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/smomni/cranio/tags). 

## Authors

* **Simo Tumelius** - *Initial work* - [smomni](https://github.com/smomni)

See also the list of [contributors](https://github.com/smomni/cranio/contributors) who participated in this project.

## License

This project is licensed under the GNU GPLv3 license - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Ritvanen, A., et al. "Force measurements during posterior calvarial vault osteodistraction: A novel measurement method." Journal of Cranio-Maxillofacial Surgery 45.6 (2017): 981-989.

