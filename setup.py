from setuptools import setup

setup(
    name='cranio',
    packages=['cranio', 'cranio.app'],
    install_requires=['pandas', 'pyserial', 'attrs', 'pyqt5', 'pyqtgraph'],
    entry_points={
        'console_scripts': [],
    },
)