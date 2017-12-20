from setuptools import setup

setup(
    name='cranio',
    packages=['cranio'],
    install_requires=['pandas', 'pyqtgraph', 'pyserial'],
    entry_points={
        'console_scripts': [],
    },
)