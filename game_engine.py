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
    # GameGuiProtocol method: turn_changed
    # This method is called by the model to indicate that the turn has changed.
    # -------------------------------------------------------------------------
    def turn_changed(self, sender, color: str) -> None:
        ...

    # -------------------------------------------------------------------------
    # GameGuiProtocol method: beetle_moved
    # This method is called by the model to indicate that a beetle jumped to
    # the square at the indicated location.
    # -------------------------------------------------------------------------
    def beetle_moved(self, sender,
                     source_row: int, source_column: int,
                     destination_row: int, destination_column: int) -> None:
        ...

    # -------------------------------------------------------------------------
    # GameGuiProtocol method: new_beetle_added
    # This method is called by the model to indicate that a new beetle was
    # added at the indicated square.
    # -------------------------------------------------------------------------
    def new_beetle_added(self, sender,
                         beetle_id: int, color: str, row: int, column: int) -> None:
        ...

    # -------------------------------------------------------------------------
    # GameGuiProtocol method: set_square_color
    # This method is called by the model to indicate that the color of the
    # indicated square should be changed.
    # -------------------------------------------------------------------------
    def set_square_color(self, sender,
                         row: int, column: int, color: str) -> None:
        ...

    # -------------------------------------------------------------------------
    # GameGuiProtocol method: set_beetle_color
    # -------------------------------------------------------------------------
    def set_beetle_color(self, sender,
                         beetle_id: int, color: str) -> None:
        ...

    # -------------------------------------------------------------------------
    # GameGuiProtocol method: announce_winner
    # This method is called by the model to indicate that the game is over
    # and the indicated player won.
    # -------------------------------------------------------------------------
    def announce_winner(self, sender, color: str) -> None:
        ...

# =============================================================================
# Classes
# =============================================================================

# -----------------------------------------------------------------------------
# Class: DummyGui
# This class implements the GameGuiProtocol and can be used as a dummy GUI
# for testing purposes.
# -----------------------------------------------------------------------------
class DummyGui(GameGuiProtocol):
    
        # -------------------------------------------------------------------------
        # DummyGui method: turn_changed
        # -------------------------------------------------------------------------
        def turn_changed(self, sender, color: str) -> None:
            pass
    
        # -------------------------------------------------------------------------
        # DummyGui method: beetle_moved
        # -------------------------------------------------------------------------
        def beetle_moved(self, sender,
                        source_row: int, source_column: int,
                        destination_row: int, destination_column: int) -> None:
            pass    
        # -------------------------------------------------------------------------
        # DummyGui method: new_beetle_added
        # -------------------------------------------------------------------------
        def new_beetle_added(self, sender,
                             beetle_id: int, color: str, row: int, column: int) -> None:
            pass

        # -------------------------------------------------------------------------
        # DummyGui method: set_square_color
        # -------------------------------------------------------------------------
        def set_square_color(self, sender,
                             row: int, column: int, color: str) -> None:
            pass

        # -------------------------------------------------------------------------
        # DummyGui method: announce_winner
        # -------------------------------------------------------------------------
        def announce_winner(self, sender,
                            color: str) -> None:
            pass

# -----------------------------------------------------------------------------
# Class: Location
# A location indicates the row and column on a grid of squares.
# -----------------------------------------------------------------------------
class Location:

    # -------------------------------------------------------------------------
    def __init__(self, row, column):
        self.row    = row
        self.column = column

    # -------------------------------------------------------------------------
    # Location method: __eq__
    # This method compares two locations and returns True if they are equal.
    # -------------------------------------------------------------------------
    def __eq__(self, other):
        return self.row == other.row and self.column == other.column

    # -------------------------------------------------------------------------
    # Location method: deep_copy
    # This method returns a deep copy of the location.
    # -------------------------------------------------------------------------
    def deep_copy(self):
        return Location(self.row, self.column)

# -----------------------------------------------------------------------------
# Class: Move
# A move indicates the color and location of a beetle that is placed on the
# board.
# -----------------------------------------------------------------------------
class Move:

    # -------------------------------------------------------------------------
    def __init__(self, color, location):
        self.color    = color
        self.location = location

    # -------------------------------------------------------------------------
    # Move method: deep_copy
    # This method returns a deep copy of the move.
    # -------------------------------------------------------------------------
    def deep_copy(self):
        return Move(self.color, self.location.deep_copy())

