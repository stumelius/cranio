from setuptools import setup

setup(
    name='craniodistractor',
    packages=['craniodistractor.producer', 'craniodistractor.server', 'craniodistractor.core'],
    entry_points={
        'console_scripts': [
            'echo_server = craniodistractor.server.echo_server:run_server',
            'QCP-004_report = scripts.standard_functionality_test_report_from_data:test_report_from_actuations'
        ],
    },
)