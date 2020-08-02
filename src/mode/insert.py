from mode.base import Mode, MAX_COMMAND_LENGTH
import mode.command as command_mode
import mode.insert as insert_mode
import mode.select as select_mode
from utils.buffer import Buffer
from utils.keys import normalize_key, is_char
from utils.position import Position, NULL_POS
from utils.state import StateManager

class InsertMode(Mode):
    def __init__(self, buffer, state_manager, caret, file_name, args):
        super().__init__(buffer, state_manager, caret, file_name, args)
        self.name = 'INSERT'

    def parse_command(self, command):
        # insert mode has no commands
        return self

    def parse_key(self, key):
        if key == 'KEY_ESCAPE':
            return command_mode.CommandMode(*self.get_properties())
        elif key == 'KEY_BACKSPACE':
            if self.caret.x != 0:
                self.buffer.delete_substr(
                    self.caret.y, self.caret.x - 1, self.caret.x
                )
                self.caret.move_left(self.buffer)
                self.push_state()
            elif self.caret.y != 0:
                # concatenate two lines
                self.caret.x = self.buffer.get_line_length(self.caret.y - 1)
                self.buffer.join(self.caret.y - 1, self.caret.y)
                self.caret.y -= 1
                self.push_state()
        elif key == 'KEY_TAB':
            self.buffer.insert(self.caret.y, self.caret.x, ' ' * 4)
            self.caret.x += 4
            self.push_state()
        elif key == 'KEY_NEWLINE':
            if self.caret.x > self.buffer.get_line_length(self.caret.y):
                self.buffer.lines.insert(self.caret.y + 1, '')
            else:
                self.buffer.split_line(self.caret.y, self.caret.x)
            self.caret = Position(self.caret.y + 1, 0)
            self.push_state()
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
        elif is_char(key):
            # allowed text characters
            self.buffer.insert(self.caret.y, self.caret.x, key)
            self.caret.x += 1 
            self.push_state()
        return self
