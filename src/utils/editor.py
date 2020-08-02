import os
import sys
import time
import traceback
from curses import *

import mode.command as command_mode
import mode.insert as insert_mode
import mode.select as select_mode
from utils.buffer import Buffer
from utils.keys import normalize_key, is_char
from utils.position import Position, NULL_POS
from utils.state import StateManager

### TODO add syntax highlighting (highlighting overrides syntax highlighting) ###

class Editor:
    def __init__(self, stdscr, args):
        self.args = args
        self.debug_mode = args.debug
        self.script_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
        # set initial values
        self.buffer = Buffer(stdscr)
        self.state_manager = StateManager()
        self.caret = Position(0, 0)
        self.scr_topleft = Position(0, 0) # inclusive
        self.scr_bottomright = Position(self.buffer.get_height() - 2, self.buffer.get_width() - 1) # inclusive
        self.file_name = 'None'
        self.mode = None
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

    def sync(self):
        """
        Syncs some variables between this object and its Mode object.
        """
        self.buffer = self.mode.buffer
        self.state_manager = self.mode.state_manager
        self.caret = self.mode.caret
        self.file_name = self.mode.file_name
        self.args = self.mode.args
        self.script_dir = self.mode.args
        self.debug_mode = self.mode.debug_mode

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
        self.sync()
        self.buffer.flush(
            self.buffer.get_header(
                self.file_name,
                self.mode.name,
                self.mode.cur_command if type(self.mode) in [command_mode.CommandMode, select_mode.SelectMode] else ''
            ),
            self.caret,
            self.mode.select_start_pos if type(self.mode) == select_mode.SelectMode else None,
            self.mode.select_end_pos if type(self.mode) == select_mode.SelectMode else None,
            self.scr_topleft,
            self.scr_bottomright
        )

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
        self.mode = command_mode.CommandMode(
            self.buffer, self.state_manager, self.caret, self.file_name, self.args
        )
        self.display()
        while True:
            key = self.get_key()
            if key == '`' and self.debug_mode:
                sys.exit(0)
            elif key == 'KEY_RESIZE':
                self.buffer.update_screen_size()
                self.resize_screen()
            else:
                self.mode = self.mode.parse_key(key)
                self.sync()
            self.display()
