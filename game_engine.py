# =============================================================================
# Beetle Battle - Game Engine Module
# By Fred Dijkstra
# (c) 2023 - Computerguided Systems B.V.
# =============================================================================

# =============================================================================
# Imports
# =============================================================================
from typing import Protocol

# =============================================================================
# Protocol: GameGuiProtocol
# This protocol defines the methods that the game model can call on the GUI.
# =============================================================================

class GameGuiProtocol(Protocol):

    # -------------------------------------------------------------------------
    # Method: turn_changed
    # This method is called by the model to indicate that the turn has changed.
    # -------------------------------------------------------------------------
    def turn_changed(self, color: str) -> None:
        ...

    # -------------------------------------------------------------------------
    # Method: beetle_moved
    # This method is called by the model to indicate that a beetle jumped to
    # the square at the indicated location.
    # -------------------------------------------------------------------------
    def beetle_moved(self, 
                     source_row: int, source_column: int,
                     destination_row: int, destination_colum: int) -> None:
        ...

    # -------------------------------------------------------------------------
    # Method: new_beetle_added
    # This method is called by the model to indicate that a new beetle was
    # added at the indicated square.
    # -------------------------------------------------------------------------
    def new_beetle_added(self, beetle_id: int, color: str, row: int, column: int) -> None:
        ...

    # -------------------------------------------------------------------------
    # Method: set_square_color
    # This method is called by the model to indicate that the color of the
    # indicated square should be changed.
    # -------------------------------------------------------------------------
    def set_square_color(self, row: int, column: int, color: str) -> None:
        ...

    # -------------------------------------------------------------------------
    # Method: announce_winner
    # This method is called by the model to indicate that the game is over
    # and the indicated player won.
    # -------------------------------------------------------------------------
    def announce_winner(self, color: str) -> None:
        ...

# =============================================================================
# Classes
# =============================================================================

# -----------------------------------------------------------------------------
# Class: Location
# A location indicates the row and column on a grid of squares.
# -----------------------------------------------------------------------------
class Location:
    row = 0
    column = 0

    # -------------------------------------------------------------------------
    def __init__(self, row, column):
        self.row = row
        self.column = column

# -----------------------------------------------------------------------------
# Class: Beetle
# A beetle has a certain color (i.e. "red" or "blue") and a location.
# In case the beetle is jumping, it also has a destination.
# -----------------------------------------------------------------------------
class Beetle:
    color = None
    location = None
    destination = None
    circle = None
    id = None

    # -------------------------------------------------------------------------
    def __init__(self, color, location, id):
        self.color = color
        self.location = location
        self.destination = None
        self.id = id

    # -------------------------------------------------------------------------
    def prepare_jump(self, destination):
        self.destination = destination

    # -------------------------------------------------------------------------
    def jump(self):
        self.location = self.destination
        self.destination = None

    # -------------------------------------------------------------------------
    def set_color(self, color):
        self.color = color

# -----------------------------------------------------------------------------
# Class: Square
# A square has a location and a capacity.
# The capacity corresponds to the number of neighboring squares.
# It also has a list of beetles. The number of beetles in that list can be 0 to 
# its capacity.
# -----------------------------------------------------------------------------
class Square:
    capacity = 0
    location = None
    beetles = []

    def __init__(self, location):

        self.location = location
        self.beetles = []

    # -------------------------------------------------------------------------
    # Method: get_color
    # This method returns the color of the beetles in the square. If there
    # are no beetles in the square, then it returns "white".
    # -------------------------------------------------------------------------
    def get_color(self):
            if len(self.beetles) == 0:
                return "white"
            else:
                return self.beetles[0].color

    # -------------------------------------------------------------------------
    # Method: add_beetle
    # This method takes a beetle and adds it to the square. The color of the
    # beetles in the square is set by the color of the beetle that is added.
    # -------------------------------------------------------------------------
    def add_beetle(self, new_beetle):
        self.beetles.append(new_beetle)
        for beetle in self.beetles:
            beetle.set_color(new_beetle.color)

    # -------------------------------------------------------------------------
    # Method: remove_beetle
    # This method takes a beetle and removes it from the square.
    # -------------------------------------------------------------------------
    def remove_beetle(self, beetle):
        self.beetles.remove(beetle)

    # -------------------------------------------------------------------------
    # Method: check_jumping_beetles
    # This method determines whether or not the beetles on the square are
    # jumping.
    # -------------------------------------------------------------------------
    def check_jumping_beetles(self):
        for beetle in self.beetles:
            if beetle.destination is not None:
                return True
        return False

