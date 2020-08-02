import argparse
import os
import traceback
import sys
from curses import *

from editor import Editor

TUTORIAL_LENGTH = 2

def main(stdscr):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file',
        nargs = '?',
        default = None,
        help = 'path to the file being edited'
    )
    parser.add_argument(
        '-g', '--debug',
        help = 'launch the editor in debug mode',
        action = 'store_true'
    )
    parser.add_argument(
        '-t', '--tutorial',
        help = 'displays tutorial file at provided index',
        type = int,
        choices = range(1, TUTORIAL_LENGTH + 1)
    )
    parser.add_argument(
        '--read-only',
        help = 'indicate that the file cannot be written to',
        action = 'store_true'
    )
    args = parser.parse_args()
    try:
        if args.tutorial is not None:
            resource_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tutorial')
            if not os.path.isdir(resource_dir):
                print('The tutorials directory was not found!\n')
                sys.exit(1)
            files = [i for i in os.listdir(resource_dir) if i.startswith('{}_'.format(str(args.tutorial)))]
            if len(files) != 1:
                print('There was an error while looking for the selected tutorial file.\n')
                sys.exit(1)
            args.file = os.path.join(resource_dir, files[0])
            args.read_only = True
        e = Editor(stdscr, args)
        e.launch()
    except Exception as e:
        error_type = type(e)
        if error_type == SystemError:
            pass
        elif error_type == NotImplementedError:
            print('This feature hasn\'t been implemented yet.\n')
            print('Feature: {}\n'.format(str(e)))
        else:
            print('A fatal error has occured.\n')
            if args.debug:
                print(traceback.format_exc())
                with open('tests/log.txt', 'w') as log:
                    log.write(traceback.format_exc())
    finally:
        print('Exited the editor.')

if __name__ == '__main__':
    wrapper(main)