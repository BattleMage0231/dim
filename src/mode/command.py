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

class CommandMode(Mode):
    def __init__(self, buffer, state_manager, caret, file_name, args):
        super().__init__(buffer, state_manager, caret, file_name, args)
        self.name = 'COMMAND'
        self.cur_command = ''

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
            return select_mode.SelectMode(*self.get_properties())
        elif command == 'x':
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
        return self

    def parse_key(self, key):
        if key == 'KEY_ESCAPE':
            if not (self.state_manager.saved or self.args.read_only):
                res = self.buffer.display_confirm(
                    'Do you want to quit without saving? (y/n): ',
                    'y'
                )
                if not res:
                    return self
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
        elif is_char(key):
            if len(self.cur_command) < MAX_COMMAND_LENGTH:
                self.cur_command += key
        return self