# -----------------------------------------------------------------------------
# Class: Board
# The board has a dimension N and is an NxN matrix that stores the squares.
# Therefore, a square can be identified by its location which corresponds to 
# the row and column in that matrix.
# -----------------------------------------------------------------------------
class Board:
    dimension = 0
    squares = []
    rectangles = []
    beetles = []

    # -------------------------------------------------------------------------
    # Constructor
    # The constructor takes the dimension of the board and creates the squares.
    # The capacity of each square is determined by the number of neighboring
    # squares.
    # -------------------------------------------------------------------------
    def __init__(self, dimension):
        self.dimension = dimension
        self.squares = []
        self.beetles = []
        for row in range(dimension):
            for column in range(dimension):
                square = Square(Location(row, column))
                location = Location(row, column)
                neighboring_locations = get_neighboring_locations(dimension, location)
                square.capacity = len(neighboring_locations)
                self.squares.append(square)

    # -------------------------------------------------------------------------
    # Method: get_square_by_location
    # This method takes a location and returns the square at that location.
    # -------------------------------------------------------------------------
    def get_square_by_location(self, row, column):
        location = Location(row, column)
        return self.squares[location.row * self.dimension + location.column]
    
    # -------------------------------------------------------------------------
    # Method: get_empty_squares
    # This method returns the list of squares that have no beetles.
    # -------------------------------------------------------------------------
    def get_empty_squares(self):
        empty_squares = []
        for square in self.squares:
            if len(square.beetles) == 0:
                empty_squares.append(square)
        return empty_squares

    # -------------------------------------------------------------------------
    # Method: get_squares_by_color
    # This method takes a color and returns the list of squares that have a
    # beetle of that color.
    # -------------------------------------------------------------------------
    def get_squares_by_color(self, color):
        found_squares = []
        for square in self.squares:
            if square.get_color() == color:
                found_squares.append(square)
        return found_squares
        
    # -------------------------------------------------------------------------
    # Method: place_new_beetle
    # This method takes a color and a location and places a new beetle of that
    # color at that location.
    # -------------------------------------------------------------------------
    def place_new_beetle(self, color, location):
        square = self.get_square_by_location(location.row, location.column)
        beetle = Beetle(color, location, len(self.beetles) )
        self.beetles.append(beetle)
        self.add_beetle(beetle, square)
        return beetle

    # -------------------------------------------------------------------------
    # Method: add_beetle
    # This method takes a beetle and adds it to the specified square. If the
    # square becomes fully filled, then the beetles are prepared to jump to
    # the neighboring squares.
    # -------------------------------------------------------------------------
    def add_beetle(self, beetle, square):
        square.beetles.append(beetle)

