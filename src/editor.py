import argparse
import os
import string
import sys
import time
import traceback
import zlib
from curses import *

import debug
from screenmanager import ScreenManager
from position import Position

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
        self.screen_manager = ScreenManager(stdscr)
        self.selecting_direction = Constants.DIRECTION_BEFORE
        self.file_name = 'None'
        self.mode = Constants.MODE_COMMAND
        self.cur_command = ''
        # these values are duplicates from ScreenManager
        # they need to be updated each time the values in ScreenManager are (and vice versa)
        self.text_selected = self.screen_manager.text_selected
        self.select_start_pos = self.screen_manager.select_start_pos
        self.select_end_pos = self.screen_manager.select_end_pos
        self.caret = self.screen_manager.caret
        self.lines = self.screen_manager.lines
        # try to find a file
        try:
            if args.path is not None:
                with open(args.path, 'r') as edit_file:
                    self.screen_manager.load_text(edit_file.read())
                self.file_name = os.path.basename(args.path)
        except (FileNotFoundError, PermissionError, OSError):
            print('The path given is invalid.')
            os._exit(1)
        except UnicodeDecodeError:
            print('The encoding of the file is not supported.')
            os._exit(1)
        # make undo stack
        self.undo_stack = [(self.caret.copy(), self.compress('\n'.join(self.lines)))]
        self.undo_ptr = 0

    def sync(self):
        """Syncs the shared values between this object and its screen_manager"""
        self.screen_manager.text_selected = self.text_selected
        self.screen_manager.select_start_pos = self.select_start_pos
        self.screen_manager.select_end_pos = self.select_end_pos
        self.screen_manager.caret = self.caret
        self.screen_manager.lines = self.lines

    def compress(self, message):
        return zlib.compress(message.encode('utf8'))

    def decompress(self, message):
        return zlib.decompress(message).decode('utf8')

    def save_state(self):
        self.undo_stack = self.undo_stack[ : self.undo_ptr]
        self.undo_ptr += 1
        self.undo_stack.append((self.caret.copy(), self.compress('\n'.join(self.lines))))

    def display(self):
        self.screen_manager.display(
            self.screen_manager.get_header(self.file_name, self.mode, self.cur_command)
        )

    def get_key(self):
        return self.screen_manager.get_key()

    def launch(self):
        if self.debug_mode:
            if self.args.path is None:
                choice = self.screen_manager.display_choose(
                    [
                        'You have launched the editor in debug mode...',
                        '',
                        'Test documents:'
                    ],
                    [text[0] for text in debug.TEXT_LIST]
                )
                self.screen_manager.load_text(debug.TEXT_LIST[choice][1])
                self.undo_stack = [(self.caret.copy(), self.compress('\n'.join(self.lines)))]
            else:
                self.screen_manager.display_text([
                    'You have launched the editor in debug mode...',
                    '',
                    'Press any key to continue.'
                ])
        self.display()
        while True:
            key = self.get_key()
            if key == '`' and self.debug_mode:
                os._exit(1)
            self.screen_manager.get_size()
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
            self.sync()
            self.mode = Constants.MODE_INSERT
        elif command == 's':
            if self.debug_mode:
                res = self.screen_manager.display_confirm(
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
                        edit_file.write('\n'.join(self.screen_manager.get_lines()))
            except (FileNotFoundError, PermissionError, OSError):
                print('The current file can no longer be found.')
                os._exit(1)
            except UnicodeDecodeError:
                print('The encoding of the file is not supported.')
                os._exit(1)
        elif command == 'v':
            self.mode = Constants.MODE_SELECT
            self.select_start_pos = self.caret.copy()
            self.sync()
            self.select_end_pos = self.caret.copy()
            self.sync()
            self.text_selected = True
            self.sync()
            self.selecting_direction = Constants.DIRECTION_BEFORE
        elif command == 'z':
            if len(self.undo_stack) > 1:
                self.undo_ptr = max(0, self.undo_ptr - 1)
                caret, compressed = self.undo_stack[self.undo_ptr]
                self.caret.x = caret.x
                self.caret.y = caret.y
                self.screen_manager.load_text(self.decompress(compressed))
        elif command == 'y':
            if self.undo_ptr + 1 < len(self.undo_stack):
                self.undo_ptr += 1
                caret, compressed = self.undo_stack[self.undo_ptr]
                self.caret.x = caret.x
                self.caret.y = caret.y
                self.screen_manager.load_text(self.decompress(compressed))
        else:
            return False
        return True

    def parse_command(self, key):
        if key == chr(27):
            # escape
            os._exit(1)
        elif key in Constants.ALLOWED_CHARS:
            # if command fits on screen
            if self.screen_manager.width - 57 - len(self.file_name) - len(self.mode) - len(self.cur_command) > 0:
                self.cur_command += key
        elif key == '\b' or key == 'KEY_BACKSPACE':
            self.cur_command = self.cur_command[ : -1]
        elif key == chr(452) or key == 'KEY_LEFT':
            self.caret.move_left(1, self.lines)
        elif key == chr(454) or key == 'KEY_RIGHT':
            self.caret.move_right(1, self.lines)
        elif key == chr(450) or key == 'KEY_UP':
            self.caret.move_up(1, self.lines)
        elif key == chr(456) or key == 'KEY_DOWN':
            self.caret.move_down(1, self.lines)
        elif key == 'KEY_PPAGE':
            # page up
            # no need to sync here since we are mutating the object
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
                    self.screen_manager.delete(self.caret.y, self.caret.x)
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
                self.screen_manager.delete(self.caret.y, self.caret.x - 1)
                self.caret.move_left(1, self.lines)
                self.save_state()
            elif self.caret.y != 0:
                # concatenate two lines
                self.caret.x = len(self.lines[self.caret.y - 1])
                self.screen_manager.join(self.caret.y - 1, self.caret.y)
                self.caret.y -= 1
                self.save_state()
        elif key == '\t':
            # tab
            self.screen_manager.insert(self.caret.y, self.caret.x, ' ' * 4)
            self.caret.x += 4
            self.save_state()
        elif key == '\n' or key == chr(13):
            # newline or carriage return
            if self.caret.x == len(self.lines[self.caret.y]):
                self.lines.insert(self.caret.y + 1, '')
            else:
                self.screen_manager.split(self.caret.y, self.caret.x)
            self.caret.x = 0
            self.caret.y += 1
            self.save_state()
        elif key == chr(452) or key == 'KEY_LEFT':
            self.caret.move_left(1, self.lines)
        elif key == chr(454) or key == 'KEY_RIGHT':
            self.caret.move_right(1, self.lines)
        elif key == chr(450) or key == 'KEY_UP':
            self.caret.move_up(1, self.lines)
        elif key == chr(456) or key == 'KEY_DOWN':
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
            self.screen_manager.insert(self.caret.y, self.caret.x, key)
            self.caret.x += 1 
            self.save_state()

    def calculate_selection(self):
        if self.caret.is_before(self.select_start_pos):
            # expand selection left
            self.select_start_pos = self.caret.copy()
            self.sync()
            self.selecting_direction = Constants.DIRECTION_BEFORE
        elif self.caret.is_after(self.select_end_pos):
            # expand selection right
            self.select_end_pos = self.caret.copy()
            self.sync()
            self.selecting_direction = Constants.DIRECTION_AFTER
        elif self.selecting_direction == Constants.DIRECTION_BEFORE:
            # shrink collection right
            self.select_start_pos = self.caret.copy()
            self.sync()
        elif self.selecting_direction == Constants.DIRECTION_AFTER:
            # shrink collection left
            self.select_end_pos = self.caret.copy()
            self.sync()

    def parse_select(self, key):
        if key == chr(27):
            # escape
            self.text_selected = False
            self.sync()
            self.mode = Constants.MODE_COMMAND
        elif key in Constants.ALLOWED_CHARS:
            if self.screen_manager.width - 57 - len(self.file_name) - len(self.mode) - len(self.cur_command) > 0:
                self.cur_command += key
        elif key == '\b' or key == 'KEY_BACKSPACE':
            self.cur_command = self.cur_command[ : -1]
        elif key == chr(452) or key == 'KEY_LEFT' or key == '\b' or key == 'KEY_BACKSPACE':
            self.caret.move_left(1, self.lines)
            self.calculate_selection()
        elif key == chr(454) or key == 'KEY_RIGHT' or key == ' ':
            self.caret.move_right(1, self.lines)
            self.calculate_selection()
        elif key == chr(450) or key == 'KEY_UP':
            self.caret.move_up(1, self.lines)
            self.calculate_selection()
        elif key == chr(456) or key == 'KEY_DOWN':
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
                    self.sync()
                    if self.select_start_pos.y == self.select_end_pos.y:
                        # delete substring
                        dif = self.select_end_pos.x - self.select_start_pos.x + 1
                        self.screen_manager.delete(self.select_start_pos.y, self.select_start_pos.x, dif)
                    else:
                        # delete inbetween
                        index = self.select_start_pos.y + 1
                        for _ in range(index, self.select_end_pos.y):
                            self.lines.pop(index)
                        # delete ending of start
                        spaces = len(self.lines[self.select_start_pos.y]) - self.select_start_pos.x
                        self.screen_manager.delete(self.select_start_pos.y, self.select_start_pos.x, spaces)
                        # delete starting of end
                        spaces = self.select_end_pos.x + 1
                        self.screen_manager.delete(index, 0, spaces)
                        if not self.lines[index]:
                            self.lines.pop(index)
                    self.mode = Constants.MODE_COMMAND
                    self.text_selected = False
                    self.sync()
                    self.save_state()
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
