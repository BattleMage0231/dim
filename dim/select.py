import os
import sys

from base import *
from buffer import *
from keys import *
from position import *
from state import StateManager

class SelectMode(Mode):
    def __init__(self, buffer, state_manager, caret, file_name, args):
        super().__init__(buffer, state_manager, caret, file_name, args)
        self.name = MODE_SELECT
        self.cur_command = ''
        self.select_start_pos = self.caret.copy()
        self.select_end_pos = self.caret.copy()
        # stores whether the last position of the caret outside of the selection is before or after it
        self.last_pos_before = True 

    def calculate_selection(self):
        if self.caret.is_before(self.select_start_pos):
            # expand selection left
            self.select_start_pos = self.caret.copy()
            self.last_pos_before = True
        elif self.caret.is_after(self.select_end_pos):
            # expand selection right
            self.select_end_pos = self.caret.copy()
            self.last_pos_before = False
        elif self.last_pos_before:
            # shrink collection right
            self.select_start_pos = self.caret.copy()            
        else:
            # shrink collection left
            self.select_end_pos = self.caret.copy()
    
    def parse_command(self, command, args = []):
        # try to parse a general command
        res = self.parse_general_command(command, args)
        if res is not None:
            return res
        # try specific commands
        if command == 'x':
            # set caret position to selection start position
            self.caret = self.select_start_pos.copy()
            if self.select_start_pos.y == self.select_end_pos.y:
                # delete substring
                dif = self.select_end_pos.x - self.select_start_pos.x + 1
                self.buffer.delete_substr(
                    self.select_start_pos.y,
                    self.select_start_pos.x,
                    self.select_start_pos.x + dif
                )
            else:
                # delete inbetween
                index = self.select_start_pos.y + 1
                for _ in range(index, self.select_end_pos.y):
                    self.buffer.pop_line(index)
                # delete ending of start
                spaces = self.buffer.get_line_length(self.select_start_pos.y) - self.select_start_pos.x
                self.buffer.delete_substr(
                    self.select_start_pos.y,
                    self.select_start_pos.x,
                    self.select_start_pos.x + spaces
                )
                # delete starting of end
                spaces = self.select_end_pos.x + 1
                self.buffer.delete_substr(index, 0, spaces)
                if self.buffer.get_line(index) == '':
                    self.buffer.pop_line(index)
            self.push_state()
            return MODE_COMMAND
        return MODE_SELECT

    def parse_key(self, key):
        if key == 'KEY_ESCAPE':
            return MODE_COMMAND
        elif key == 'KEY_BACKSPACE':
            self.cur_command = self.cur_command[ : -1]
        elif key in ['KEY_LEFT', 'KEY_BACKSPACE']:
            self.caret.move_left(self.buffer)
            self.calculate_selection()
        elif key in ['KEY_RIGHT', ' ']:
            self.caret.move_right(self.buffer)
            self.calculate_selection()
        elif key == 'KEY_UP':
            self.caret.move_up(self.buffer)
            self.calculate_selection()
        elif key == 'KEY_DOWN':
            self.caret.move_down(self.buffer)
            self.calculate_selection()
        elif key == 'KEY_PAGE_UP':
            self.caret = Position(0, 0)
            self.calculate_selection()
        elif key == 'KEY_PAGE_DOWN':
            self.caret.y = self.buffer.get_text_height() - 1
            self.caret.x = self.buffer.get_line_length(self.caret.y)
            self.calculate_selection()
        elif key == 'KEY_HOME':
            # go to left
            self.caret.x = 0
            self.calculate_selection()
        elif key == 'KEY_END':
            # go to right
            self.caret.x = self.buffer.get_line_length(self.caret.y)
            self.calculate_selection()
        elif key == 'KEY_NEWLINE':
            try:
                return self.parse_command(*self.parse_args(self.cur_command))
            finally:
                self.cur_command = ''
        elif ischar(key):
            if len(self.cur_command) < MAX_COMMAND_LENGTH:
                self.cur_command += key
        return MODE_SELECT
