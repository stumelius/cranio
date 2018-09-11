from pathlib import Path

DEFAULT_DATEFMT = '%Y-%m-%d %H:%M:%S'
DEFAULT_LOGGING_CONFIG_PATH = Path(__file__).parent.parent / 'logging.yml'
SQLITE_FILENAME = 'cranio.db'
# Seconds to include in plot. None for no filtering.
PLOT_N_SECONDS = 10