# -----------------------------------------------------------------------------
# Class: Beetle
# A beetle has a certain color (i.e. "red" or "blue") and a location.
# In case the beetle is jumping, it also has a destination.
# -----------------------------------------------------------------------------
class Beetle:

    # -------------------------------------------------------------------------
    # Beetle constructor
    # -------------------------------------------------------------------------
    def __init__(self, color, location, id):
        self.color       = color
        self.location    = location
        self.destination = None
        self.id          = id

    # -------------------------------------------------------------------------
    # Beetle method: deep_copy
    # This method returns a deep copy of the beetle.
    # -------------------------------------------------------------------------
    def deep_copy(self):
        beetle_copy = Beetle(self.color, self.location.deep_copy(), self.id)
        if self.destination is not None:
            beetle_copy.destination = self.destination.deep_copy()
        return beetle_copy

    # -------------------------------------------------------------------------
    # Beetle method: prepare_jump
    # This method takes a destination and prepares the beetle to jump to that
    # destination.
    # -------------------------------------------------------------------------
    def prepare_jump(self, destination):
        self.destination = destination

    # -------------------------------------------------------------------------
    # Beetle method: jump
    # This method makes the beetle jump to the destination.
    # -------------------------------------------------------------------------
    def jump(self):
        self.location = self.destination
        self.destination = None

# -----------------------------------------------------------------------------
# Class: Square
# A square has a location and a capacity.
# The capacity corresponds to the number of neighboring squares.
# It also has a list of beetles. The number of beetles in that list can be 0 to 
# its capacity.
# -----------------------------------------------------------------------------
class Square:

    # -------------------------------------------------------------------------
    # Square constructor
    # -------------------------------------------------------------------------
    def __init__(self, location):
        self.location = location
        self.beetles = []
        self.neighbors = []

    @property
    def color(self):
        return "white" if len(self.beetles) == 0 else self.beetles[0].color
    
    @property
    def capacity(self):
        return len(self.neighbors)

    # -------------------------------------------------------------------------
    # Square method: deep_copy
    # This method returns a deep copy of the square.
    # -------------------------------------------------------------------------
    def deep_copy(self):
        square_copy = Square(self.location.deep_copy())
        square_copy.neighbors = [ neighbor.deep_copy() for neighbor in self.neighbors]
        square_copy.beetles = [ beetle.deep_copy() for beetle in self.beetles]
        return square_copy

    # -------------------------------------------------------------------------
    # Square method: add_beetle
    # This method takes a beetle and adds it to the square. The color of the
    # beetles in the square is set by the color of the beetle that is added.
    # -------------------------------------------------------------------------
    def add_beetle(self, new_beetle):
        for beetle in self.beetles:
            beetle.color = new_beetle.color
        self.beetles.append(new_beetle)

    # -------------------------------------------------------------------------
    # Square method: remove_beetle
    # This method takes a beetle and removes it from the square.
    # -------------------------------------------------------------------------
    def remove_beetle(self, beetle):
        self.beetles.remove(beetle)

    # -------------------------------------------------------------------------
    # Square method: check_jumping_beetles
    # This method determines whether or not the beetles on the square are
    # jumping.
    # -------------------------------------------------------------------------
    def check_jumping_beetles(self):
        return any(beetle.destination is not None for beetle in self.beetles)

