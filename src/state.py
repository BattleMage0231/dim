import zlib

class StateManager:
    def __init__(self):
        self.saved = True
        self.undo_stack = []
        self.undo_ptr = -1

    def compress_text(self, text):
        return zlib.compress(text.encode('utf8'))

    def decompress_text(self, text):
        return zlib.decompress(text).decode('utf8')

    def push_state(self, caret, text):
        self.saved = False
        self.undo_stack = self.undo_stack[ : self.undo_ptr + 1]
        self.undo_ptr += 1
        self.undo_stack.append((caret.copy(), self.compress_text(text)))

    def undo(self):
        self.saved = False
        self.undo_ptr = max(0, self.undo_ptr - 1)
        caret, compressed = self.undo_stack[self.undo_ptr]
        return (caret, self.decompress_text(compressed))

    def redo(self):
        if self.undo_ptr + 1 < len(self.undo_stack):
            self.saved = False
            self.undo_ptr += 1
            caret, compressed = self.undo_stack[self.undo_ptr]
            return (caret, self.decompress_text(compressed))
        return None, None

    def clear_stack(self):
        self.undo_ptr = -1
        self.undo_stack = []
        self.saved = True
