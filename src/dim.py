import argparse
import traceback
from curses import *

from editor import Editor

def main(stdscr):
    parser = argparse.ArgumentParser()
    parser.add_argument('-path', '-p', help='path to file being edited')
    parser.add_argument('-debug', help='launch the editor in debug mode', action='store_true')
    args = parser.parse_args()
    try:
        editor = Editor(stdscr, args)
        editor.launch()
    except:
        print(traceback.format_exc())

if __name__ == '__main__':
    wrapper(main)
