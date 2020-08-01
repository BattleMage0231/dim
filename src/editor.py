import os
import sys
import time
import traceback
from curses import *

from buffer import Buffer, ALLOWED_CHARS
from position import Position, NULL_POS
from state import StateManager

# editor mode constants
MODE_INSERT = 'INSERT'
MODE_COMMAND = 'COMMAND'
MODE_SELECT = 'SELECT'

# editor constants
MAX_COMMAND_LENGTH = 20

### TODO add syntax highlighting (highlighting overrides syntax highlighting) ###

class Editor:
    def __init__(self, stdscr, args):
        self.args = args
        self.debug_mode = args.debug
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        # set initial values
        self.buffer = Buffer(stdscr)
        self.state_manager = StateManager()
        self.caret = Position(0, 0)
        self.scr_topleft = Position(0, 0) # inclusive
        self.scr_bottomright = Position(self.buffer.get_height() - 2, self.buffer.get_width() - 1) # inclusive
        self.select_start_pos = Position(None, None)
        self.select_end_pos = NULL_POS
        self.text_selected = False
        self.last_selection_before = True
        self.file_name = 'None'
        self.mode = MODE_COMMAND
        self.cur_command = ''
        # try to find a file
        try:
            if args.file is not None:
                with open(args.file, 'r') as edit_file:
                    self.buffer.load_text(edit_file.read())
                self.file_name = os.path.basename(args.file)
        except (FileNotFoundError, PermissionError, OSError) as e:
            print('The path given is invalid or inaccessible.\n')
            sys.exit(1)
        except UnicodeDecodeError as e:
            print('The encoding of the file is not supported.\n')
            sys.exit(1)
        # push initial state
        self.state_manager.push_state(self.caret.copy(), self.buffer.get_content())

    def resize_screen(self):
        """
        Resizes the area of the matrix shown to the user when the terminal window is resized.
        """
        # there was much more code here previously which adjusted the screen
        # however, it is much more easy and efficient to just rely on the scroll_screen function
        self.scr_topleft = Position(0, 0)
        self.scr_bottomright = Position(self.buffer.get_height() - 2, self.buffer.get_width() - 1)

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
        self.buffer.update_screen_size()
        self.scroll_screen()
        self.buffer.flush(
            self.buffer.get_header(self.file_name, self.mode, self.cur_command),
            self.caret,
            self.select_start_pos if self.text_selected else None,
            self.select_end_pos if self.text_selected else None,
            self.scr_topleft,
            self.scr_bottomright
        )

    def push_state(self):
        self.state_manager.push_state(self.caret, self.buffer.get_content())

    def get_key(self):
        return self.buffer.get_key()

    def launch(self):
        if self.debug_mode:
            if self.args.file is None:
                text_list = ['NONE']
                debug_dir = os.path.join(self.script_dir, 'debug')
                if os.path.exists(debug_dir):
                    text_list.extend(sorted([file_name for file_name in os.listdir(debug_dir)]))
                choice = self.buffer.display_choose(
                    [
                        'You have launched the editor in debug mode...',
                        '',
                        'Test documents:'
                    ],
                    [text for text in text_list]
                )
                if choice == 0:
                    self.buffer.load_text('')
                elif os.path.exists(debug_dir):
                    file_name = os.path.join(debug_dir, text_list[choice])
                    with open(file_name, 'r') as text:
                        self.buffer.load_text(text.read())
                self.state_manager.clear_stack()
                self.state_manager.push_state(self.caret.copy(), self.buffer.get_content())
            else:
                self.buffer.display_text([
                    'You have launched the editor in debug mode...',
                    '',
                    'Press any key to continue.'
                ])
        if self.args.read_only:
            self.buffer.display_text([
                'The editor has been opened in read only mode. Press any key to continue.'
            ])
        self.display()
        while True:
            key = self.get_key()
            if key == '`' and self.debug_mode:
                sys.exit(0)
            elif key == 'KEY_RESIZE':
                self.buffer.update_screen_size()
                self.resize_screen()
            elif self.mode == MODE_COMMAND:
                self.parse_command(key)
            elif self.mode == MODE_INSERT:
                self.parse_insert(key)
            elif self.mode == MODE_SELECT:
                self.parse_select(key)
            self.display()

    def parse_general_command(self, command):
        """Executes a general command in all command modes. Returns true if command was found."""
        if command == 'i':
            self.text_selected = False
            self.mode = MODE_INSERT
        elif command == 's':
            if self.args.read_only:
                self.buffer.display_text([
                    'This file cannot be written to. The editor may have been launched in read only mode.'
                ])
                return
            if self.debug_mode:
                res = self.buffer.display_confirm(
                    'Confirm that you want to save the file (type \'save\'): ',
                    'save'
                )
                if not res:
                    # return without confirmation
                    # True means that the command was found as a general command
                    return True
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
            self.mode = MODE_SELECT
            self.select_start_pos = self.caret.copy()
            self.select_end_pos = self.caret.copy()
            self.text_selected = True
            self.last_selection_before = True
        else:
            return False
        return True

    def parse_command(self, key):
        if key == 'KEY_ESCAPE':
            if not self.state_manager.saved and not self.args.read_only:
                res = self.buffer.display_confirm(
                    'Do you want to quit without saving? (y/n): ',
                    'y'
                )
                if not res:
                    return
            sys.exit(0)
        elif key in ALLOWED_CHARS:
            if len(self.cur_command) < MAX_COMMAND_LENGTH:
                self.cur_command += key
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
                if self.parse_general_command(self.cur_command):
                    pass
                elif self.cur_command == 'x':
                    self.buffer.delete_substr(
                        self.caret.y, self.caret.x, self.caret.x + 1
                    )
                    self.push_state()
                elif self.cur_command == 'z':
                    caret, text = self.state_manager.undo()
                    self.caret = caret.copy()
                    self.buffer.load_text(text)
                elif self.cur_command == 'y':
                    caret, text = self.state_manager.redo()
                    if caret is not None and text is not None:
                        self.caret = caret.copy()
                        self.buffer.load_text(text)
            finally:
                self.cur_command = ''

    def parse_insert(self, key):
        if key == 'KEY_ESCAPE':
            self.mode = MODE_COMMAND
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
        elif key in ALLOWED_CHARS:
            # allowed text characters
            self.buffer.insert(self.caret.y, self.caret.x, key)
            self.caret.x += 1 
            self.push_state()

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
        if key == 'KEY_ESCAPE':
            self.text_selected = False
            self.mode = MODE_COMMAND
        elif key in ALLOWED_CHARS:
            if len(self.cur_command) < MAX_COMMAND_LENGTH:
                self.cur_command += key
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
                if self.parse_general_command(self.cur_command):
                    pass
                elif self.cur_command == 'x':
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
                    self.mode = MODE_COMMAND
                    self.text_selected = False
                    self.push_state()
                elif self.cur_command == 'z':
                    caret, text = self.state_manager.undo()
                    self.caret = caret.copy()
                    self.buffer.load_text(text)
                    self.mode = MODE_COMMAND
                    self.text_selected = False
                elif self.cur_command == 'y':
                    caret, text = self.state_manager.redo()
                    if caret is not None and text is not None:
                        self.caret = caret.copy()
                        self.buffer.load_text(text)
                        self.mode = MODE_COMMAND
                        self.text_selected = False
            finally:
                self.cur_command = ''

if __name__ == '__main__':
    print('This is a helper file used by the editor. If you are looking to open the editor, try dim.py.')
