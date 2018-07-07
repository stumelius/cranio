from setuptools import setup
from cranio import __version__

setup(
    name='cranio',
    version=__version__,
    packages=['cranio', 'cranio.app'],
    install_requires=['pandas', 'pyserial', 'attrs', 'pyqtgraph'],
    extras_require={
        'dev': [],
        'test': ['pytest', 'pytest-cov'],
        'docs': ['sphinx', 'sphinx-autodoc-typehints']
    },
    entry_points={
        'console_scripts': [],
    },
)