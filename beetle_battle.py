# =============================================================================
# Beetle Battle app
# By Fred Dijkstra
# (c) 2024 - Computerguided Systems B.V.
# =============================================================================

# =============================================================================
# Imports
# =============================================================================
import tkinter as tk
import os
import csv
from tkinter import filedialog
import datetime
from typing import Optional
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
    def prepare_jump(self, destination) -> None:
        self.destination = destination

    # -------------------------------------------------------------------------
    # Beetle method: jump
    # This method makes the beetle jump to the destination.
    # -------------------------------------------------------------------------
    def jump(self) -> None:
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
    def is_empty(self):
        return len(self.beetles) == 0
    
    @property
    def is_full(self):
        return len(self.beetles) == self.capacity
    
    @property
    def is_critical(self):
        return len(self.beetles) == self.capacity - 1
    
    @property
    def num_beetles(self):
        return len(self.beetles)
    
    @property
    def capacity(self):
        return len(self.neighbors)

    # -------------------------------------------------------------------------
    # Square method: deep_copy
    # This method returns a deep copy of the square.
    # -------------------------------------------------------------------------
    def deep_copy(self):
        square_copy = Square(self.location.deep_copy())
        square_copy.neighbors = [neighbor.deep_copy() for neighbor in self.neighbors]
        square_copy.beetles = [beetle.deep_copy() for beetle in self.beetles]
        return square_copy

    # -------------------------------------------------------------------------
    # Square method: add_beetle
    # This method takes a beetle and adds it to the square. The color of the
    # beetles in the square is set by the color of the beetle that is added.
    # -------------------------------------------------------------------------
    def add_beetle(self, new_beetle) -> None:
        for beetle in self.beetles:
            beetle.color = new_beetle.color
        self.beetles.append(new_beetle)

    # -------------------------------------------------------------------------
    # Square method: remove_beetle
    # This method takes a beetle and removes it from the square.
    # -------------------------------------------------------------------------
    def remove_beetle(self, beetle) -> None:
        self.beetles.remove(beetle)

    # -------------------------------------------------------------------------
    # Square method: check_jumping_beetles
    # This method determines whether or not the beetles on the square are
    # jumping.
    # -------------------------------------------------------------------------
    def check_jumping_beetles(self) -> bool:
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
        self.num_beetles = 0
        self.squares = [Square(Location(row, column)) for row in range(dimension) for column in range(dimension)]
        for square in self.squares:
            square.neighbors = self.get_neighboring_locations(square.location)

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
    def get_square_by_location(self, row, column) -> Optional[Square]:
        return self.squares[row * self.dimension + column]
    
    # -------------------------------------------------------------------------
    # Board method: get_empty_squares
    # This method returns the list of squares that have no beetles.
    # -------------------------------------------------------------------------
    def get_empty_squares(self) -> list[Square]:
        return [square for square in self.squares if len(square.beetles) == 0]

    # -------------------------------------------------------------------------
    # Board method: get_squares_by_color
    # This method takes a color and returns the list of squares that have a
    # beetle of that color.
    # -------------------------------------------------------------------------
    def get_squares_by_color(self, color) -> list[Square]:
        return [square for square in self.squares if square.color == color]
        
    # -------------------------------------------------------------------------
    # Board method: place_new_beetle
    # This method takes a color and a location and places a new beetle of that
    # color at that location.
    # -------------------------------------------------------------------------
    def place_new_beetle(self, color, location) -> Beetle:
        square = self.get_square_by_location(location.row, location.column)
        beetle = Beetle(color, location, self.num_beetles )
        square.beetles.append(beetle)
        self.num_beetles += 1
        return beetle
    
    # -------------------------------------------------------------------------
    # Board method: get_neighboring_locations
    # This function determines the neighboring locations of a square at a certain 
    # location. It takes the dimension of the board and the location of the square and returns
    # the list of neighboring locations.
    # -------------------------------------------------------------------------
    def get_neighboring_locations(self, location) -> list[Location]:

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
        game_copy.moves = [move.deep_copy() for move in self.moves]
        return game_copy
    
    # -------------------------------------------------------------------------
    # Game method: get_possible_moves
    # This method determines all the possible moves for the current turn.
    # -------------------------------------------------------------------------
    def get_possible_moves(self) -> list[Location]:
        possible_squares = self.board.get_empty_squares() + self.board.get_squares_by_color(self.turn)
        return [square.location for square in possible_squares]

    # -------------------------------------------------------------------------
    # Game method: check_move
    # This method takes a location and checks if the move is valid given the
    # current turn.
    # -------------------------------------------------------------------------
    def check_move(self, row, column) -> bool:

        location = Location(row, column)

        # Check if the game is over.
        if self.get_winner() is not None:
            # No move is allowed if the game is over.
            return False
        
        # Check if the move is valid.
        possible_moves = self.get_possible_moves()
        return location in possible_moves
    
    # -------------------------------------------------------------------------
    # Game method: do_move
    # This method checks the move and if it is valid, places a new beetle of the
    # current color at that location.
    # -------------------------------------------------------------------------
    def do_move(self, row, column) -> bool:

        # Check if it is a valid move.
        if not self.check_move(row, column):
            return False

        location = Location(row, column)
        color = self.turn

        new_beetle = self.board.place_new_beetle(color, location)
        self.gui.new_beetle_added(self, new_beetle.id, color, location.row, location.column)

        square = self.board.get_square_by_location(location.row, location.column)
        self.evaluate_square(square)
        self.moves.append(Move(color, location))

        self.transition()

        # Toggle the turn.
        self.turn = "blue" if self.turn == "red" else "red"

        # If there is a winner, then the game is over.
        winner = self.get_winner()
        if winner is not None:
            self.gui.announce_winner(self, winner)
            return True
        
        self.gui.turn_changed(self, self.turn)
        return True

    # -------------------------------------------------------------------------
    # Game method: evaluate_square
    # This method takes a square and if the square is fully filled, then the
    # beetles on the square are prepared to jump to the neighboring squares but
    # only if the beetles are not already jumping.
    # -------------------------------------------------------------------------
    def evaluate_square(self, square) -> None:

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
    def transition(self) -> None:

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
    def make_beetle_jump(self, beetle) -> None:

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
    def get_winner(self) -> Optional[str]:

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
    
    # -------------------------------------------------------------------------
    # Game method: reset_game
    # This method resets the game by creating a new game with the specified
    # dimension.
    # -------------------------------------------------------------------------
    def reset_game(self) -> None:
        self.__init__(self.board.dimension, self.gui)

