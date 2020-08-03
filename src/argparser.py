import argparse
import hashlib
import os

class Argparser:
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    TUTORIAL_DIR = os.path.join(SCRIPT_DIR, 'tutorial')
    TUTORIAL_LEN = len(os.listdir(TUTORIAL_DIR)) if os.path.exists(TUTORIAL_DIR) else 0

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument(
            'file',
            nargs = '?',
            default = None,
            help = 'path to the file being edited'
        )
        parser.add_argument(
            '-g', '--debug',
            help = 'launch the editor in debug mode',
            action = 'store_true'
        )
        parser.add_argument(
            '-t', '--tutorial',
            help = 'displays tutorial file at provided index',
            type = int,
            choices = range(1, Argparser.TUTORIAL_LEN + 1)
        )
        parser.add_argument(
            '--read-only',
            help = 'indicate that the file cannot be written to',
            action = 'store_true'
        )
        return parser.parse_args()

    @staticmethod
    def get_args():
        args = Argparser.parse_args()
        res = type('config', (), {})
        if args.tutorial is None:
            for attr in ['file', 'debug', 'read_only']:
                setattr(res, attr, getattr(args, attr) if hasattr(args, attr) else None)
            res.tutorial = None
        else:
            res.debug = True if (hasattr(args, 'debug') and args.debug) else None
            file_hash = hashlib.md5(str(args.tutorial).encode()).hexdigest()
            file_path = os.path.join(Argparser.TUTORIAL_DIR, file_hash)
            if not (os.path.isdir(Argparser.TUTORIAL_DIR or os.path.isfile(file_path))):
                print('The tutorial directory or file was not found!\n')
                sys.exit(1)
            res.file = file_path
            res.read_only = True
        return res