# -----------------------------------------------------------------------------
# Class: Board
# The board has a dimension N and is an NxN matrix that stores the squares.
# Therefore, a square can be identified by its location which corresponds to 
# the row and column in that matrix.
# -----------------------------------------------------------------------------
class Board:

    # -------------------------------------------------------------------------
    # Board constructor
    # The constructor takes the dimension of the board and creates the squares.
    # The capacity of each square is determined by the number of neighboring
    # squares.
    # -------------------------------------------------------------------------
    def __init__(self, dimension):
        self.dimension = dimension
        self.squares = []
        for row in range(dimension):
            for column in range(dimension):
                square = Square(Location(row, column))
                location = Location(row, column)
                square.neighbors = self.get_neighboring_locations(location)
                self.squares.append(square)
        self.num_beetles = 0

    # -------------------------------------------------------------------------
    # Board method: deep_copy
    # This method returns a deep copy of the board. 
    # -------------------------------------------------------------------------
    def deep_copy(self):
        board_copy = Board(self.dimension)
        board_copy.squares = [square.deep_copy() for square in self.squares]
        board_copy.num_beetles = self.num_beetles
        return board_copy

    # -------------------------------------------------------------------------
    # Board method: get_square_by_location
    # This method takes a location and returns the square at that location.
    # -------------------------------------------------------------------------
    def get_square_by_location(self, row, column):
        location = Location(row, column)
        return self.squares[location.row * self.dimension + location.column]
    
    # -------------------------------------------------------------------------
    # Board method: get_empty_squares
    # This method returns the list of squares that have no beetles.
    # -------------------------------------------------------------------------
    def get_empty_squares(self):
        return [square for square in self.squares if len(square.beetles) == 0]

    # -------------------------------------------------------------------------
    # Board method: get_squares_by_color
    # This method takes a color and returns the list of squares that have a
    # beetle of that color.
    # -------------------------------------------------------------------------
    def get_squares_by_color(self, color):
        return [square for square in self.squares if square.color == color]
        
    # -------------------------------------------------------------------------
    # Board method: place_new_beetle
    # This method takes a color and a location and places a new beetle of that
    # color at that location.
    # -------------------------------------------------------------------------
    def place_new_beetle(self, color, location):
        square = self.get_square_by_location(location.row, location.column)
        beetle = Beetle(color, location, self.num_beetles )
        square.beetles.append(beetle)
        self.num_beetles += 1
        return beetle
    
    # -----------------------------------------------------------------------------
    # Board method: get_neighboring_locations
    # This function determines the neighboring locations of a square at a certain 
    # location. It takes the dimension of the board and the location of the square and returns
    # the list of neighboring locations.
    # -----------------------------------------------------------------------------
    def get_neighboring_locations(self, location):

        neighboring_locations = []
        row = location.row
        column = location.column

        # Check if the square is on the top row
        if row > 0:
            neighboring_locations.append(Location(row - 1, column))

        # Check if the square is on the bottom row
        if row < self.dimension - 1:
            neighboring_locations.append(Location(row + 1, column))

        # Check if the square is on the left column
        if column > 0:
            neighboring_locations.append(Location(row, column - 1))

        # Check if the square is on the right column
        if column < self.dimension - 1:
            neighboring_locations.append(Location(row, column + 1))

        return neighboring_locations

