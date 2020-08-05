import os
import sys

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
        if self.args.allow_state:
            self.state_manager.push_state(self.caret, self.buffer.get_content())

    def parse_args(self, command):
        """
        Parses the arguments of a command.
        Commands are of the form KEYWORD[ARG1][ARG2][ARG3].
        """
        try:
            start = command.find('[')
            if start == -1:
                return (command.strip(), [])
            base_cmd = command[ : start].strip()
            assert base_cmd # base command must not be empty
            args = []
            while start > -1:
                end = command.index(']', start + 1) # throw exception if not found
                args.append(command[start + 1 : end])
                start = command.find('[', end + 1)
            return (base_cmd, args)
        except:
            # bracket mismatch
            return ('', [])

    def parse_general_command(self, command, args = []):
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
                if args:
                    self.args.file = args[0]
                else:
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
        elif command == 'z':
            if not self.args.allow_state:
                return MODE_COMMAND
            caret, text = self.state_manager.undo()
            self.caret = caret.copy()
            self.buffer.load_text(text)
            return MODE_COMMAND
        elif command == 'y':
            if not self.args.allow_state:
                return MODE_COMMAND
            caret, text = self.state_manager.redo()
            if caret is not None and text is not None:
                self.caret = caret.copy()
                self.buffer.load_text(text)
                return MODE_COMMAND
        else:
            return None
        return self.name
    
    def parse_command(self, command):
        raise NotImplementedError('no instances of the mode.base.Mode Base class should exist')

    def parse_key(self, key):
        raise NotImplementedError('no instances of the mode.base.Mode class should exist')
