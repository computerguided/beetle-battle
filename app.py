# =============================================================================
# Beetle Battle
# =============================================================================

# =============================================================================
# Imports
# =============================================================================
import tkinter as tk
import sys

# =============================================================================
# Constants
# =============================================================================
SQUARE_SIZE = 100  # Size of the squares in pixels

# =============================================================================
# Global variables
# =============================================================================
canvas = None
game   = None
root   = None

# =============================================================================
# GUI
# =============================================================================

# -----------------------------------------------------------------------------
# Function: create_main_window
# This function creates a main window and its menu and returns it.
# -----------------------------------------------------------------------------
def create_main_window():
    root = tk.Tk()
    root.title("Beetle Battle")

    # Create the menu
    menubar = tk.Menu(root)

    # Create the File menu with "New game" and "Exit" items
    game_menu = tk.Menu(menubar, tearoff=0)
    game_menu.add_command(label="New Game", command=lambda: [game.reset_game()])
    game_menu.add_separator()
    game_menu.add_command(label="Exit", command=root.destroy)

    # Add the File menu to the menu bar
    menubar.add_cascade(label="Game", menu=game_menu)

    # Create the "Board" menu with "3x3", "4x4", "5x5", and "10x10" items.
    board_menu = tk.Menu(menubar, tearoff=0)
    board_menu.add_command(label="3x3",   command=lambda: [root.destroy(), main(3)])
    board_menu.add_command(label="4x4",   command=lambda: [root.destroy(), main(4)])
    board_menu.add_command(label="5x5",   command=lambda: [root.destroy(), main(5)])
    board_menu.add_command(label="10x10", command=lambda: [root.destroy(), main(10)])

    # Add the "Board" menu to the menu bar
    menubar.add_cascade(label="Board", menu=board_menu)

    # Add the menu bar to the root window
    root.config(menu=menubar)

    return root

# -----------------------------------------------------------------------------
# Function: init_canvas
# This function initializes and returns a canvas.
# -----------------------------------------------------------------------------
def init_canvas(dimension):
    canvas = tk.Canvas(root, width=dimension * SQUARE_SIZE, height=dimension * SQUARE_SIZE)
    canvas.pack()
    return canvas

# -----------------------------------------------------------------------------
# Function: draw_grid
# This function draws the grid.
# -----------------------------------------------------------------------------
def draw_grid(dimension, color="black"):
    rectangles = []
    for i in range(dimension):
        for j in range(dimension):
            x1 = j * SQUARE_SIZE
            y1 = i * SQUARE_SIZE
            x2 = x1 + SQUARE_SIZE
            y2 = y1 + SQUARE_SIZE
            rectangle = canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline=color)
            rectangles.append(rectangle)

    return rectangles

# -----------------------------------------------------------------------------
# Function: draw_circle
# This function draws a circle on the square and saves the circle in the 
# beetle object for later use.
# -----------------------------------------------------------------------------
def draw_circle(canvas, square, beetle):
    color = beetle.color
    row = square.location.row
    column = square.location.column

    x = column * SQUARE_SIZE + SQUARE_SIZE // 2
    y = row * SQUARE_SIZE + SQUARE_SIZE // 2
    radius = SQUARE_SIZE // 8
    circle = canvas.create_oval(
        x - radius, y - radius,
        x + radius, y + radius,
        fill=color
    )
    beetle.circle = circle

# -----------------------------------------------------------------------------
# Function: move_circle
# This function moves a circle to a new location.
# -----------------------------------------------------------------------------
def move_circle(canvas, item_id, new_x, new_y):
    # Get the current coordinates of the circle's bounding box
    x1, y1, x2, y2 = canvas.coords(item_id)
    
    # Calculate the current center of the circle
    current_center_x = (x1 + x2) / 2
    current_center_y = (y1 + y2) / 2
    
    # Calculate the distance to move the circle to place its center at (new_x, new_y)
    dx = new_x - current_center_x
    dy = new_y - current_center_y
    
    # Move the circle by the calculated distance
    canvas.move(item_id, dx, dy)

# -----------------------------------------------------------------------------
# Function: change_circle_color
# This function changes the color of a circle.
# -----------------------------------------------------------------------------
def change_circle_color(canvas, item_id, new_color):
    canvas.itemconfig(item_id, fill=new_color)

# -----------------------------------------------------------------------------
# Function: on_canvas_click
# This function is called when the canvas is clicked on a certain square.
# -----------------------------------------------------------------------------
def on_canvas_click(event):
    # Calculate the row and column number
    col = event.x // SQUARE_SIZE
    row = event.y // SQUARE_SIZE
    if game.check_move(Location(row, col)):
        # Disable the canvas while the beetles are jumping.
        canvas.unbind("<Button-1>")

        # Set all squares to white.
        game.set_color_of_squares()

        game.do_move(game.turn, Location(row, col))

        # Check if there is a winner.
        winner = game.get_winner()
        if winner is not None:
            set_window_title()
            game.announce_winner(winner)
            return
        
        # Set the title of the window to indicate the turn.
        set_window_title(game.turn)
        
        # Enable the canvas again.
        canvas.bind("<Button-1>", on_canvas_click)

        # Set the squares to the valid moves for the current turn.
        game.set_color_of_squares(game.turn)
    
