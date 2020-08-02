import os

MAX_COMMAND_LENGTH = 20

# mode constants
MODE_COMMAND = 'COMMAND'
MODE_INSERT = 'INSERT'
MODE_SELECT = 'SELECT'

class Mode:
    def __init__(self, buffer, state_manager, caret, file_name, args):
        self.buffer = buffer
        self.state_manager = state_manager
        self.caret = caret
        self.file_name = file_name
        self.args = args
        # set up
        self.script_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
        self.debug_mode = args.debug

    def get_properties(self):
        return (self.buffer, self.state_manager, self.caret, self.file_name, self.args)

    def push_state(self):
        self.state_manager.push_state(self.caret, self.buffer.get_content())
    
    def parse_command(self, command):
        raise NotImplementedError('no instances of the mode.base.Mode Base class should exist')

    def parse_key(self, key):
        raise NotImplementedError('no instances of the mode.base.Mode class should exist')
