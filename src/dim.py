import argparse
import traceback
from curses import *

from editor import Editor

def main(stdscr):
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs = '?', default = None, help = 'path to the file being edited')
    parser.add_argument('-g', '--debug', help = 'launch the editor in debug mode', action = 'store_true')
    args = parser.parse_args()
    try:
        editor = Editor(stdscr, args)
        editor.launch()
    except Exception as e:
        if type(e) == SystemError:
            print('Successfully exited editor.')
        else:
            print('A fatal error has occured.\n')
            print(traceback.format_exc())

if __name__ == '__main__':
    wrapper(main)
