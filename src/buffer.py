from curses import *

from keys import *
from position import *

COLORS = [
    (1, 7, 233),
    (2, 7, 237),
    (3, 221, 237),
    (4, 200, 237),
    (5, 35, 237),
    (6, 150, 237),
    (7, 233, 7)
]

class Buffer:
    def __init__(self, stdscr):
        # set initial values
        self.stdscr = stdscr
        self.lines = ['']
        self.height, self.width = stdscr.getmaxyx()
        # load colors
        start_color()
        use_default_colors()
        for color in COLORS:
            init_pair(*color)
        # set background
        stdscr.bkgd(' ', color_pair(1) | A_BOLD)

    def load_text(self, text):
        self.lines = text.split('\n')

    def get_content(self):
        return '\n'.join(self.lines)

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def get_text_height(self):
        return len(self.lines)
    
    def get_line_length(self, y):
        return len(self.lines[y])

    def get_max_line_length(self):
        return max([len(i) for i in self.lines])

    def update_screen_size(self):
        self.height, self.width = self.stdscr.getmaxyx()

    def delete_substr(self, y, x1, x2):
        """Deletes some number of characters on one line, from x1 to x2 [inclusive, exclusive)"""
        self.lines[y] = self.lines[y][ : x1] + self.lines[y][x2 : ]

    def get_substr(self, y, x1, x2):
        """Gets a substring of a line, from x1 to x2 [inclusive, exclusive)"""
        return self.lines[y][x1 : x2]

    def insert(self, y, x, text):
        """Inserts some text at lines[y][x]"""
        self.lines[y] = self.lines[y][ : x] + text + self.lines[y][x : ]

    def join(self, y1, y2):
        self.lines[y1] += self.lines[y2]
        self.pop_line(y2)

    def get_line(self, y):
        return self.lines[y][ : ]

    def get_lines(self):
        return self.lines[:]

    def pop_line(self, y):
        self.lines.pop(y) 

    def insert_line(self, y, text = ''):
        self.lines.insert(y, text)

    def split_line(self, y, x):
        dif = self.get_substr(y, x, None) # None = to end of line
        self.lines[y] = self.get_substr(y, 0, x)
        self.insert_line(y + 1, dif)
        
    def get_header(self, file_name, mode, cur_command):
        self.update_screen_size()
        justified_left = [
            (' Dim',                        3), 
            (' ' * 8,                       2),
            ('Editing ' + file_name,        4),
            (' ' * 20,                      2),
            (cur_command,                   6),
        ]
        justified_right = [
            ('Mode: ' + mode,               5),
            (' ' * 10,                      2),
        ]
        padding = (self.width - sum([len(i) for i, j in (justified_left + justified_right)]))
        return justified_left + [(' ' * padding, 2)] + justified_right + [('─' * self.width, 2)]

    def get_key(self):
        return normalizekey(self.stdscr.getkey())

    def display_text(self, text):
        """Displays an array of strings to the screen. Waits for user input before continuing"""
        self.update_screen_size()
        self.stdscr.erase()
        self.stdscr.addstr(' ' + text[0] + '\n ')
        for line in text[1 : ]:
            self.stdscr.addstr(line)
            self.stdscr.addstr('\n ')
        self.get_key()

    def display_prompt(self, text):
        """
        Displays a line of text to the screen and awaits a line of input, which is returned.
        """
        self.stdscr.erase()
        self.stdscr.addstr(' ' + text + '\n ')
        self.stdscr.refresh()
        key = self.get_key()
        res = ''
        while key != 'KEY_NEWLINE':
            self.stdscr.erase()
            self.stdscr.addstr(' ' + text)
            if key == 'KEY_BACKSPACE':
                res = res[ : -1]
            elif ischar(key):
                res += key
            self.stdscr.addstr('\n ' + res)
            key = self.get_key()
        return res

    def display_confirm(self, text, password):
        """
        Displays a line of text to the screen and awaits a case-sensitive password.
        Returns true if the password is equal to the given password.
        """
        return self.display_prompt(text) == password

    def display_choose(self, text, choices):
        """
        Displays an array of strings to the screen and awaits a choice of the options.
        Returns the index of the choice (0-indexed).
        """
        cur_index = 0
        key = None
        while key != 'KEY_NEWLINE':
            if key == 'KEY_UP':
                cur_index -= 1
                cur_index = max(cur_index, 0)
            elif key == 'KEY_DOWN':
                cur_index += 1
                cur_index = min(cur_index, len(choices) - 1)
            self.stdscr.erase()
            for line in text:
                self.stdscr.addstr(' ' + line + '\n')
            for index, value in enumerate(choices):
                self.stdscr.addstr('\n ')
                self.stdscr.addstr(value, color_pair(7 if index == cur_index else 1))
            self.stdscr.addstr('\n\n ') 
            key = self.get_key()  
        return cur_index 

    def flush(self, header, caret, select_start_pos, select_end_pos, scr_topleft, scr_bottomright):
        """Displays buffer to the screen"""
        self.update_screen_size()
        self.stdscr.erase()
        # header
        for text, color in header:
            self.stdscr.addstr(text, color_pair(color))
        text_selected = select_start_pos is not None
        # display lines
        displayed_lines = self.lines[scr_topleft.y : min(len(self.lines), scr_bottomright.y)]
        for index, line in enumerate(displayed_lines):
            self.stdscr.addstr(' ')
            if len(line) >= scr_topleft.x:
                # inclusive, position of line start and line end of displayed line
                ln_start = Position(scr_topleft.y + index, scr_topleft.x)
                ln_end = Position(scr_topleft.y + index, scr_topleft.x + self.width - 1)
                displayed_line = line[ln_start.x : min(len(line), scr_bottomright.x - 1)]
                if text_selected:
                    # whether start position and end position of line are between selection
                    start_between = ln_start.is_between(select_start_pos, select_end_pos)
                    end_between = ln_end.is_between(select_start_pos, select_end_pos)
                    # whether selection is between start and end position
                    select_start_between = select_start_pos.is_between(ln_start, ln_end)
                    select_end_between = select_end_pos.is_between(ln_start, ln_end)
                    if start_between and end_between:
                        # completely enclosed
                        self.stdscr.addstr(displayed_line, color_pair(7))
                    elif start_between:
                        # only start between selection
                        # end is on same line
                        # only starting portion is highlighted
                        self.stdscr.addstr(displayed_line[ : select_end_pos.x - ln_start.x + 1], color_pair(7))
                        self.stdscr.addstr(displayed_line[select_end_pos.x - ln_start.x + 1 : ])
                    elif end_between:
                        # only end between selection
                        # start is on same
                        # only ending portion is highlighted
                        self.stdscr.addstr(displayed_line[ : select_start_pos.x - ln_start.x])
                        self.stdscr.addstr(displayed_line[select_start_pos.x - ln_start.x : ], color_pair(7))
                    elif select_start_between and select_end_between:
                        # selection is all on this line
                        # start and end not highlighted
                        self.stdscr.addstr(displayed_line[ : select_start_pos.x - ln_start.x])
                        self.stdscr.addstr(
                            displayed_line[select_start_pos.x - ln_start.x : select_end_pos.x - ln_start.x + 1],
                            color_pair(7)
                        )
                        self.stdscr.addstr(displayed_line[select_end_pos.x + 1  - ln_start.x : ])
                    else:
                        # not enclosed by selection at all
                        self.stdscr.addstr(displayed_line)
                else:
                    self.stdscr.addstr(displayed_line)
            if index != len(displayed_lines) - 1:
                self.stdscr.addstr('\n')
        self.stdscr.move(caret.y - scr_topleft.y + 2, caret.x - scr_topleft.x + 1)
