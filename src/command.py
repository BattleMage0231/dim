import os
import sys

from base import *
from buffer import Buffer
from keys import *
from position import *
from state import StateManager

class CommandMode(Mode):
    def __init__(self, buffer, state_manager, caret, file_name, args):
        super().__init__(buffer, state_manager, caret, file_name, args)
        self.name = MODE_COMMAND
        self.cur_command = ''

    def parse_command(self, command):
        # try to parse a general command
        res = self.parse_general_command(command)
        if res is not None:
            return res
        # try specific commands
        if command == 'x':
            self.buffer.delete_substr(
                self.caret.y, self.caret.x, self.caret.x + 1
            )
            self.push_state()
        elif command == 'z':
            caret, text = self.state_manager.undo()
            self.caret = caret.copy()
            self.buffer.load_text(text)
        elif command == 'y':
            caret, text = self.state_manager.redo()
            if caret is not None and text is not None:
                self.caret = caret.copy()
                self.buffer.load_text(text)
        return MODE_COMMAND

    def parse_key(self, key):
        if key == 'KEY_ESCAPE':
            if not (self.state_manager.saved or self.args.read_only):
                res = self.buffer.display_confirm(
                    'Do you want to quit without saving? (y/n): ',
                    'y'
                )
                if not res:
                    return MODE_COMMAND
            sys.exit(0)
        elif key == 'KEY_BACKSPACE':
            self.cur_command = self.cur_command[ : -1]
        elif key == 'KEY_LEFT':
            self.caret.move_left(self.buffer)
        elif key == 'KEY_RIGHT':
            self.caret.move_right(self.buffer)
        elif key == 'KEY_UP':
            self.caret.move_up(self.buffer)
        elif key == 'KEY_DOWN':
            self.caret.move_down(self.buffer)
        elif key == 'KEY_PAGE_UP':
            self.caret = Position(0, 0)
        elif key == 'KEY_PAGE_DOWN':
            self.caret.y = self.buffer.get_text_height() - 1
            self.caret.x = self.buffer.get_line_length(self.caret.y)
        elif key == 'KEY_HOME':
            # go to left
            self.caret.x = 0
        elif key == 'KEY_END':
            # go to right
            self.caret.x = self.buffer.get_line_length(self.caret.y)
        elif key == 'KEY_NEWLINE':
            try:
                return self.parse_command(self.cur_command)
            finally:
                self.cur_command = ''
        elif ischar(key):
            if len(self.cur_command) < MAX_COMMAND_LENGTH:
                self.cur_command += key
        return MODE_COMMAND
