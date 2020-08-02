import argparse
import os

# constants
_tutorial_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tutorial')
TUTORIAL_LENGTH = len(os.listdir(_tutorial_dir)) if os.path.exists(_tutorial_dir) else 0

# setup
_parser = argparse.ArgumentParser()
_parser.add_argument(
    'file',
    nargs = '?',
    default = None,
    help = 'path to the file being edited'
)
_parser.add_argument(
    '-g', '--debug',
    help = 'launch the editor in debug mode',
    action = 'store_true'
)
_parser.add_argument(
    '-t', '--tutorial',
    help = 'displays tutorial file at provided index',
    type = int,
    choices = range(1, TUTORIAL_LENGTH + 1)
)
_parser.add_argument(
    '--read-only',
    help = 'indicate that the file cannot be written to',
    action = 'store_true'
)

# parse and return args
def getargs():
    return _parser.parse_args()