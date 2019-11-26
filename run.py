import sys
from argparse import ArgumentParser
from cranio.app import app
from cranio.utils import attach_excepthook, logger, configure_logging
from cranio.model import Session, DefaultDatabase
from cranio.state_machine import StateMachine
from config import Config

log_level_parser = ArgumentParser(add_help=False)
log_level_parser.add_argument(
    '--log-level',
    help='Logging level',
    type=str,
    default='INFO',
    choices=['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
)

# Attach custom excepthook
attach_excepthook()

parser = ArgumentParser(
    description='Cranio measurement software', parents=[log_level_parser]
)
subparsers = parser.add_subparsers(title='cmd', dest='cmd')

parser_initdb = subparsers.add_parser('initdb')
parser_initdb.add_argument(
    '--reset',
    action='store_true',
    help='Clear database before initialization (i.e., fresh start)',
)

parser_run = subparsers.add_parser('run')
parser_run.add_argument(
    '-d', '--enable-dummy-sensor', action='store_true', help='Allow dummy sensor'
)


def initdb(args):
    """
    Initialize cranio.db.

    :return:
    """
    database = DefaultDatabase.SQLITE
    database.create_engine()
    if args.reset:
        database.clear()
    database.init()


def run(args):
    """
    Run the craniodistractor application.

    :return: 
    """
    if args.enable_dummy_sensor:
        Config.ENABLE_DUMMY_SENSOR = True
    database = DefaultDatabase.SQLITE
    database.create_engine()
    Session.init(database=database)
    machine = StateMachine(database)
    logger.register_machine(machine)
    logger.info('Start state machine')
    machine.start()
    ret = app.exec_()
    logger.info('Stop state machine')
    machine.stop()
    return ret


commands = {'initdb': initdb, 'run': run}


def main():
    args = parser.parse_args()
    configure_logging(log_level=args.log_level)
    command = commands[args.cmd]
    sys.exit(command(args))


if __name__ == '__main__':
    main()
