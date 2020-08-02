import os
import sys

from mode.base import Mode, MAX_COMMAND_LENGTH
import mode.command as command_mode
import mode.insert as insert_mode
import mode.select as select_mode
from utils.buffer import Buffer
from utils.keys import normalize_key, is_char
from utils.position import Position, NULL_POS
from utils.state import StateManager

class SelectMode(Mode):
    def __init__(self, buffer, state_manager, caret, file_name, args):
        super().__init__(buffer, state_manager, caret, file_name, args)
        self.name = 'SELECT'
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
    
    def parse_command(self, command):
        if command == 'i':
            # change to insert mode
            return insert_mode.InsertMode(*self.get_properties())
        elif command == 's':
            if self.args.read_only:
                self.buffer.display_text([
                    'This file cannot be written to. The editor may have been launched in read only mode.'
                ])
                return self
            if self.debug_mode:
                res = self.buffer.display_confirm(
                    'Confirm that you want to save the file (type \'save\'): ',
                    'save'
                )
                if not res:
                    # return without confirmation
                    return self
            if self.args.file is None:
                self.args.file = self.buffer.display_prompt('Enter the name of the file: ')
                self.file_name = os.path.basename(self.args.file)
                try:
                    if not os.path.isfile(self.args.file):
                        open(self.args.file, 'a').close()
                except:
                    print('An error occured when creating the file.\n')
                    sys.exit(1)
            try:
                if self.args.file is not None:
                    if not os.path.isfile(self.args.file): 
                        raise FileNotFoundError
                    with open(self.args.file, 'w') as edit_file:
                        edit_file.write(self.buffer.get_content())
            except (FileNotFoundError, PermissionError, OSError):
                print('The current file can no longer be found.\n')
                sys.exit(1)
            except UnicodeDecodeError:
                print('The encoding of the file is not supported.\n')
                sys.exit(1)
            self.state_manager.saved = True
        elif command == 'v':
            return self
        elif command == 'x':
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
                self.buffer.delete_substr(
                    index, 0, spaces
                )
                if self.buffer.get_line(index) == '':
                    self.buffer.pop_line(index)
            self.push_state()
            return command_mode.CommandMode(*self.get_properties())
        elif command == 'z':
            caret, text = self.state_manager.undo()
            self.caret = caret.copy()
            self.buffer.load_text(text)
            return command_mode.CommandMode(*self.get_properties())
        elif command == 'y':
            caret, text = self.state_manager.redo()
            if caret is not None and text is not None:
                self.caret = caret.copy()
                self.buffer.load_text(text)
                return command_mode.CommandMode(*self.get_properties())
        return self

    def parse_key(self, key):
        if key == 'KEY_ESCAPE':
            return command_mode.CommandMode(*self.get_properties())
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
                return self.parse_command(self.cur_command)
            finally:
                self.cur_command = ''
        elif is_char(key):
            if len(self.cur_command) < MAX_COMMAND_LENGTH:
                self.cur_command += key
        return self