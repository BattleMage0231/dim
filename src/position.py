class Position:
    def __init__(self, y = None, x = None):
        self.y = y
        self.x = x

    def move_left(self, grid, spaces = 1):
        if not grid:
            return
        self.x -= spaces
        if self.x >= 0:
            return
        while self.x < 0 and self.y > 0:
            self.y -= 1
            if len(grid[self.y]) == 0:
                self.x += 1
            else:
                self.x += len(grid[self.y])
        if self.y < 0 or self.x < 0:
            self.y = self.x = 0
        else:
            self.x += min(1, len(grid[self.y]))

    def move_right(self, grid, spaces = 1):
        if not grid:
            return
        self.x += spaces
        if self.x <= len(grid[self.y]):
            return
        while self.y < len(grid) - 1 and spaces > 0:
            self.y += 1
            if len(grid[self.y]) == 0:
                spaces -= 1
            else:
                spaces -= len(grid[self.y])
        if self.y >= len(grid):
            self.y = len(grid) - 1
            self.x = len(grid[self.y])
        else:
            self.x = max(0, spaces + len(grid[self.y]) - 1)

    def move_up(self, grid, spaces = 1):
        if not grid:
            return
        self.y -= spaces
        if self.y < 0:
            self.y = 0
        self.x = min(len(grid[self.y]), self.x)

    def move_down(self, grid, spaces = 1):
        if not grid:
            return
        self.y += spaces
        if self.y >= len(grid):
            self.y = len(grid) - 1
        self.x = min(len(grid[self.y]), self.x)

    def is_before(self, other):
        return self < other

    def is_after(self, other):
        return self > other

    def is_between(self, first, second):
        """Returns true if the position is in the range [first, second]""" 
        return first <= self <= second

    def copy(self):
        return Position(self.y, self.x)

    def __eq__(self, other):
        return (self.y, self.x) == (other.y, other.x)
    
    def __ne__(self, other):
        return (self.y, self.x) != (other.y, other.x)

    def __lt__(self, other):
        return (self.y, self.x) < (other.y, other.x)

    def __gt__(self, other):
        return (self.y, self.x) > (other.y, other.x)

    def __le__(self, other):
        return (self.y, self.x) <= (other.y, other.x)

    def __ge__(self, other):
        return (self.y, self.x) >= (other.y, other.x)

    def __hash__(self):
        return hash((self.y, self.x))

    def __repr__(self):
        return f'({self.y}, {self.x})'