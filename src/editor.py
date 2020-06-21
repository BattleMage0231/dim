import os
import string
import sys
import time
import traceback
import zlib
from curses import *

import debug
from matrix import Matrix
from position import Position

### TODO add syntax highlighting (highlighting override syntax highlighting) ###

class Constants:
    ALLOWED_CHARS = string.ascii_letters + string.digits + string.punctuation + ' '
    MODE_INSERT = 'INSERT'
    MODE_COMMAND = 'COMMAND'
    MODE_SELECT = 'SELECT'
    DIRECTION_BEFORE = 0
    DIRECTION_AFTER = 1

class Editor:
    def __init__(self, stdscr, args):
        self.args = args
        self.debug_mode = args.debug
        # set initial values
        self.matrix = Matrix(stdscr)
        self.caret = Position(0, 0)
        self.scr_topleft = Position(0, 0)
        self.scr_bottomright = Position(self.matrix.get_height() - 2, self.matrix.get_width() - 1)
        self.select_start_pos = Position()
        self.select_end_pos = Position()
        self.text_selected = False
        self.last_selection_before = True
        self.file_name = 'None'
        self.mode = Constants.MODE_COMMAND
        self.cur_command = ''
        # try to find a file
        try:
            if args.path is not None:
                with open(args.path, 'r') as edit_file:
                    self.matrix.load_text(edit_file.read())
                self.file_name = os.path.basename(args.path)
        except (FileNotFoundError, PermissionError, OSError):
            print('The path given is invalid.')
            os._exit(1)
        except UnicodeDecodeError:
            print('The encoding of the file is not supported.')
            os._exit(1)
        # make undo stack
        self.undo_stack = [(self.caret.copy(), self.compress(self.matrix.get_content()))]
        self.undo_ptr = 0

    def compress(self, message):
        return zlib.compress(message.encode('utf8'))

    def decompress(self, message):
        return zlib.decompress(message).decode('utf8')

    def save_state(self):
        self.undo_stack = self.undo_stack[ : self.undo_ptr + 1]
        self.undo_ptr += 1
        self.undo_stack.append((self.caret.copy(), self.compress(self.matrix.get_content())))

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

    def display(self):
        self.scroll_screen()
        self.matrix.display(
            self.matrix.get_header(self.file_name, self.mode, self.cur_command),
            self.caret,
            self.select_start_pos if self.text_selected else None,
            self.select_end_pos if self.text_selected else None,
            self.scr_topleft,
            self.scr_bottomright
        )

    def get_key(self):
        return self.matrix.get_key()

    def move_left(self, pos, spaces = 1):
        pos.move_left(self.matrix.get_lines(), spaces)

    def move_right(self, pos, spaces = 1):
        pos.move_right(self.matrix.get_lines(), spaces)

    def move_up(self, pos, spaces = 1):
        pos.move_up(self.matrix.get_lines(), spaces)

    def move_down(self, pos, spaces = 1):
        pos.move_down(self.matrix.get_lines(), spaces)

    def launch(self):
        if self.debug_mode:
            if self.args.path is None:
                choice = self.matrix.display_choose(
                    [
                        'You have launched the editor in debug mode...',
                        '',
                        'Test documents:'
                    ],
                    [text[0] for text in debug.TEXT_LIST]
                )
                self.matrix.load_text(debug.TEXT_LIST[choice][1])
                self.undo_stack = [(self.caret.copy(), self.compress(self.matrix.get_content()))]
            else:
                self.matrix.display_text([
                    'You have launched the editor in debug mode...',
                    '',
                    'Press any key to continue.'
                ])
        self.display()
        while True:
            key = self.get_key()
            if key == '`' and self.debug_mode:
                os._exit(1)
            if self.mode == Constants.MODE_COMMAND:
                self.parse_command(key)
            elif self.mode == Constants.MODE_INSERT:
                self.parse_insert(key)
            elif self.mode == Constants.MODE_SELECT:
                self.parse_select(key)
            self.display()

    def parse_general_command(self, command):
        """Executes a general command in all command modes. Returns true if command was found."""
        if command == 'i':
            self.text_selected = False
            self.mode = Constants.MODE_INSERT
        elif command == 's':
            if self.debug_mode:
                res = self.matrix.display_confirm(
                    'Confirm that you want to save the file (type \'save\'): ',
                    'save'
                )
                if not res:
                    # return without confirmation
                    # True means that the command was found as a general command
                    return True
            try:
                if self.args.path is not None:
                    if not os.path.isfile(self.args.path): 
                        raise FileNotFoundError
                    with open(self.args.path, 'w') as edit_file:
                        edit_file.write(self.matrix.get_lines())
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
            self.last_selection_before = True
        elif command == 'z':
            self.undo_ptr = max(0, self.undo_ptr - 1)
            caret, compressed = self.undo_stack[self.undo_ptr]
            self.caret.x = caret.x
            self.caret.y = caret.y
            self.matrix.load_text(self.decompress(compressed))
        elif command == 'y':
            if self.undo_ptr + 1 < len(self.undo_stack):
                self.undo_ptr += 1
                caret, compressed = self.undo_stack[self.undo_ptr]
                self.caret.x = caret.x
                self.caret.y = caret.y
                self.matrix.load_text(self.decompress(compressed))
        else:
            return False
        return True

    def parse_command(self, key):
        if key == chr(27):
            # escape
            os._exit(1)
        elif key in Constants.ALLOWED_CHARS:
            # if command fits on screen
            padding = 57 + sum(list(map(len, [self.file_name, self.mode, self.cur_command])))
            self.matrix.update_screen_size()
            if self.matrix.get_width() - padding > 0:
                self.cur_command += key
        elif key == '\b' or key == 'KEY_BACKSPACE':
            self.cur_command = self.cur_command[ : -1]
        elif key == chr(452) or key == 'KEY_LEFT':
            self.move_left(self.caret)
        elif key == chr(454) or key == 'KEY_RIGHT':
            self.move_right(self.caret)
        elif key == chr(450) or key == 'KEY_UP':
            self.move_up(self.caret)
        elif key == chr(456) or key == 'KEY_DOWN':
            self.move_down(self.caret)
        elif key == 'KEY_PPAGE':
            # page up
            self.caret.y = 0
            self.caret.x = 0
        elif key == 'KEY_NPAGE':
            # page down
            self.caret.y = self.matrix.get_text_height() - 1
            self.caret.x = self.matrix.get_line_length(self.caret.y)
        elif key == 'KEY_HOME':
            # go to left
            self.caret.x = 0
        elif key == 'KEY_END':
            # go to right
            self.caret.x = self.matrix.get_line_length(self.caret.y)
        elif key == '\n' or key == chr(13):
            try:
                if self.parse_general_command(self.cur_command):
                    pass
                elif self.cur_command == 'x':
                    self.matrix.delete_substr(
                        self.caret.y, self.caret.x, self.caret.x + 1
                    )
                    self.save_state()
            finally:
                self.cur_command = ''

    def parse_insert(self, key):
        if key == chr(27):
            # escape
            self.mode = Constants.MODE_COMMAND
        elif key == '\b' or key == 'KEY_BACKSPACE':
            # backspace
            if self.caret.x != 0:
                self.matrix.delete_substr(
                    self.caret.y, self.caret.x - 1, self.caret.x
                )
                self.move_left(self.caret)
                self.save_state()
            elif self.caret.y != 0:
                # concatenate two lines
                self.caret.x = self.matrix.get_line_length(self.caret.y - 1)
                self.matrix.join(self.caret.y - 1, self.caret.y)
                self.caret.y -= 1
                self.save_state()
        elif key == '\t':
            # tab
            self.matrix.insert(self.caret.y, self.caret.x, ' ' * 4)
            self.caret.x += 4
            self.save_state()
        elif key == '\n' or key == chr(13):
            # newline or carriage return
            if self.caret.x > self.matrix.get_line_length(self.caret.y):
                self.matrix.lines.insert(self.caret.y + 1, '')
            else:
                self.matrix.split_line(self.caret.y, self.caret.x)
            self.caret.x = 0
            self.caret.y += 1
            self.save_state()
        elif key == chr(452) or key == 'KEY_LEFT':
            self.move_left(self.caret)
        elif key == chr(454) or key == 'KEY_RIGHT':
            self.move_right(self.caret)
        elif key == chr(450) or key == 'KEY_UP':
            self.move_up(self.caret)
        elif key == chr(456) or key == 'KEY_DOWN':
            self.move_down(self.caret)
        elif key == 'KEY_PPAGE':
            # page up
            self.caret.y = 0
            self.caret.x = 0
        elif key == 'KEY_NPAGE':
            # page down
            self.caret.y = self.matrix.get_text_height() - 1
            self.caret.x = self.matrix.get_line_length(self.caret.y)
        elif key == 'KEY_HOME':
            # go to left
            self.caret.x = 0
        elif key == 'KEY_END':
            # go to right
            self.caret.x = self.matrix.get_line_length(self.caret.y)
        elif key in Constants.ALLOWED_CHARS:
            # allowed text characters
            self.matrix.insert(self.caret.y, self.caret.x, key)
            self.caret.x += 1 
            self.save_state()

    def calculate_selection(self):
        if self.caret.is_before(self.select_start_pos):
            # expand selection left
            self.select_start_pos = self.caret.copy()
            self.last_selection_before = True
        elif self.caret.is_after(self.select_end_pos):
            # expand selection right
            self.select_end_pos = self.caret.copy()
            self.last_selection_before = False
        elif self.last_selection_before:
            # shrink collection right
            self.select_start_pos = self.caret.copy()            
        else:
            # shrink collection left
            self.select_end_pos = self.caret.copy()           

    def parse_select(self, key):
        if key == chr(27):
            # escape
            self.text_selected = False
            self.mode = Constants.MODE_COMMAND
        elif key in Constants.ALLOWED_CHARS:
            # if command fits on screen
            padding = 57 + sum(list(map(len, [self.file_name, self.mode, self.cur_command])))
            self.matrix.update_screen_size()
            if self.matrix.get_width() - padding > 0:
                self.cur_command += key
        elif key == '\b' or key == 'KEY_BACKSPACE':
            self.cur_command = self.cur_command[ : -1]
        elif key == chr(452) or key == 'KEY_LEFT' or key == '\b' or key == 'KEY_BACKSPACE':
            self.move_left(self.caret)
            self.calculate_selection()
        elif key == chr(454) or key == 'KEY_RIGHT' or key == ' ':
            self.move_right(self.caret)
            self.calculate_selection()
        elif key == chr(450) or key == 'KEY_UP':
            self.move_up(self.caret)
            self.calculate_selection()
        elif key == chr(456) or key == 'KEY_DOWN':
            self.move_down(self.caret)
            self.calculate_selection()
        elif key == 'KEY_PPAGE':
            # page up
            self.caret.y = 0
            self.caret.x = 0
            self.calculate_selection()
        elif key == 'KEY_NPAGE':
            # page down
            self.caret.y = self.matrix.get_text_height() - 1
            self.caret.x = self.matrix.get_line_length(self.caret.y)
            self.calculate_selection()
        elif key == 'KEY_HOME':
            # go to left
            self.caret.x = 0
            self.calculate_selection()
        elif key == 'KEY_END':
            # go to right
            self.caret.x = self.matrix.get_line_length(self.caret.y)
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
                        self.matrix.delete_substr(
                            self.select_start_pos.y,
                            self.select_start_pos.x,
                            self.select_start_pos.x + dif
                        )
                    else:
                        # delete inbetween
                        index = self.select_start_pos.y + 1
                        for _ in range(index, self.select_end_pos.y):
                            self.matrix.pop_line(index)
                        # delete ending of start
                        spaces = self.matrix.get_line_length(self.select_start_pos.y) - self.select_start_pos.x
                        self.matrix.delete_substr(
                            self.select_start_pos.y,
                            self.select_start_pos.x,
                            self.select_start_pos.x + spaces
                        )
                        # delete starting of end
                        spaces = self.select_end_pos.x + 1
                        self.matrix.delete_substr(
                            index, 0, spaces
                        )
                        if self.matrix.get_line(index) == '':
                            self.matrix.pop_line(index)
                    self.mode = Constants.MODE_COMMAND
                    self.text_selected = False
                    self.save_state()
            finally:
                self.cur_command = ''