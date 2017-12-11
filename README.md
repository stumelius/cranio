# Craniodistractor

Craniodistractor is a Python library used for force measurements, data analysis and visualization in posterior calvarial vault osteodistraction (PCVO). 
The methods implemented in this library are based on a whitepaper by Ritvanen et al. (2017).


## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a target machine.

### Prerequisites

* OS: tested on Windows 10
* Python 3.x

### Installing

The source code is currently hosted on GitHub at https://github.com/smomni/craniodistractor

You can use git clone and pip to install from sources:

```
git clone https://github.com/smomni/craniodistractor
cd craniodistractor
pip install -e .
```

The package will be available in Python package index (PyPI) in the future.

## Running the tests

The tests can be run using pytest as the test runner:

```
pytest tests
```

## Deployment

Software deployment by installation from sources on a target machine. 
Alternatively, you can freeze the source in an executable using [PyInstaller](http://www.pyinstaller.org/) and running the executable on a target machine.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/smomni/craniodistractor/tags). 

## Authors

* **Simo Tumelius** - *Initial work* - [smomni](https://github.com/smomni)

See also the list of [contributors](https://github.com/smomni/craniodistractor/contributors) who participated in this project.

## License

This project is licensed under the GNU GPLv3 license - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Ritvanen, A., et al. "Force measurements during posterior calvarial vault osteodistraction: A novel measurement method." Journal of Cranio-Maxillofacial Surgery 45.6 (2017): 981-989.

