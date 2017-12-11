from setuptools import setup

setup(
    name='craniodistractor',
    packages=['craniodistractor.producer', 'craniodistractor.server', 'craniodistractor.core'],
    install_requires=['twisted', 'pyqtgraph', 'pandas'],
    entry_points={
        'console_scripts': [
            'echo_server = craniodistractor.server.echo_server:run_server'
        ],
    },
)