# =============================================================================
# Constants
# =============================================================================
WINDOW_SIZE = 500  # Size of the square window
BOARD_SIZE = 11  # Size of the board

# =============================================================================
# Global Variables
# =============================================================================
square_size = WINDOW_SIZE // 3  # Size of the square

# =============================================================================
# Functions
# =============================================================================

# -----------------------------------------------------------------------------
# Function: get_square_size
# This function returns the size of the square based on the dimension.
# -----------------------------------------------------------------------------
def get_square_size(dimension: int) -> int:
    return WINDOW_SIZE // dimension

# =============================================================================
# Class: GameGui
# =============================================================================
class GameGui:

    # -----------------------------------------------------------------------------
    # GameGui constructor
    # This function initializes the GUI.
    # -----------------------------------------------------------------------------
    def __init__(self, dimension = 3, root = None, canvas = None):

        # Properties
        self.game = None
        self.rectangles = None
        self.computer_player = "blue"
        self.circles = []
        self.player_selection = None
        self.last_move_rectangle = None
        self.root = root
        self.canvas = canvas

        self.create_main_window()
        self.init_canvas(dimension)
        self.set_window_title()
        self.draw_grid(dimension)

        # Set the appropriate window size
        window_width = WINDOW_SIZE
        window_height = WINDOW_SIZE

        # Center the main window
        self.center_window(self.root, window_width, window_height)

        # Enable the canvas.
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.game = Game(dimension, self)

        # Start the GUI loop
        self.root.mainloop()

    # -----------------------------------------------------------------------------
    # GameGui method: new_game
    # This function creates a new game.
    # -----------------------------------------------------------------------------
    def new_game(self, dimension = None) -> None:
        if dimension is None:
            dimension = self.game.board.dimension
        self.__init__(dimension, self.root, self.canvas)

    # -----------------------------------------------------------------------------
    # GameGui method: create_main_window
    # This function creates the root window.
    # -----------------------------------------------------------------------------
    def create_main_window(self) -> None:
        
        # Create the root window if not already created.
        if self.root is None:
            self.root = tk.Tk()
            self.root.title("Beetle Battle")
            self.root.resizable(False, False)

        # Create the menu.
        menu_bar = tk.Menu(self.root)

        # Create the File menu with "New game" and "Exit" items.
        game_menu = tk.Menu(menu_bar, tearoff=0)
        game_menu.add_command(label="New Game", command=lambda: [self.new_game()])
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.root.destroy)

        # Add the File menu to the menu bar.
        menu_bar.add_cascade(label="Game", menu=game_menu)

        # Add the menu bar to the root window.
        self.root.config(menu=menu_bar)

    # -----------------------------------------------------------------------------
    # GameGui method: init_canvas
    # This function initializes the canvas.
    # -----------------------------------------------------------------------------
    def init_canvas(self, dimension) -> None:

        # Destroy the canvas if it already exists.
        if self.canvas is not None:
            self.canvas.destroy()

        # Calculate the square size based on the dimension.
        square_size = get_square_size(dimension)

        # Create the canvas.
        self.canvas = tk.Canvas(self.root, width=dimension * square_size, height=dimension * square_size)
        self.canvas.pack()

    # -----------------------------------------------------------------------------
    # GameGui method: draw_grid
    # This function draws the grid.
    # -----------------------------------------------------------------------------
    def draw_grid(self, dimension, color="black") -> None:

        # Calculate the square size based on the dimension.
        square_size = get_square_size(dimension)

        # Start with a blank list of rectangles.
        self.rectangles = []
        for i in range(dimension):
            for j in range(dimension):
                x1 = j * square_size
                y1 = i * square_size
                x2 = x1 + square_size
                y2 = y1 + square_size
                rectangle = self.canvas.create_rectangle(x1, y1, x2, y2, 
                                                        fill="white", outline=color)
                self.rectangles.append(rectangle)
    
    # -----------------------------------------------------------------------------
    # GameGui method: draw_circle
    # This function draws a circle on the square.
    # -----------------------------------------------------------------------------
    def draw_circle(self, row, column, color) -> int:

        # Calculate the square size based on the dimension.
        square_size = get_square_size(self.game.board.dimension)

        x = column * square_size + square_size / 2
        y = row * square_size + square_size / 2
        radius = square_size / 8
        circle = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=color,
            outline="black")
        return circle

    # -----------------------------------------------------------------------------
    # GameGui method: move_circle
    # This function moves a circle to a new location.
    # -----------------------------------------------------------------------------
    def move_circle(self, item_id, new_x, new_y) -> None:

        # Get the current coordinates of the circle's bounding box
        x1, y1, x2, y2 = self.canvas.coords(item_id)
        
        # Calculate the current center of the circle
        current_center_x = (x1 + x2) / 2
        current_center_y = (y1 + y2) / 2
        
        # Calculate the distance to move the circle to place its center 
        # at (new_x, new_y)
        dx = new_x - current_center_x
        dy = new_y - current_center_y
        
        # Move the circle by the calculated distance
        self.canvas.move(item_id, dx, dy)

    # -----------------------------------------------------------------------------
    # GameGui method: draw_last_move_rectangle
    # This function draws a rectangle around the last move.
    # -----------------------------------------------------------------------------
    def draw_last_move_rectangle(self, row, column, color) -> None:

        # Get the rectangle at the specified location.
        rectangle = self.rectangles[row * self.game.board.dimension + column]

        # Get the coordinates of the rectangle.
        x1, y1, x2, y2 = self.canvas.coords(rectangle)

        points = [x1, y1,  # Top left
                x2, y1,  # Top right
                x2, y2,  # Bottom right
                x1, y2]  # Bottom left
        
        # If the last move rectangle already exists, then move it to the new location.
        if self.last_move_rectangle is not None:
            self.canvas.coords(self.last_move_rectangle, points)
            self.canvas.itemconfig(self.last_move_rectangle, outline=color, width=3)
            return
        
        self.last_move_rectangle = self.canvas.create_polygon(points, outline=color, fill='', width=3)

    # -----------------------------------------------------------------------------
    # GameGui method: change_circle_color
    # This function changes the color of a circle.
    # -----------------------------------------------------------------------------
    def change_circle_color(self, item_id, new_color) -> None:
        self.canvas.itemconfig(item_id, fill=new_color)

   # -----------------------------------------------------------------------------
    # GameGui method: set_color_of_squares
    # This method sets the valid moves for the current turn. It does this by 
    # temporarily changing the color of the square to light gray for those squares 
    # on which the player cannot make a move.
    # -----------------------------------------------------------------------------
    def set_color_of_squares(self, turn=None) -> None:

        # If the turn is not specified, then set all squares to white. This is used
        # when the game is transitioning between moves.
        if turn is None:
            for rectangle in self.rectangles:
                self.canvas.itemconfig(rectangle, fill="white")
            return
        
        # Get the empty squares and the squares that have beetles of the current turn's color.
        valid_squares = self.game.board.get_empty_squares() + self.game.board.get_squares_by_color(turn)

        for index, rectangle in enumerate(self.rectangles):
            square = self.game.board.squares[index]

            # Check if the square at the specified location is is part of the valid squares.
            if square in valid_squares:
                self.canvas.itemconfig(rectangle, fill="white")
            else:
                self.canvas.itemconfig(rectangle, fill="light gray")

        self.canvas.update()

    # -------------------------------------------------------------------------
    # GameGui method: set_last_move
    # This method sets the last move by changing the border of the square to
    # the color of the turn.
    # -------------------------------------------------------------------------
    def show_last_move(self, row, column, color) -> None:
        self.draw_last_move_rectangle(row, column, color)
        self.canvas.update()

    # -------------------------------------------------------------------------
    # GameGui method: set_internal_positions
    # This method takes a list of beetles and sets their internal positions
    # based on the number of beetles in the square.
    # -------------------------------------------------------------------------
    def set_internal_positions(self, row, column) -> None:

        # Get the square at the specified location
        square = self.game.board.get_square_by_location(row, column)

        # Get the circles by getting the beetles in the square
        circles_in_square = []
        for beetle in square.beetles:
            circles_in_square.append(self.circles[beetle.id])

        # Calculate the square size based on the dimension.
        square_size = get_square_size(self.game.board.dimension)

        # Get the center of the square
        center_x = (square.location.column * square_size) + (square_size / 2)
        center_y = (square.location.row * square_size) + (square_size / 2)
    
        # Define positions for the circles based on the count
        # This list holds the positions for up to 4 circles
        positions = [
            [(center_x, center_y)],  # Center for 1 circle
            # Top and bottom for 2 circles
            [(center_x - square_size / 4, center_y - square_size / 4),
            (center_x + square_size / 4, center_y + square_size / 4)],
            # Triangle for 3 circles
            [(center_x, center_y - square_size / 4),
            (center_x - square_size / 4, center_y + square_size / 4),
            (center_x + square_size / 4, center_y + square_size / 4)],
            # Corners for 4 circles
            [(center_x - square_size / 4, center_y - square_size / 4),
            (center_x + square_size / 4, center_y - square_size / 4),
            (center_x - square_size / 4, center_y + square_size / 4),
            (center_x + square_size / 4, center_y + square_size / 4)],
        ]

        # Move the circles
        count = len(circles_in_square)
        circle_positions = positions[count - 1]
        for i in range(count):
            x, y = circle_positions[i]
            self.move_circle(circles_in_square[i], x, y)
        
        self.canvas.update()

    # -----------------------------------------------------------------------------
    # GameGui method: on_canvas_click
    # This function is called when the canvas is clicked on a certain square.
    # -----------------------------------------------------------------------------
    def on_canvas_click(self, event) -> None:

        # Calculate the square size based on the dimension.
        square_size = get_square_size(self.game.board.dimension)

        # Calculate the row and column number
        column = event.x // square_size
        row    = event.y // square_size

        # Check if valid move.
        if not self.game.check_move(row, column):
            return

        self.do_move(row, column)

    # -----------------------------------------------------------------------------
    # GameGui method: do_move
    # This function places a beetle on the board. It is called when the user clicks
    # on a square or when the computer makes a move.
    # -----------------------------------------------------------------------------
    def do_move(self, row, column) -> None:
        # Disable the canvas while the beetles are jumping.
        self.canvas.unbind("<Button-1>")
        self.show_last_move(row, column, self.game.turn) 
        self.game.do_move( row, column )

    # -----------------------------------------------------------------------------
    # GameGui method: center_window
    # This function centers a window on the screen.
    # -----------------------------------------------------------------------------
    def center_window(self, window, width=300, height=200) -> None:

        # Get the screen width and height
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Calculate the x and y coordinates based on the screen dimensions
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        # Set the geometry of the toplevel
        window.geometry(f'{width}x{height}+{x}+{y}')

    # -----------------------------------------------------------------------------
    # GameGui method: set_window_title
    # This function sets the title of the window indicating the turn.
    # -----------------------------------------------------------------------------
    def set_window_title(self, turn = None) -> None:
        if turn is None:
            self.root.title("Beetle Battle")
            return
        self.root.title("Beetle Battle - " + turn + "'s turn")

    # -----------------------------------------------------------------------------
    # GameGui method: set_background_color_of_squares
    # This method sets the valid moves for the current turn. It does this by 
    # temporarily changing the background color of the square to light gray for 
    # those squares on which the player cannot make a move.
    # -----------------------------------------------------------------------------
    def set_background_color_of_squares(self, turn=None) -> None:

        # If the turn is not specified, then set all squares to white. This is used
        # when the game is transitioning between moves.
        if turn is None:
            for rectangle in self.rectangles:
                self.canvas.itemconfig(rectangle, fill="white")
            return
        
        # Get the empty squares and the squares that have beetles of the current turn's color.
        valid_squares = self.game.board.get_empty_squares() + self.game.board.get_squares_by_color(turn)

        for index, square in enumerate(self.game.board.squares):
            # Check if the square at the specified location is is part of the valid squares.
            if square in valid_squares:
                self.canvas.itemconfig(self.rectangles[index], fill="white")
            else:
                self.canvas.itemconfig(self.rectangles[index], fill="light gray")

   # -----------------------------------------------------------------------------
    # GameGui method: save_game
    # This method saves the game by saving the moves to a CSV file.
    # The format is as follows:
    #   move_number, color, row, column
    # -----------------------------------------------------------------------------
    def save_game(self, calling_window) -> None:

        # Create a CSV string from the moves.
        csv_data = [("move_number", "color", "row", "column")]  # Start with the header
        for index, move in enumerate(self.game.moves):
            csv_data.append((index + 1, move.color, move.location.row, move.location.column))

        # Format the current date and time as yyyymmddhhmm
        current_time = datetime.datetime.now()
        default_filename = "beetle-battle " + current_time.strftime("%Y-%m-%d-%H-%M")

        # Get the directory where the current script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Ask the user for a location and name for the CSV file
        file_path = filedialog.asksaveasfilename(
            defaultextension='.csv',
            filetypes=[("CSV files", "*.csv")],
            title="Save moves as CSV",
            initialdir=script_dir, # Set the initial directory
            initialfile=default_filename  # Set the default file name
        )

        # If the user doesn't cancel, then save the file
        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                # Write the board dimension as metadata at the top
                file.write(f"dimension: {self.game.board.dimension}\n")
                file.write(f"winner: {self.game.get_winner()}\n\n")

                writer = csv.writer(file)
                writer.writerows(csv_data)  # Write the data rows

        # return the focus to the calling window
        calling_window.focus_force()

    # -------------------------------------------------------------------------
    # -- GameGuiProtocol Methods --
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # GameGui method: turn_changed
    # -------------------------------------------------------------------------
    def turn_changed(self, sender, color: str) -> None:

        self.game = sender

        self.set_window_title( color )
        
        # Indicate invalid moves.
        self.set_color_of_squares(color)
    
        # Enable the canvas again.
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    # -------------------------------------------------------------------------
    # GameGui method: beetle_moved
    # -------------------------------------------------------------------------
    def beetle_moved(self, sender,
                     source_row: int, source_column: int,
                     destination_row: int, destination_column: int) -> None:
        # First reorganize the circles in the destination square and then
        # in the source square for better visual effect.
        self.set_internal_positions(destination_row, destination_column)
        self.set_internal_positions(source_row, source_column)

    # -------------------------------------------------------------------------
    # GameGui method: new_beetle_added
    # -------------------------------------------------------------------------
    def new_beetle_added(self, sender,
                         beetle_id: int, color: str, row: int, column: int) -> None:
        new_circle = self.draw_circle(row, column, color)
        self.circles.append(new_circle)
        self.set_internal_positions(row, column)

    # -------------------------------------------------------------------------
    # GameGui method: set_beetle_color
    # -------------------------------------------------------------------------
    def set_beetle_color(self, sender,
                         beetle_id: int, color: str) -> None:
        circle = self.circles[beetle_id]
        self.change_circle_color(circle, color)

    # -------------------------------------------------------------------------
    # GameGui method: announce_winner
    # -------------------------------------------------------------------------
    def announce_winner(self, sender,
                        color: str) -> None:
        message = "The winner is " + color + "!"

        # Create a top-level window to act as the message box
        message_window = tk.Toplevel(self.root)
        message_window.title("Game over!")
        
        # Center the window on the screen
        self.center_window(message_window, 300, 100)

        # Make sure the message window takes focus and stays on top
        message_window.grab_set()
        message_window.transient(self.root)  # Set to be on top of the main window
        message_window.focus_force()
        
        # Add a label with the message
        tk.Label(message_window, text=message, padx=20, pady=10).pack()

        # Create a frame to contain the buttons
        button_frame = tk.Frame(message_window)
        button_frame.pack(pady=10)

        # Add an OK button that closes the message window    
        tk.Button(button_frame, text="OK", 
                command=lambda: [message_window.destroy(), self.new_game()], 
                padx=20, pady=5).pack(side=tk.LEFT)

        # Add a "Save game" button, assuming you have a method self.download_moves
        tk.Button(button_frame, text="Save game", 
                command=lambda: [self.save_game(message_window)], 
                padx=20, pady=5).pack(side=tk.LEFT)
        
        # Capture the window close (X) button click as well
        message_window.protocol("WM_DELETE_WINDOW", 
                                lambda: [message_window.destroy(), 
                                         self.new_game()])

# =============================================================================


if __name__ == '__main__':
    GameGui(11)