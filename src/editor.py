# TODO move screen related stuff to a file with a class called Buffer (buffer.py)
# TODO implement undo and redo via zlib or files

import argparse
import os
import string
import sys
import time
import traceback
from curses import *

import debug
from position import Position

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
        self.lines = ['']
        self.height, self.width = stdscr.getmaxyx()
        self.scr_topleft = Position(0, 0)
        self.scr_bottomright = Position(self.height - 2, self.width - 1)
        self.caret = Position(0, 0)
        self.text_selected = False
        self.select_start_pos = Position()
        self.select_end_pos = Position()
        self.selecting_direction = Constants.DIRECTION_BEFORE
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

    def get_header(self):
        self.height, self.width = self.stdscr.getmaxyx()
        padding = (self.width - 56 - len(self.file_name) - len(self.mode) - len(self.cur_command))
        header = [
            (' Dim v1',                     3), 
            (' ' * 5,                       2),
            ('Editing ' + self.file_name,   4),
            (' ' * 20,                      2),
            (self.cur_command,              6),
            (' ' * padding,                 2),
            ('Mode: ' + self.mode,          5),
            (' ' * 10,                      2),
            ('─' * self.width,              2) # horizontal bar
        ]
        return header

    def scroll_screen(self):
        # scroll up down
        if self.scr_topleft.y > self.caret.y:
            self.scr_bottomright.y -= self.scr_topleft.y - self.caret.y
            self.scr_topleft.y = self.caret.y
        elif self.scr_bottomright.y <= self.caret.y:
            self.scr_topleft.y += self.caret.y - self.scr_bottomright.y + 1
            self.scr_bottomright.y = self.caret.y + 1
        # scroll left right
        if self.caret.x < self.scr_topleft.x:
            self.scr_bottomright.x -= self.scr_topleft.x - self.caret.x
            self.scr_topleft.x = self.caret.x
        elif self.caret.x >= self.scr_bottomright.x:
            self.scr_topleft.x += self.caret.x - self.scr_bottomright.x + 1
            self.scr_bottomright.x = self.caret.x + 1

    def display_text(self):
        self.height, self.width = self.stdscr.getmaxyx()
        self.stdscr.erase()
        # header
        header = self.get_header()
        for text, color in header:
            self.stdscr.addstr(text, color_pair(color))
        # default value of lines
        if not self.lines:
            self.stdscr.addstr('')
        # scroll screen
        self.scroll_screen()
        # display lines
        displayed_lines = self.lines[self.scr_topleft.y : min(len(self.lines), self.scr_bottomright.y)]
        for index, line in enumerate(displayed_lines):
            self.stdscr.addstr(' ')
            if len(line) >= self.scr_topleft.x:
                # inclusive, position of line start and line end of displayed line
                ln_start = Position(self.scr_topleft.y + index, self.scr_topleft.x)
                ln_end = Position(self.scr_topleft.y + index, self.scr_topleft.x + self.width - 1)
                displayed_line = line[ln_start.x : min(len(line), self.scr_bottomright.x - 1)]
                if self.text_selected:
                    # whether start position and end position of line are between selection
                    start_between = ln_start.is_between(self.select_start_pos, self.select_end_pos)
                    end_between = ln_end.is_between(self.select_start_pos, self.select_end_pos)
                    # whether selection is between start and end position
                    select_start_between = self.select_start_pos.is_between(ln_start, ln_end)
                    select_end_between = self.select_end_pos.is_between(ln_start, ln_end)
                    if start_between and end_between:
                        # completely enclosed
                        self.stdscr.addstr(displayed_line, color_pair(7))
                    elif start_between:
                        # only start between selection
                        # end is on same line
                        # only starting portion is highlighted
                        self.stdscr.addstr(displayed_line[ : self.select_end_pos.x - ln_start.x + 1], color_pair(7))
                        self.stdscr.addstr(displayed_line[self.select_end_pos.x - ln_start.x + 1 : ])
                    elif end_between:
                        # only end between selection
                        # start is on same line
                        # only ending portion is highlighted
                        self.stdscr.addstr(displayed_line[ : self.select_start_pos.x - ln_start.x])
                        self.stdscr.addstr(displayed_line[self.select_start_pos.x - ln_start.x : ], color_pair(7))
                    elif select_start_between and select_end_between:
                        # selection is all on this line
                        # start and end not highlighted
                        self.stdscr.addstr(displayed_line[ : self.select_start_pos.x - ln_start.x])
                        self.stdscr.addstr(
                            displayed_line[self.select_start_pos.x - ln_start.x : self.select_end_pos.x - ln_start.x + 1],
                            color_pair(7)
                        )
                        self.stdscr.addstr(displayed_line[self.select_end_pos.x + 1  - ln_start.x : ])
                    else:
                        # not enclosed by selection at all
                        self.stdscr.addstr(displayed_line)
                else:
                    self.stdscr.addstr(displayed_line)
            if index != len(displayed_lines) - 1:
                self.stdscr.addstr('\n')
        self.stdscr.move(self.caret.y - self.scr_topleft.y + 2, self.caret.x - self.scr_topleft.x + 1)

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
            if key == '`' and self.debug_mode:
                os._exit(1)
            self.height, self.width = self.stdscr.getmaxyx()
            if self.mode == Constants.MODE_COMMAND:
                self.parse_command(key)
            elif self.mode == Constants.MODE_INSERT:
                self.parse_insert(key)
            elif self.mode == Constants.MODE_SELECT:
                self.parse_select(key)
            self.display_text()

    def delete(self, y, x, number = 1):
        """Deletes some number of characters on one line"""
        line = self.lines[y]
        line = line[ : x] + line[x + number : ]
        self.lines[y] = line

    def insert(self, y, x, text):
        line = self.lines[y]
        line = line[ : x] + text + line[x : ]
        self.lines[y] = line 

    def confirm(self, text, password):
        self.stdscr.erase()
        self.stdscr.addstr(' ' + text)
        self.stdscr.refresh()
        for desired_key in password:
            cur_key = self.stdscr.getkey()
            self.stdscr.addstr(cur_key)
            self.stdscr.refresh()
            if cur_key != desired_key:
                return False
        return True

    def parse_general_command(self, command):
        """Executes a general command in all command modes. Returns true if command was found."""
        if command == 'i':
            self.text_selected = False
            self.mode = Constants.MODE_INSERT
        elif command == 's':
            if self.debug_mode:
                res = self.confirm('Confirm that you want to save the file (type \'save\'): ', 'save')
                if not res:
                    # return without confirmation
                    # True means that the command was found as a general command
                    return True
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
        elif command == 'v':
            self.mode = Constants.MODE_SELECT
            self.select_start_pos = self.caret.copy()
            self.select_end_pos = self.caret.copy()
            self.text_selected = True
            self.selecting_direction = Constants.DIRECTION_BEFORE
        else:
            return False
        return True

    def parse_command(self, key):
        if key == chr(27):
            # escape
            os._exit(1)
        elif key in Constants.ALLOWED_CHARS:
            if self.width - 57 - len(self.file_name) - len(self.mode) - len(self.cur_command) > 0:
                self.cur_command += key
        elif key == '\b' or key == 'KEY_BACKSPACE':
            self.cur_command = self.cur_command[ : -1]
        elif key == 'KEY_LEFT':
            self.caret.move_left(1, self.lines)
        elif key == 'KEY_RIGHT':
            self.caret.move_right(1, self.lines)
        elif key == 'KEY_UP':
            self.caret.move_up(1, self.lines)
        elif key == 'KEY_DOWN':
            self.caret.move_down(1, self.lines)
        elif key == 'KEY_PPAGE':
            # page up
            self.caret.y = 0
            self.caret.x = 0
        elif key == 'KEY_NPAGE':
            # page down
            self.caret.y = len(self.lines) - 1
            self.caret.x = len(self.lines[self.caret.y])
        elif key == 'KEY_HOME':
            # go to left
            self.caret.x = 0
        elif key == 'KEY_END':
            # go to right
            self.caret.x = len(self.lines[self.caret.y])
        elif key == '\n' or key == chr(13):
            try:
                if self.parse_general_command(self.cur_command):
                    pass
                elif self.cur_command == 'x':
                    self.delete(self.caret.y, self.caret.x)
            finally:
                self.cur_command = ''

    def parse_insert(self, key):
        if key == chr(27):
            # escape
            self.mode = Constants.MODE_COMMAND
        elif key == '\b' or key == 'KEY_BACKSPACE':
            # backspace
            if self.caret.x != 0:
                self.delete(self.caret.y, self.caret.x - 1)
                self.caret.x -= 1
            elif self.caret.y != 0:
                # concatenate two lines
                line = self.lines[self.caret.y]
                self.lines.pop(self.caret.y)
                self.caret.y -= 1
                self.caret.x = len(self.lines[self.caret.y])
                self.lines[self.caret.y] += line
        elif key == '\t':
            # tab
            self.insert(self.caret.y, self.caret.x, ' ' * 4)
            self.caret.x += 4
        elif key == '\n' or key == chr(13):
            # newline or carriage return
            if self.caret.x == len(self.lines[self.caret.y]):
                self.lines.insert(self.caret.y + 1, '')
            else:
                dif = self.lines[self.caret.y][self.caret.x : ]
                self.lines[self.caret.y] = self.lines[self.caret.y][ : self.caret.x]
                self.lines.insert(self.caret.y + 1, dif)
            self.caret.x = 0
            self.caret.y += 1
        elif key == 'KEY_LEFT':
            self.caret.move_left(1, self.lines)
        elif key == 'KEY_RIGHT':
            self.caret.move_right(1, self.lines)
        elif key == 'KEY_UP':
            self.caret.move_up(1, self.lines)
        elif key == 'KEY_DOWN':
            self.caret.move_down(1, self.lines)
        elif key == 'KEY_PPAGE':
            # page up
            self.caret.y = 0
            self.caret.x = 0
        elif key == 'KEY_NPAGE':
            # page down
            self.caret.y = len(self.lines) - 1
            self.caret.x = len(self.lines[self.caret.y])
        elif key == 'KEY_HOME':
            # go to left
            self.caret.x = 0
        elif key == 'KEY_END':
            # go to right
            self.caret.x = len(self.lines[self.caret.y])
        elif key in Constants.ALLOWED_CHARS:
            # allowed text characters
            self.insert(self.caret.y, self.caret.x, key)
            self.caret.x += 1 

    def calculate_selection(self):
        if self.caret.is_before(self.select_start_pos):
            # expand selection left
            self.select_start_pos = self.caret.copy()
            self.selecting_direction = Constants.DIRECTION_BEFORE
        elif self.caret.is_after(self.select_end_pos):
            # expand selection right
            self.select_end_pos = self.caret.copy()
            self.selecting_direction = Constants.DIRECTION_AFTER
        elif self.selecting_direction == Constants.DIRECTION_BEFORE:
            # shrink collection right
            self.select_start_pos = self.caret.copy()
        elif self.selecting_direction == Constants.DIRECTION_AFTER:
            # shrink collection left
            self.select_end_pos = self.caret.copy()

    def parse_select(self, key):
        if key == chr(27):
            # escape
            self.text_selected = False
            self.mode = Constants.MODE_COMMAND
        elif key in Constants.ALLOWED_CHARS:
            if self.width - 57 - len(self.file_name) - len(self.mode) - len(self.cur_command) > 0:
                self.cur_command += key
        elif key == '\b' or key == 'KEY_BACKSPACE':
            self.cur_command = self.cur_command[ : -1]
        elif key == 'KEY_LEFT' or key == '\b' or key == 'KEY_BACKSPACE':
            self.caret.move_left(1, self.lines)
            self.calculate_selection()
        elif key == 'KEY_RIGHT' or key == ' ':
            self.caret.move_right(1, self.lines)
            self.calculate_selection()
        elif key == 'KEY_UP':
            self.caret.move_up(1, self.lines)
            self.calculate_selection()
        elif key == 'KEY_DOWN':
            self.caret.move_down(1, self.lines)
            self.calculate_selection()
        elif key == 'KEY_PPAGE':
            # page up
            self.caret.y = 0
            self.caret.x = 0
            self.selecting_direction = Constants.DIRECTION_BEFORE
            self.calculate_selection()
        elif key == 'KEY_NPAGE':
            # page down
            self.caret.y = len(self.lines) - 1
            self.caret.x = len(self.lines[self.caret.y])
            self.selecting_direction = Constants.DIRECTION_AFTER
            self.calculate_selection()
        elif key == 'KEY_HOME':
            # go to left
            self.caret.x = 0
            self.selecting_direction = Constants.DIRECTION_BEFORE
            self.calculate_selection()
        elif key == 'KEY_END':
            # go to right
            self.caret.x = len(self.lines[self.caret.y])
            self.selecting_direction = Constants.DIRECTION_AFTER
            self.calculate_selection()
        elif key == '\n' or key == chr(13):
            try:
                if self.parse_general_command(self.cur_command):
                    pass
                elif self.cur_command == 'x':
                    # set caret position to selection start position
                    self.caret = self.select_start_pos.copy()
                    if self.select_start_pos.y == self.select_end_pos.y:
                        # delete substring
                        dif = self.select_end_pos.x - self.select_start_pos.x + 1
                        self.delete(self.select_start_pos.y, self.select_start_pos.x, dif)
                    else:
                        # delete inbetween
                        index = self.select_start_pos.y + 1
                        for _ in range(index, self.select_end_pos.y):
                            self.lines.pop(index)
                        # delete ending of start
                        spaces = len(self.lines[self.select_start_pos.y]) - self.select_start_pos.x
                        self.delete(self.select_start_pos.y, self.select_start_pos.x, spaces)
                        # delete starting of end
                        spaces = self.select_end_pos.x + 1
                        self.delete(index, 0, spaces)
                        if not self.lines[index]:
                            self.lines.pop(index)
                    self.mode = Constants.MODE_COMMAND
                    self.text_selected = False
            finally:
                self.cur_command = ''

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
