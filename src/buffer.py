class Buffer:
    def __init__(self):
        self.matrix = ['']
        self.highlight_start = None
        self.highlight_end = None

    def delete(self, y, x, num = 1):
        """Deletes some number of characters on one line"""
        line = self.matrix[y]
        line = line[ : x] + line[x + num : ]
        self.matrix[y] = line

    def insert(self, y, x, text):
        line = self.matrix[y]
        line = line[ : x] + text + line[x : ]
        self.matrix[y] = line 

    def display(self, stdscr, topleft, bottomright):
        """Displays to the given screen"""