# -----------------------------------------------------------------------------
# Class: Game
# The game has a board and a list of beetles that are about to jump.
# -----------------------------------------------------------------------------
class Game:
    board = None
    beetles_to_jump = []
    turn = None
    moves = []
    gui : GameGuiProtocol = None

    # -------------------------------------------------------------------------
    # Constructor
    # The constructor takes the dimension of the board and creates the board.
    # -------------------------------------------------------------------------
    def __init__(self, dimension, gui: GameGuiProtocol = None):
        self.gui = gui
        self.board = Board(dimension)
        self.beetles_to_jump = []
        self.turn = "red"
        self.gui.turn_changed(self.turn)
        self.moves = []

    # -------------------------------------------------------------------------
    # Method: check_move
    # This method takes a location and checks if the move is valid given the
    # current turn.
    # -------------------------------------------------------------------------
    def check_move(self, location):

        # Check if the game is over.
        if self.get_winner() is not None:
            # No move is allowed if the game is over.
            return False

        # Get the square at the specified location.
        square = self.board.get_square_by_location(location.row, location.column)

        # Get the empty squares.
        empty_squares = self.board.get_empty_squares()

        # Get the squares that have beetles of the current turn's color.
        squares_with_current_turn_color = self.board.get_squares_by_color(self.turn)

        # Check if the square at the specified location is is part of the empty 
        # squares or the squares that have beetles of the current turn's color.
        if square in empty_squares or square in squares_with_current_turn_color:
            return True
        
        # Invalid move.
        return False

    # -------------------------------------------------------------------------
    # Method: do_move
    # This method takes a color and a location and places a new beetle of that
    # color at that location.
    # -------------------------------------------------------------------------
    def do_move(self, row, column):

        # Check if it is a valid move.
        if not self.check_move(Location(row, column)):
            return

        location = Location(row, column)
        color = self.turn

        new_beetle = self.board.place_new_beetle(color, location)
        self.gui.new_beetle_added(new_beetle.id, color, location.row, location.column)

        square = self.board.get_square_by_location(location.row, location.column)
        self.evaluate_square(square)
        self.moves.append((color, location))

        self.transition()

        # If there is a winner, then the game is over.
        winner = self.get_winner()
        if winner is not None:
            self.gui.announce_winner(winner)
            return
        
        if self.turn == "red":
            self.turn = "blue"
        else:
            self.turn = "red"

        self.gui.turn_changed(self.turn)

    # -------------------------------------------------------------------------
    # Method: evaluate_square
    # This method takes a square and if the square is fully filled, then the
    # beetles on the square are prepared to jump to the neighboring squares.
    # -------------------------------------------------------------------------
    def evaluate_square(self, square):

        # Determine the number of not jumping beetles on the square.
        not_jumping_beetles = 0
        for beetle in square.beetles:
            if beetle.destination is None:
                not_jumping_beetles += 1

        # If the square is fully filled and all beetles are not jumping, then
        # prepare the beetles to jump to the neighboring squares.
        if not_jumping_beetles == square.capacity:
            neighboring_locations = get_neighboring_locations(self.board.dimension, square.location)
            for index, location in enumerate(neighboring_locations):
                square.beetles[index].prepare_jump(location)
                self.beetles_to_jump.append(square.beetles[index])

    # -------------------------------------------------------------------------
    # Method: transition
    # This method performs the transition of the game between two moves.
    # To do this it loops through the list of beetles that are about to jump and
    # make them jump to their destination when possible. If a beetle cannot jump, 
    # then the next beetle is considered. If the beetle can jump, then the beetle
    # is removed from the list of beetles that are about to jump and moved
    # to the destination square.
    # -------------------------------------------------------------------------
    def transition(self):

        # The number of skipped beetle jumps is used to keep track of the number
        # of beetles that are skipped because they cannot jump to the destination.
        skipped_beetle_jumps = 0

        # Check if there is a winner.
        game_over = self.get_winner() is not None

        # Loop through the list of beetles that are about to jump until there
        # are no beetles left or until there is a winner.
        while len(self.beetles_to_jump) > 0 and not game_over:

            beetle = self.beetles_to_jump[skipped_beetle_jumps]
            destination = beetle.destination
            destination_square = self.board.get_square_by_location(destination.row, destination.column)

            # If the destination square is not fully filled, 
            # then the beetle can jump to the destination square.
            if len(destination_square.beetles) < destination_square.capacity:

                # Make the beetle jump to the destination square.
                self.make_beetle_jump(beetle)

                # Reset the number of skipped beetle jumps to start
                # considering the beetle at the beginning of the list again.
                skipped_beetle_jumps = 0
            else:
                # If the destination square is fully filled, then the beetle
                # cannot jump to the destination square. Therefore, the beetle
                # has to wait until there is room. Therefore, the beetle
                # is skipped for now and the next beetle is considered.
                skipped_beetle_jumps += 1

            # If there is a winner, then the game is over.
            game_over = self.get_winner() is not None

    # -------------------------------------------------------------------------
    # Method: make_beetle_jump
    # This method takes a beetle and a destination and makes the beetle jump
    # to the destination.
    # -------------------------------------------------------------------------
    def make_beetle_jump(self, beetle):

        current_square = self.board.get_square_by_location(beetle.location.row, beetle.location.column)
        destination_square = self.board.get_square_by_location(beetle.destination.row, beetle.destination.column)

        # The beetle is no longer about to jump so it is removed from the list.
        self.beetles_to_jump.remove(beetle)

        beetle.jump()
        original_destination_color = destination_square.get_color()

        current_square.remove_beetle(beetle)
        destination_square.add_beetle(beetle)

        self.gui.beetle_moved( current_square.location.row, current_square.location.column,
            destination_square.location.row, destination_square.location.column )

        # If the square was conquered, then the color of the beetles was changed.
        if original_destination_color != destination_square.get_color():
            for square_beetle in destination_square.beetles:
                if square_beetle != beetle:
                    self.gui.set_beetle_color( square_beetle.id, beetle.color)


        self.evaluate_square(destination_square)
           
    # -------------------------------------------------------------------------
    # Method: get_winner
    # This method checks if there is a winner, which can only be the case from
    # move 3 onwards. It checks if there are any red squares left or any blue
    # squares left. If there are no red squares left, then blue wins. If there
    # are no blue squares left, then red wins. Otherwise, there is no winner.
    # If there is a winner, then it
    # returns the color of the winner. Otherwise, it returns None.
    # -------------------------------------------------------------------------
    def get_winner(self):

        # There can only be a winner from move 3 onwards.
        if len(self.moves) < 3:
            return None
        
        # Get the red squares and blue squares.
        red_squares = self.board.get_squares_by_color("red")
        blue_squares = self.board.get_squares_by_color("blue")

        # If there are no red squares left, then blue wins.
        if len(red_squares) == 0:
            return "blue"
        
        # If there are no blue squares left, then red wins.
        if len(blue_squares) == 0:
            return "red"
        
        # Otherwise, there is no winner.
        return None
    
    # -----------------------------------------------------------------------------
    # Method: reset_game
    # This method resets the game by creating a new game with the specified
    # dimension.
    # -----------------------------------------------------------------------------
    def reset_game(self):
        self.__init__(self.board.dimension, self.gui)

# =============================================================================
# Data manipulation functions
# =============================================================================

# -----------------------------------------------------------------------------
# Function: get_capacity
# This function determines the neighboring locations of a square at a certain 
# location. It takes the dimension of the board and the location of the square and returns
# the list of neighboring locations.
# -----------------------------------------------------------------------------
def get_neighboring_locations(dimension, location):

    neighboring_locations = []
    row = location.row
    column = location.column

    # Check if the square is on the top row
    if row > 0:
        neighboring_locations.append(Location(row - 1, column))

    # Check if the square is on the bottom row
    if row < dimension - 1:
        neighboring_locations.append(Location(row + 1, column))

    # Check if the square is on the left column
    if column > 0:
        neighboring_locations.append(Location(row, column - 1))

    # Check if the square is on the right column
    if column < dimension - 1:
        neighboring_locations.append(Location(row, column + 1))

    return neighboring_locations

# =============================================================================