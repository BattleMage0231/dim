import argparse
import os
import string
import sys
import time
import traceback
from curses import *

import debug

class Constants:
    ALLOWED_CHARS = string.ascii_letters + string.digits + string.punctuation + ' '
    BG_COLOR = (1, 7, 233)
    BAR_COLOR = (2, 7, 237)
    DIM_COLOR = (3, 221, 237)
    FILE_COLOR = (4, 200, 237)
    MODE_COLOR = (5, 35, 237)
    CUR_COMMAND_COLOR = (6, 150, 237)
    HIGHLIGHT_COLOR = (7, 233, 7)
    MODE_INSERT = 'INSERT'
    MODE_COMMAND = 'COMMAND'
    MODE_SELECT = 'SELECT'
    DIRECTION_BEFORE = 0
    DIRECTION_AFTER = 1

class Editor:
    def __init__(self, stdscr, args):
        self.stdscr = stdscr
        self.args = args
        self.debug_mode = args.debug
        # setup colors
        start_color()
        use_default_colors()
        init_pair(*Constants.BG_COLOR)
        init_pair(*Constants.BAR_COLOR)
        init_pair(*Constants.DIM_COLOR)
        init_pair(*Constants.FILE_COLOR)
        init_pair(*Constants.MODE_COLOR)
        init_pair(*Constants.CUR_COMMAND_COLOR)
        init_pair(*Constants.HIGHLIGHT_COLOR)
        # set initial values
        self.height, self.width = stdscr.getmaxyx()
        self.scrtop, self.scrbottom = 0, self.height - 2 # exclusive
        self.scrleft, self.scrright = 0, self.width - 1 # exclusive
        self.caret_y, self.caret_x = 0, 0
        self.text_selected = False
        self.select_start_x, self.select_start_y = -1, -1
        self.select_end_x, self.select_end_y = -1, -1
        self.selecting_direction = Constants.DIRECTION_BEFORE
        self.lines = ['']
        self.file_name = 'None'
        self.mode = Constants.MODE_COMMAND
        self.cur_command = ''
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
            print('The encoding of the file is not supported.')
            os._exit(1)

    def display_text(self):
        self.height, self.width = self.stdscr.getmaxyx()
        self.stdscr.erase()
        self.stdscr.addstr(' Dim v1', color_pair(3))
        self.stdscr.addstr(' ' * 5, color_pair(2))
        self.stdscr.addstr('Editing ' + self.file_name, color_pair(4))
        self.stdscr.addstr(' ' * 20, color_pair(2))
        self.stdscr.addstr(self.cur_command, color_pair(6))
        self.stdscr.addstr(
            ' ' * (self.width - 56 - len(self.file_name) - len(self.mode) - len(self.cur_command)),
            color_pair(2)
        )
        self.stdscr.addstr('Mode: ' + self.mode, color_pair(5))
        self.stdscr.addstr(' ' * 10, color_pair(2))
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
            if len(line) >= self.scrleft:
                displayed_line = line[self.scrleft : min(len(line), self.scrright - 1)]
                if self.text_selected:
                    if self.select_start_y < self.scrtop + index:
                        if self.select_end_y > self.scrtop + index:
                            self.stdscr.addstr(displayed_line, color_pair(7))
                        elif self.select_end_y == self.scrtop + index:
                            if self.select_start_y == self.scrtop + index:
                                if self.select_start_x - self.scrleft < 0:
                                    if self.select_end_x - self.scrleft < 0:
                                        self.stdscr.addstr(displayed_line)
                                    elif self.select_end_x - self.scrleft >= self.width:
                                        self.stdscr.addstr(displayed_line, color_pair(7))
                                    else:
                                        self.stdscr.addstr(
                                            displayed_line[ : self.select_end_x - self.scrleft + 1],
                                            color_pair(7)
                                        )
                                        self.stdscr.addstr(displayed_line[self.select_end_x - self.scrleft + 1 : ])
                                elif self.select_start_x - self.scrleft >= self.width:
                                    pass
                                else:
                                    if self.select_end_x - self.scrleft >= self.width:
                                        self.stdscr.addstr(displayed_line[ : self.select_start_x - self.scrleft])
                                        self.stdscr.addstr(
                                            displayed_line[self.select_start_x - self.scrleft : ],
                                            color_pair(7)
                                        )
                                    else:
                                        self.stdscr.addstr(displayed_line[ : self.select_start_x - self.scrleft])
                                        self.stdscr.addstr(
                                            displayed_line[self.select_start_x - self.scrleft : self.select_end_x - self.scrleft + 1],
                                            color_pair(7)
                                        )
                                        self.stdscr.addstr(displayed_line[self.select_end_x - self.scrleft + 1 : ])
                            else:
                                self.stdscr.addstr(
                                    displayed_line[ : self.select_end_x + 1 - self.scrleft],
                                    color_pair(7)
                                )
                                self.stdscr.addstr(displayed_line[self.select_end_x + 1 - self.scrleft : ])
                        else:
                            self.stdscr.addstr(displayed_line)
                    elif self.select_start_y == self.scrtop + index:
                        if self.select_end_y == self.scrtop + index:
                            if self.select_start_x - self.scrleft < 0:
                                if self.select_end_x - self.scrleft < 0:
                                    self.stdscr.addstr(displayed_line)
                                elif self.select_end_x - self.scrleft >= self.width:
                                    self.stdscr.addstr(displayed_line, color_pair(7))
                                else:
                                    self.stdscr.addstr(
                                        displayed_line[ : self.select_end_x - self.scrleft + 1],
                                        color_pair(7)
                                    )
                                    self.stdscr.addstr(displayed_line[self.select_end_x - self.scrleft + 1 : ])
                            elif self.select_start_x - self.scrleft >= self.width:
                                pass
                            else:
                                if self.select_end_x - self.scrleft >= self.width:
                                    self.stdscr.addstr(displayed_line[ : self.select_start_x - self.scrleft])
                                    self.stdscr.addstr(
                                        displayed_line[self.select_start_x - self.scrleft : ],
                                        color_pair(7)
                                    )
                                else:
                                    self.stdscr.addstr(displayed_line[ : self.select_start_x - self.scrleft])
                                    self.stdscr.addstr(
                                        displayed_line[self.select_start_x - self.scrleft : self.select_end_x - self.scrleft + 1],
                                        color_pair(7)
                                    )
                                    self.stdscr.addstr(displayed_line[self.select_end_x - self.scrleft + 1 : ])
                        else:
                            self.stdscr.addstr(displayed_line[ : self.select_start_x - self.scrleft])
                            self.stdscr.addstr(
                               displayed_line[self.select_start_x - self.scrleft : ],
                               color_pair(7)
                            )
                    else:
                        self.stdscr.addstr(displayed_line)
                else:
                    self.stdscr.addstr(displayed_line)
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

    def launch(self):
        self.stdscr.bkgd(' ', color_pair(1) | A_BOLD)
        if self.debug_mode:
            if self.args.path is None:
                cur_index = 0
                key = None
                while key != '\n' and key != chr(13):
                    if key == 'KEY_UP':
                        cur_index -= 1
                        cur_index = max(cur_index, 0)
                    elif key == 'KEY_DOWN':
                        cur_index += 1
                        cur_index = min(cur_index, len(debug.TEXT_LIST) - 1)
                    self.stdscr.erase()
                    self.stdscr.addstr(' You have launched the editor in debug mode.')
                    self.stdscr.addstr('\n\n')
                    self.stdscr.addstr(' Test documents:')
                    self.stdscr.addstr('\n')
                    for index, value in enumerate(debug.TEXT_LIST):
                        text_name, _ = value 
                        self.stdscr.addstr('\n ')
                        self.stdscr.addstr(text_name, color_pair(7 if index == cur_index else 1))
                    self.stdscr.addstr('\n\n ') 
                    key = self.stdscr.getkey()      
                self.lines = debug.TEXT_LIST[cur_index][1].split('\n')
            else:
                self.stdscr.addstr(' You have launched the editor in debug mode.')
                self.stdscr.addstr('\n\n')
                self.stdscr.addstr(' Press any key to continue... ')
                self.stdscr.getkey()
        self.display_text()
        while True:
            key = self.stdscr.getkey()
            self.height, self.width = self.stdscr.getmaxyx()
            if self.mode == Constants.MODE_COMMAND:
                self.parse_command(key)
            elif self.mode == Constants.MODE_INSERT:
                self.parse_insert(key)
            elif self.mode == Constants.MODE_SELECT:
                self.parse_select(key)
            self.display_text()

    def parse_command(self, key):
        if key == chr(27):
            # escape
            os._exit(1)
        elif key in Constants.ALLOWED_CHARS:
            if self.width - 57 - len(self.file_name) - len(self.mode) - len(self.cur_command) > 0:
                self.cur_command += key
        elif key == '\b' or key == 'KEY_BACKSPACE':
            self.cur_command = self.cur_command[ : -1]
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
        elif key == '\n' or key == chr(13):
            try:
                if self.cur_command == 'i':
                    if self.text_selected:
                        self.text_selected = False
                    self.mode = Constants.MODE_INSERT
                elif self.cur_command == 's':
                    if self.debug_mode:
                        self.stdscr.erase()
                        self.stdscr.addstr(' Confirm that you want to save the file (type \'save\'): ')
                        self.stdscr.refresh()
                        for desired_key in 'save':
                            cur_key = self.stdscr.getkey()
                            self.stdscr.addstr(cur_key)
                            self.stdscr.refresh()
                            if cur_key != desired_key:
                                return
                    try:
                        if self.args.path is not None:
                            if not os.path.isfile(self.args.path): 
                                raise FileNotFoundError
                            with open(self.args.path, 'w') as edit_file:
                                edit_file.write('\n'.join(self.lines))
                    except (FileNotFoundError, PermissionError, OSError):
                        print('The current file can no longer be found.')
                        os._exit(1)
                    except UnicodeDecodeError:
                        print('The encoding of the file is not supported.')
                        os._exit(1)
                elif self.cur_command == 'v':
                    self.mode = Constants.MODE_SELECT
                    self.select_start_y, self.select_start_x = self.caret_y, self.caret_x
                    self.select_end_y, self.select_end_x = self.caret_y, self.caret_x
                    self.text_selected = True
            finally:
                self.cur_command = ''

    def parse_insert(self, key):
        if key == chr(27):
            # escape
            self.mode = Constants.MODE_COMMAND
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
        elif key in Constants.ALLOWED_CHARS:
            # allowed text characters
            line = self.lines[self.caret_y]
            line = line[ : self.caret_x] + key + line[self.caret_x : ]
            self.lines[self.caret_y] = line
            self.caret_x += 1 

    def calculate_selection(self):
        y, x = self.caret_y, self.caret_x
        # both inclusive
        s_y, s_x = self.select_start_y, self.select_start_x
        e_y, e_x = self.select_end_y, self.select_end_x
        if y < s_y:
            self.select_start_y, self.select_start_x = y, x
            self.selecting_direction = Constants.DIRECTION_BEFORE
        elif y == s_y and x < s_x:
            self.select_start_y, self.select_start_x = y, x
            self.selecting_direction = Constants.DIRECTION_BEFORE
        elif y > e_y:
            self.select_end_y, self.select_end_x = y, x
            self.selecting_direction = Constants.DIRECTION_AFTER
        elif y == e_y and x > e_x:
            self.select_end_y, self.select_end_x = y, x
            self.selecting_direction = Constants.DIRECTION_AFTER
        elif self.selecting_direction == Constants.DIRECTION_BEFORE:
            self.select_start_y, self.select_start_x = y, x
        elif self.selecting_direction == Constants.DIRECTION_AFTER:
            self.select_end_y, self.select_end_x = y, x

    def parse_select(self, key):
        if key == chr(27):
            # escape
            self.mode = Constants.MODE_COMMAND
        elif key == 'KEY_RESIZE':
            pass
        elif key == 'KEY_LEFT' or key == '\b' or key == 'KEY_BACKSPACE':
            self.move_left(1)
            self.calculate_selection()
        elif key == 'KEY_RIGHT' or key == ' ':
            self.move_right(1)
            self.calculate_selection()
        elif key == 'KEY_UP':
            self.move_up(1)
            self.calculate_selection()
        elif key == 'KEY_DOWN':
            self.move_down(1)
            self.calculate_selection()
        elif key == 'KEY_PPAGE':
            # page up
            self.caret_y = 0
            self.caret_x = 0
            self.selecting_direction = Constants.DIRECTION_BEFORE
            self.calculate_selection()
        elif key == 'KEY_NPAGE':
            # page down
            self.caret_y = len(self.lines) - 1
            self.caret_x = len(self.lines[self.caret_y])
            self.selecting_direction = Constants.DIRECTION_AFTER
            self.calculate_selection()
        elif key == 'KEY_HOME':
            # go to left
            self.caret_x = 0
            self.selecting_direction = Constants.DIRECTION_BEFORE
            self.calculate_selection()
        elif key == 'KEY_END':
            # go to right
            self.caret_x = len(self.lines[self.caret_y])
            self.selecting_direction = Constants.DIRECTION_AFTER
            self.calculate_selection()

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