# -----------------------------------------------------------------------------
# Class: Game
# The game has a board and a list of beetles that are about to jump.
# -----------------------------------------------------------------------------
class Game:

    # -------------------------------------------------------------------------
    # Game constructor
    # The constructor takes the dimension of the board and creates the board.
    # -------------------------------------------------------------------------
    def __init__(self, dimension, gui: GameGuiProtocol = None):
        self.gui = gui
        self.board = Board(dimension)
        self.beetles_to_jump = []
        self.turn = "red"
        self.moves = []
        self.gui.turn_changed(self, self.turn)

    # -------------------------------------------------------------------------
    # Game method: deep_copy
    # This method returns a deep copy of the game. Note that this is done when
    # there are no more beetles to jump and that a dummy GUI is used.
    # -------------------------------------------------------------------------
    def deep_copy(self):    
        game_copy = Game(self.board.dimension, DummyGui()) 
        game_copy.board = self.board.deep_copy()
        game_copy.turn = self.turn
        game_copy.moves = [ move.deep_copy() for move in self.moves ]
        return game_copy
    
    # -------------------------------------------------------------------------
    # Game method: get_possible_moves
    # This method determines all the possible moves for the current turn.
    # -------------------------------------------------------------------------
    def get_possible_moves(self):
        possible_squares = self.board.get_empty_squares() + self.board.get_squares_by_color(self.turn)
        return [ square.location for square in possible_squares ]

    # -------------------------------------------------------------------------
    # Game method: check_move
    # This method takes a location and checks if the move is valid given the
    # current turn.
    # -------------------------------------------------------------------------
    def check_move(self, location):

        # Check if the game is over.
        if self.get_winner() is not None:
            # No move is allowed if the game is over.
            return False
        
        # Check if the move is valid.
        possible_moves = self.get_possible_moves()
        return location in possible_moves
    
    # -------------------------------------------------------------------------
    # Game method: do_move
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
        self.gui.new_beetle_added(self, new_beetle.id, color, location.row, location.column)

        square = self.board.get_square_by_location(location.row, location.column)
        self.evaluate_square(square)
        self.moves.append(Move(color, location))

        self.transition()

        # If there is a winner, then the game is over.
        winner = self.get_winner()
        if winner is not None:
            self.gui.announce_winner(self, winner)
            return
        
        # Toggle the turn.
        self.turn = "blue" if self.turn == "red" else "red"
        self.gui.turn_changed(self, self.turn)

    # -------------------------------------------------------------------------
    # Game method: evaluate_square
    # This method takes a square and if the square is fully filled, then the
    # beetles on the square are prepared to jump to the neighboring squares but
    # only if the beetles are not already jumping.
    # -------------------------------------------------------------------------
    def evaluate_square(self, square):

        # Determine the number of not jumping beetles on the square.
        not_jumping_beetles = sum(1 for beetle in square.beetles if beetle.destination is None)

        # If the square is not fully filled, then there is nothing to do.
        if not_jumping_beetles < square.capacity:
            return

        # If the square is fully filled and non of the beetles are jumping, then
        # prepare the beetles to jump to the neighboring squares.
        neighboring_locations = square.neighbors
        for index, location in enumerate(neighboring_locations):
            square.beetles[index].prepare_jump(location)
            self.beetles_to_jump.append(square.beetles[index])

    # -------------------------------------------------------------------------
    # Game method: transition
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
    # Game method: make_beetle_jump
    # This method takes a beetle and a destination and makes the beetle jump
    # to the destination.
    # -------------------------------------------------------------------------
    def make_beetle_jump(self, beetle):

        current_square = self.board.get_square_by_location(beetle.location.row, beetle.location.column)
        destination_square = self.board.get_square_by_location(beetle.destination.row, beetle.destination.column)

        # The beetle is no longer about to jump so it is removed from the list.
        self.beetles_to_jump.remove(beetle)

        beetle.jump()
        original_destination_color = destination_square.color

        current_square.remove_beetle(beetle)
        destination_square.add_beetle(beetle)

        self.gui.beetle_moved( self, current_square.location.row, current_square.location.column,
            destination_square.location.row, destination_square.location.column )

        # If the square was conquered, then the color of the beetles was changed.
        if original_destination_color != destination_square.color:
            for square_beetle in destination_square.beetles:
                if square_beetle != beetle:
                    self.gui.set_beetle_color(self, square_beetle.id, beetle.color)

        self.evaluate_square(destination_square)
           
    # -------------------------------------------------------------------------
    # Game method: get_winner
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
    # Game method: reset_game
    # This method resets the game by creating a new game with the specified
    # dimension.
    # -----------------------------------------------------------------------------
    def reset_game(self):
        self.__init__(self.board.dimension, self.gui)

    # -----------------------------------------------------------------------------
    # Game method: calculate_heuristic_values
    # This method calculates the heuristic values of the current game state for
    # each of the possible moves.
    # -----------------------------------------------------------------------------
    def calculate_heuristic_values(self):
        heuristic_values = []

        # Get the possible moves.
        possible_moves = self.get_possible_moves()

        # Determine the heuristic value for each of the possible moves.
        for move in possible_moves:
            heuristic_value = self.calculate_move_value(move)
            heuristic_values.append(heuristic_value)

        return heuristic_values

    # -----------------------------------------------------------------------------
    # Game method: calculate_move_value
    # This method calculates the heuristic value of the current game state for
    # the specified move.
    # -----------------------------------------------------------------------------
    def calculate_move_value(self, move):
        heuristic_value = 0

        # Deep copy the game (which uses a dummy GUI).
        # Note that this copy is done when there are no more beetles to jump.
        game_copy = self.deep_copy()

        # Perform the move on the game copy.
        game_copy.do_move(move.row, move.column)

        # Determine the number of red squares and blue squares.
        num_red_squares = len(game_copy.board.get_squares_by_color("red"))
        num_blue_squares = len(game_copy.board.get_squares_by_color("blue"))

        # Simple heuristic: the number of red squares minus the number of blue squares.
        heuristic_value = num_red_squares - num_blue_squares

        # Set the sign of the heuristic value to the current turn.
        if self.turn == "blue":
            heuristic_value = -heuristic_value
        
        return heuristic_value
    
    # -----------------------------------------------------------------------------
    # Game method: get_best_move
    # This method determines the best move for the current turn.
    # -----------------------------------------------------------------------------
    def get_best_move(self):
        best_move = None
        best_heuristic_value = None

        # Get the possible moves.
        possible_moves = self.get_possible_moves()

        # Determine the heuristic value for each of the possible moves.
        for move in possible_moves:
            heuristic_value = self.calculate_move_value(move)

            if best_heuristic_value is None or heuristic_value > best_heuristic_value:
                best_heuristic_value = heuristic_value
                best_move = move

        return best_move

# =============================================================================