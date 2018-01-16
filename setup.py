from setuptools import setup

setup(
    name='cranio',
    packages=['cranio', 'cranio.app'],
    install_requires=['pandas', 'pyqtgraph', 'pyserial', 'attrs'],
    entry_points={
        'console_scripts': [],
    },
)