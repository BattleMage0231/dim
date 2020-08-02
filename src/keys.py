KEY_DICT = {
    # escape
    chr(27): 'KEY_ESCAPE',
    # backspace
    '\b': 'KEY_BACKSPACE',
    # left arrow
    'KEY_B1': 'KEY_LEFT',
    chr(452): 'KEY_LEFT',
    # right arrow
    'KEY_B3': 'KEY_RIGHT',
    chr(454): 'KEY_RIGHT',
    # up arrow,
    'KEY_A2': 'KEY_UP',
    chr(450): 'KEY_UP',
    # down arrow
    'KEY_C2': 'KEY_DOWN',
    chr(456): 'KEY_DOWN',
    # page up
    'KEY_PPAGE': 'KEY_PAGE_UP',
    'KEY_A3': 'KEY_PAGE_UP',
    chr(451): 'KEY_PAGE_UP',
    # page down
    'KEY_NPAGE': 'KEY_PAGE_DOWN',
    'KEY_C3': 'KEY_PAGE_DOWN',
    chr(457): 'KEY_PAGE_DOWN',
    # home
    'KEY_A1': 'KEY_HOME',
    chr(449): 'KEY_HOME',
    # end
    'KEY_C1': 'KEY_END',
    chr(455): 'KEY_END',
    # enter/return
    '\n': 'KEY_NEWLINE',
    chr(13): 'KEY_NEWLINE',
    # tab
    '\t': 'KEY_TAB'
}

def normalizekey(key):
    """Generates a consistent key name for key."""
    return KEY_DICT[key] if key in KEY_DICT else key

def ischar(key):
    return key.isprintable() and len(key) == 1