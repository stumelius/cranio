from setuptools import setup
from cranio import __version__

setup(
    name='cranio',
    version=__version__,
    packages=['cranio', 'cranio.app'],
    install_requires=['pandas', 'pyserial', 'attrs', 'pyqtgraph', 'sqlalchemy'],
    extras_require={
        'dev': [],
        'lint': ['black'],
        'test': ['pytest', 'pytest-cov', 'pytest-helpers-namespace'],
        'docs': ['sphinx', 'sphinx-autodoc-typehints', 'm2r'],
    },
    scripts=['scripts/sqlite-to-csv.py'],
    entry_points={'console_scripts': ['cranio = run:main']},
)
