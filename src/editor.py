import argparse
import os
import string
import sys
import time
import traceback
from curses import *

class Constants:
    ALLOWED_CHARS = string.ascii_letters + string.digits + string.punctuation + ' '
    BG_COLOR = (1, 7, 233)
    BAR_COLOR = (2, 7, 237)
    DIM_COLOR = (3, 221, 237)
    FILE_COLOR = (4, 200, 237)
    LAST_COMMAND_COLOR = (5, 35, 237)

class Editor:
    def __init__(self, stdscr, args):
        self.stdscr = stdscr
        self.args = args
        # setup colors
        start_color()
        use_default_colors()
        init_pair(*Constants.BG_COLOR)
        init_pair(*Constants.BAR_COLOR)
        init_pair(*Constants.DIM_COLOR)
        init_pair(*Constants.FILE_COLOR)
        init_pair(*Constants.LAST_COMMAND_COLOR)
        # set initial values
        self.height, self.width = stdscr.getmaxyx()
        self.scrtop, self.scrbottom = 0, self.height - 2 # exclusive
        self.scrleft, self.scrright = 0, self.width - 1 # exclusive
        self.caret_y, self.caret_x = 0, 0
        self.lines = ['']
        self.file_name = 'None'
        self.cur_command = None
        # try to find a file
        try:
            if args.path is not None:
                with open(args.path, 'r') as edit_file:
                    self.lines = edit_file.read().split('\n')
                self.file_name = os.path.basename(args.path)
        except (FileNotFoundError, PermissionError, OSError):
            print('The path given is invalid.')
            os._exit(1)
        except UnicodeDecodeError:
            # try to open the file in binary format
            try:
                with open(args.path, 'rb') as edit_file:
                    self.lines = [str(edit_file.read())[2 : -1]]
                self.file_name = os.path.basename(args.path)
            except Exception:
                print('The encoding of the file is not supported.')
                os._exit(1)

    def display_text(self):
        self.stdscr.erase()
        self.stdscr.addstr(' Dim v1', color_pair(3))
        self.stdscr.addstr(' ' * 5, color_pair(2))
        self.stdscr.addstr('Editing ' + self.file_name, color_pair(4))
        if self.cur_command is not None:
            self.stdscr.addstr(' ' * (self.width - 30 - len(self.file_name) - len(self.cur_command)), color_pair(2))
            self.stdscr.addstr(self.cur_command, color_pair(5))
            self.stdscr.addstr(' ' * 10, color_pair(2))
        else:
            self.stdscr.addstr(' ' * (self.width - 20 - len(self.file_name)), color_pair(2))
        self.stdscr.addstr('─' * self.width, color_pair(2))
        if not self.lines:
            self.stdscr.addstr('')
        # scroll up down
        if self.scrtop > self.caret_y:
            self.scrbottom -= self.scrtop - self.caret_y
            self.scrtop = self.caret_y
        elif self.scrbottom <= self.caret_y:
            self.scrtop += self.caret_y - self.scrbottom + 1
            self.scrbottom = self.caret_y + 1
        # scroll left right
        if self.caret_x < self.scrleft:
            self.scrright -= self.scrleft - self.caret_x
            self.scrleft = self.caret_x
        elif self.caret_x >= self.scrright:
            self.scrleft += self.caret_x - self.scrright + 1
            self.scrright = self.caret_x + 1
        displayed_lines = self.lines[self.scrtop : min(len(self.lines), self.scrbottom)]
        for index, line in enumerate(displayed_lines):
            self.stdscr.addstr(' ')
            if len(line) < self.scrleft:
                pass
            elif len(line) < self.scrright - 1:
                self.stdscr.addstr(line[self.scrleft : ])
            else:
                self.stdscr.addstr(line[self.scrleft : self.scrright - 1])
            if index != len(displayed_lines) - 1:
                self.stdscr.addstr('\n')
        self.stdscr.move(self.caret_y - self.scrtop + 2, self.caret_x - self.scrleft + 1)

    def move_left(self, spaces):
        if not self.lines:
            return
        self.caret_x -= spaces
        if self.caret_x >= 0:
            return
        while self.caret_x < 0 and self.caret_y > 0:
            self.caret_y -= 1
            if len(self.lines[self.caret_y]) == 0:
                self.caret_x += 1
            else:
                self.caret_x += len(self.lines[self.caret_y])
        if self.caret_y < 0 or self.caret_x < 0:
            self.caret_y = self.caret_x = 0
        else:
            self.caret_x += min(1, len(self.lines[self.caret_y]))

    def move_right(self, spaces):
        if not self.lines:
            return
        self.caret_x += spaces
        if self.caret_x <= len(self.lines[self.caret_y]):
            return
        while self.caret_y < len(self.lines) - 1 and spaces > 0:
            self.caret_y += 1
            if len(self.lines[self.caret_y]) == 0:
                spaces -= 1
            else:
                spaces -= len(self.lines[self.caret_y])
        if self.caret_y >= len(self.lines):
            self.caret_y = len(self.lines) - 1
            self.caret_x = len(self.lines[self.caret_y])
        else:
            self.caret_x = max(0, spaces + len(self.lines[self.caret_y]) - 1)

    def move_up(self, spaces):
        if not self.lines:
            return
        self.caret_y -= spaces
        if self.caret_y < 0:
            self.caret_y = 0
        self.caret_x = min(len(self.lines[self.caret_y]), self.caret_x)

    def move_down(self, spaces):
        if not self.lines:
            return
        self.caret_y += spaces
        if self.caret_y >= len(self.lines):
            self.caret_y = len(self.lines) - 1
        self.caret_x = min(len(self.lines[self.caret_y]), self.caret_x)

    def main(self):
        self.stdscr.bkgd(' ', color_pair(1) | A_BOLD)
        self.display_text()
        while True:
            key = self.stdscr.getkey()
            self.height, self.width = self.stdscr.getmaxyx()
            if key == chr(27):
                # escape
                break
            elif key == '\b' or key == 'KEY_BACKSPACE':
                # backspace
                if self.caret_x != 0:
                    line = self.lines[self.caret_y]
                    line = line[ : self.caret_x - 1] + line[self.caret_x : ]
                    self.lines[self.caret_y] = line
                    self.caret_x -= 1
                elif self.caret_y != 0:
                    line = self.lines[self.caret_y]
                    self.lines.pop(self.caret_y)
                    self.caret_y -= 1
                    self.caret_x = len(self.lines[self.caret_y])
                    self.lines[self.caret_y] += line
            elif key == '\t':
                # tab
                line = self.lines[self.caret_y]
                line = line[ : self.caret_x] + (' ' * 4) + line[self.caret_x : ]
                self.lines[self.caret_y] = line
                self.caret_x += 4
            elif key == '\n' or key == chr(13):
                # newline or carriage return
                if self.caret_x == len(self.lines[self.caret_y]):
                    self.lines.insert(self.caret_y + 1, '')
                else:
                    dif = self.lines[self.caret_y][self.caret_x : ]
                    self.lines[self.caret_y] = self.lines[self.caret_y][ : self.caret_x]
                    self.lines.insert(self.caret_y + 1, dif)
                self.caret_x = 0
                self.caret_y += 1
            elif key == 'KEY_RESIZE':
                pass
            elif key == 'KEY_LEFT':
                self.move_left(1)
            elif key == 'KEY_RIGHT':
                self.move_right(1)
            elif key == 'KEY_UP':
                self.move_up(1)
            elif key == 'KEY_DOWN':
                self.move_down(1)
            elif key == 'KEY_PPAGE':
                # page up
                self.caret_y = 0
                self.caret_x = 0
            elif key == 'KEY_NPAGE':
                # page down
                self.caret_y = len(self.lines) - 1
                self.caret_x = len(self.lines[self.caret_y])
            elif key == 'KEY_HOME':
                # go to left
                self.caret_x = 0
            elif key == 'KEY_END':
                # go to right
                self.caret_x = len(self.lines[self.caret_y])
            elif key.startswith('ALT'):
                # alt + key
                self.cur_command = key
            elif key in Constants.ALLOWED_CHARS:
                # allowed text characters
                line = self.lines[self.caret_y]
                line = line[ : self.caret_x] + key + line[self.caret_x : ]
                self.lines[self.caret_y] = line
                self.caret_x += 1
            self.display_text()

def main(stdscr):
    parser = argparse.ArgumentParser()
    parser.add_argument('-path', help='path to file being edited')
    args = parser.parse_args()
    try:
        editor = Editor(stdscr, args)
        editor.main()
    except:
        print(traceback.format_exc())

if __name__ == '__main__':
    wrapper(main)
