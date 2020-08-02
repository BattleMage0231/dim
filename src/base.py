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

    def parse_general_command(self, command):
        if command == 'i':
            # change to insert mode
            return MODE_INSERT
        elif command == 's':
            if self.args.read_only:
                self.buffer.display_text([
                    'This file cannot be written to. The editor may have been launched in read only mode.'
                ])
                return self.name
            if self.debug_mode:
                res = self.buffer.display_confirm(
                    'Confirm that you want to save the file (type \'save\'): ',
                    'save'
                )
                if not res:
                    # return without confirmation
                    return self.name
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
            return MODE_SELECT
        else:
            return None
        return self.name
    
    def parse_command(self, command):
        raise NotImplementedError('no instances of the mode.base.Mode Base class should exist')

    def parse_key(self, key):
        raise NotImplementedError('no instances of the mode.base.Mode class should exist')
