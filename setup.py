from setuptools import setup

setup(
    name='craniodistractor',
    packages=['craniodistractor.producer', 'craniodistractor.server', 'craniodistractor.core'],
    install_requires=['twisted'],
    entry_points={
        'console_scripts': [
            'echo_server = craniodistractor.server.echo_server:run_server'
        ],
    },
)