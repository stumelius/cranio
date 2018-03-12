from setuptools import setup

setup(
    name='cranio',
    packages=['cranio', 'cranio.app'],
    install_requires=['pandas', 'pyserial', 'attrs', 'pyqt5', 'pyqtgraph'],
    extras_require={
        'dev': [],
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [],
    },
)