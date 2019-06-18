#!/usr/bin/env python
import argparse
import pandas as pd
from pathlib import Path
from cranio.model import Database, session_scope, Base, Measurement
from cranio.utils import logger, configure_logging
parser = argparse.ArgumentParser()
parser.add_argument('path', help='Path to SQLite file (.db)', type=str)


if __name__ == '__main__':
    configure_logging()
    args = parser.parse_args()
    path = Path(args.path)
    database = Database(drivername='sqlite', database=str(path))
    database.create_engine()
    with session_scope(database) as s:
        for table_name, table in Base.metadata.tables.items():
            path_out = path.parent / (table_name + '.csv')
            logger.info(f'Read table {table_name} from {database.url} to {path_out}')
            df = pd.read_sql_table(table_name, con=database.engine)
            df.to_csv(path_out, sep=';', index=False)