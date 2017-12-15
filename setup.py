from setuptools import setup

setup(
    name='craniodistractor',
    packages=['craniodistractor'],
    install_requires=['pandas', 'pyqtgraph', 'pyserial'],
    entry_points={
        'console_scripts': [],
    },
)