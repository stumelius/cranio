import sys
from argparse import ArgumentParser
from cranio.app import app
from cranio.utils import attach_excepthook, logger, configure_logging
from cranio.model import Session, DefaultDatabase, Patient
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

parser_add_patient = subparsers.add_parser('add_patient')
parser_add_patient.add_argument('patient_id', help='Pseudonymized patient identifier')

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


def add_patient(args):
    database = DefaultDatabase.SQLITE
    database.create_engine()
    Patient.add_new(patient_id=args.patient_id, database=database)


def run(args):
    """
    Run the craniodistractor application.

    :return: 
    """
    if args.enable_dummy_sensor:
        Config.ENABLE_DUMMY_SENSOR = True
    database = DefaultDatabase.SQLITE
    database.create_engine()
    machine = StateMachine(database)
    # Initialize session
    with database.session_scope() as s:
        session = Session()
        s.add(session)
    machine.session = session
    logger.register_machine(machine)
    logger.info('Start state machine')
    machine.start()
    ret = app.exec_()
    logger.info('Stop state machine')
    machine.stop()
    return ret


commands = {'initdb': initdb, 'run': run, 'add_patient': add_patient}


def main():
    args = parser.parse_args()
    configure_logging(log_level=args.log_level)
    if args.cmd is None:
        parser.print_help()
        return
    command = commands[args.cmd]
    sys.exit(command(args))


if __name__ == '__main__':
    main()
