from setuptools import setup

setup(
    name='cranio',
    packages=['cranio', 'cranio.app'],
    install_requires=['pandas', 'pyqtgraph', 'pyserial'],
    entry_points={
        'console_scripts': [],
    },
)