# -----------------------------------------------------------------------------
# Function: center_window
# This function centers a window on the screen.
# -----------------------------------------------------------------------------
def center_window(window, width=300, height=200):
    # Get the screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Calculate the x and y coordinates based on the screen dimensions
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    
    # Set the geometry of the toplevel
    window.geometry(f'{width}x{height}+{x}+{y}')

# -----------------------------------------------------------------------------
# Function: set_window_title
# This function sets the title of the window indicating the turn.
# -----------------------------------------------------------------------------
def set_window_title(turn = None):
    if turn is None:
        root.title("Beetle Battle")
        return
    
    root.title("Beetle Battle - " + turn + "'s turn")

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

    # -------------------------------------------------------------------------
    def __init__(self, color, location):
        self.color = color
        self.location = location
        self.destination = None

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
        change_circle_color(canvas, self.circle, color)

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
    # Method: add_beetle
    # This method takes a beetle and adds it to the square. The color of the
    # beetles in the square is set by the color of the beetle that is added.
    # -------------------------------------------------------------------------
    def add_beetle(self, new_beetle):
        self.beetles.append(new_beetle)
        for beetle in self.beetles:
            beetle.set_color(new_beetle.color)
        self.set_internal_positions()

    # -------------------------------------------------------------------------
    # Method: remove_beetle
    # This method takes a beetle and removes it from the square.
    # -------------------------------------------------------------------------
    def remove_beetle(self, beetle):
        self.beetles.remove(beetle)
        self.set_internal_positions()

    # -------------------------------------------------------------------------
    # Method: set_internal_positions
    # This method takes a list of beetles and sets their internal positions
    # based on the number of beetles in the square.
    # -------------------------------------------------------------------------
    def set_internal_positions(self):
        # Define the center of the square
        center_x = (self.location.column * SQUARE_SIZE) + (SQUARE_SIZE // 2)
        center_y = (self.location.row * SQUARE_SIZE) + (SQUARE_SIZE // 2)
    
        # Define positions for the circles based on the count
        # This list holds the positions for up to 4 circles
        positions = [
            [(center_x, center_y)],  # Center for 1 circle
            # Top and bottom for 2 circles
            [(center_x - SQUARE_SIZE // 4, center_y - SQUARE_SIZE // 4),
            (center_x + SQUARE_SIZE // 4, center_y + SQUARE_SIZE // 4)],
            # Triangle for 3 circles
            [(center_x, center_y - SQUARE_SIZE // 4),
            (center_x - SQUARE_SIZE // 4, center_y + SQUARE_SIZE // 4),
            (center_x + SQUARE_SIZE // 4, center_y + SQUARE_SIZE // 4)],
            # Corners for 4 circles
            [(center_x - SQUARE_SIZE // 4, center_y - SQUARE_SIZE // 4),
            (center_x + SQUARE_SIZE // 4, center_y - SQUARE_SIZE // 4),
            (center_x - SQUARE_SIZE // 4, center_y + SQUARE_SIZE // 4),
            (center_x + SQUARE_SIZE // 4, center_y + SQUARE_SIZE // 4)],
        ]

        # Move the circles
        count = len(self.beetles)
        circle_positions = positions[count - 1]
        for i in range(count):
            x, y = circle_positions[i]
            move_circle(canvas, self.beetles[i].circle, x, y)
        
        canvas.update()

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

    # -------------------------------------------------------------------------
    # Constructor
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
                square.capacity = len(get_neighboring_locations(dimension, Location(row, column)))
                self.squares.append(square)

    # -------------------------------------------------------------------------
    # Method: get_square_by_location
    # This method takes a location and returns the square at that location.
    # -------------------------------------------------------------------------
    def get_square_by_location(self, location):
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
        squares = []
        for square in self.squares:
            for beetle in square.beetles:
                if beetle.color == color:
                    squares.append(square)
                    break
        return squares
        
    # -------------------------------------------------------------------------
    # Method: place_new_beetle
    # This method takes a color and a location and places a new beetle of that
    # color at that location.
    # -------------------------------------------------------------------------
    def place_new_beetle(self, color, location):
        square = self.get_square_by_location(location)
        beetle = Beetle(color, location)
        draw_circle(canvas, square, beetle)
        self.add_beetle(beetle, square)

    # -------------------------------------------------------------------------
    # Method: add_beetle
    # This method takes a beetle and adds it to the specified square. If the
    # square becomes fully filled, then the beetles are prepared to jump to
    # the neighboring squares.
    # -------------------------------------------------------------------------
    def add_beetle(self, beetle, square):
        square.beetles.append(beetle)
        square.set_internal_positions()

# -----------------------------------------------------------------------------
# Class: Game
# The game has a board and a list of beetles that are about to jump.
# -----------------------------------------------------------------------------
class Game:
    board = None
    beetles_to_jump = []
    turn = None
    moveCount = 0

    # -------------------------------------------------------------------------
    # Constructor
    # The constructor takes the dimension of the board and creates the board.
    # -------------------------------------------------------------------------
    def __init__(self, dimension):
        self.board = Board(dimension)

        # Draw the grid
        self.board.rectangles = draw_grid(self.board.dimension)

        self.beetles_to_jump = []
        self.turn = "red"
        self.moveCount = 0

        # Enable the canvas click.
        canvas.bind("<Button-1>", on_canvas_click)

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
        square = self.board.get_square_by_location(location)

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
    def do_move(self, color, location):
        self.board.place_new_beetle(color, location)
        square = self.board.get_square_by_location(location)
        self.evaluate_square(square)
        self.moveCount += 1

        self.transition()
        
        if self.turn == "red":
            self.turn = "blue"
        else:
            self.turn = "red"

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
        skipped_beetle_jumps = 0
        game_over = self.get_winner() is not None

        # Loop through the list of beetles that are about to jump until there
        # are no beetles left or until there is a winner.
        while len(self.beetles_to_jump) > 0 and not game_over:

            beetle = self.beetles_to_jump[skipped_beetle_jumps]
            destination = beetle.destination
            destination_square = self.board.get_square_by_location(destination)

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
        current_square = self.board.get_square_by_location(beetle.location)
        destination_square = self.board.get_square_by_location(beetle.destination)

        # The beetle is no longer about to jump so it is removed from the list.
        self.beetles_to_jump.remove(beetle)

        # For visualization: first move the beetle to the destination square and 
        # then remove it from the current square.
        beetle.jump()
        destination_square.add_beetle(beetle)
        current_square.remove_beetle(beetle)

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
        if self.moveCount < 3:
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
    # Method: announce_winner
    # This method announces the winner by creating a modal message box.
    # -----------------------------------------------------------------------------
    def announce_winner(self, winner_name):
        message = "The winner is " + winner_name + "!"

        # Create a top-level window to act as the message box
        message_window = tk.Toplevel(root)
        message_window.title("Game over!")
        
        # Center the window on the screen
        center_window(message_window, 300, 100)  # You can adjust the size as needed

        # Make sure the message window takes focus and stays on top
        message_window.grab_set()
        message_window.transient(root)  # Set to be on top of the main window
        message_window.focus_force()
        
        # Add a label with the message
        tk.Label(message_window, text=message, padx=20, pady=10).pack()
        
        # Add an OK button that closes the message window    
        tk.Button(message_window, text="OK", command=lambda: [message_window.destroy(), self.reset_game()], padx=20, pady=5).pack()

    # -----------------------------------------------------------------------------
    # Method: reset_game
    # This method resets the game.
    # -----------------------------------------------------------------------------
    def reset_game(self):

        # Clear the canvas
        canvas.delete("all")

        # Create a new game with the specified dimension
        self.__init__(self.board.dimension)

        # Set the title of the window to indicate the turn.
        set_window_title(self.turn)

    # -----------------------------------------------------------------------------
    # Method: set_color_of_squares
    # This method sets the valid moves for the current turn. It does this by 
    # temporarily changing the color of the square to light gray for those squares 
    # on which the player cannot make a move.
    # -----------------------------------------------------------------------------
    def set_color_of_squares(self, turn=None):

        # If the turn is not specified, then set all squares to white. This is used
        # when the game is transitioning between moves.
        if turn is None:
            for square in self.board.squares:
                canvas.itemconfig(self.board.rectangles[square.location.row * self.board.dimension + square.location.column], fill="white")
            return
        
        # Get the empty squares and the squares that have beetles of the current turn's color.
        valid_squares = self.board.get_empty_squares() + self.board.get_squares_by_color(turn)

        for square in self.board.squares:

            # Check if the square at the specified location is is part of the valid squares.
            if square in valid_squares:
                canvas.itemconfig(self.board.rectangles[square.location.row * self.board.dimension + square.location.column], fill="white")
            else:
                canvas.itemconfig(self.board.rectangles[square.location.row * self.board.dimension + square.location.column], fill="light gray")

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
# Main program
# =============================================================================

# -----------------------------------------------------------------------------
# Function: main
# This function is the main program. It takes the dimension of the board as an
# argument and runs the game.
# -----------------------------------------------------------------------------
def main(dimension):

    # Initialize the main window.
    global root
    root = create_main_window()

    # Initialize the canvas.
    global canvas
    canvas = init_canvas(dimension)

    # Create a new game with the specified dimension.
    global game
    game = Game(dimension)

    # Set the title of the window to indicate the turn.
    set_window_title(game.turn)

    # Draw the grid.
    game.board.rectangles = draw_grid(dimension)

    # Calculate the appropriate window size
    window_width = dimension * SQUARE_SIZE
    window_height = dimension * SQUARE_SIZE

    # Center the main window
    center_window(root, window_width, window_height)

    # Start the GUI loop
    root.mainloop()

# -----------------------------------------------------------------------------
# Run the main program and use the argument as the dimension of the board.
# -----------------------------------------------------------------------------
if __name__ == "__main__":

    # Get the argument from the command line. If it is not supplied, then use 5.
    if len(sys.argv) > 1:
        dimension = int(sys.argv[1])
    else:
        dimension = 5
    main(dimension)