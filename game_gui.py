# =============================================================================
# Beetle Battle - Game GUI Module
# By Fred Dijkstra
# (c) 2023 - Computerguided Systems B.V.
# =============================================================================

# =============================================================================
# Imports
# =============================================================================
import tkinter as tk
import os
import csv
from tkinter import filedialog
import datetime

# =============================================================================
# Local Imports
# =============================================================================
from game_engine import Game

# =============================================================================
# Constants
# =============================================================================
SQUARE_SIZE = 100  # Size of the squares in pixels

# =============================================================================
# Class: GameGui
# =============================================================================
class GameGui:
    game = None
    root = None
    canvas = None
    circles = None
    rectangles = None

    # -----------------------------------------------------------------------------
    # Function: __init__
    # This function initializes the GUI.
    # -----------------------------------------------------------------------------
    def __init__(self, dimension = 3):
        self.circles = []
        self.create_main_window()
        self.init_canvas(dimension)
        self.set_window_title()
        self.draw_grid(dimension)

        # Calculate the appropriate window size
        window_width = dimension * SQUARE_SIZE
        window_height = dimension * SQUARE_SIZE

        # Center the main window
        self.center_window(self.root, window_width, window_height)

        # Enable the canvas again.
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.game = Game(dimension, self)

        # Start the GUI loop
        self.root.mainloop()

    # -----------------------------------------------------------------------------
    # Function: new_game
    # This function creates a new game.
    # -----------------------------------------------------------------------------
    def new_game(self, dimension = None):
        if dimension is None:
            dimension = self.game.board.dimension
        self.__init__(dimension)

    # -----------------------------------------------------------------------------
    # Function: create_main_window
    # This function creates the root window.
    # -----------------------------------------------------------------------------
    def create_main_window(self):
        
        # Create the root window if not already created.
        if self.root is None:
            self.root = tk.Tk()
            self.root.title("Beetle Battle")
            self.root.resizable(False, False)

        # Create the menu.
        menubar = tk.Menu(self.root)

        # Create the File menu with "New game" and "Exit" items.
        game_menu = tk.Menu(menubar, tearoff=0)
        game_menu.add_command(label="New Game", command=lambda: [self.new_game()])
        game_menu.add_separator()
        game_menu.add_command(label="Exit", command=self.root.destroy)

        # Add the File menu to the menu bar.
        menubar.add_cascade(label="Game", menu=game_menu)

        # Create the "Board" menu with "3x3", "4x4", "5x5", and "10x10" items.
        board_menu = tk.Menu(menubar, tearoff=0)
        board_menu.add_command(label="3x3",   command=lambda: [self.new_game(3)])
        board_menu.add_command(label="4x4",   command=lambda: [self.new_game(4)])
        board_menu.add_command(label="5x5",   command=lambda: [self.new_game(5)])
        board_menu.add_command(label="10x10", command=lambda: [self.new_game(10)])

        # Add the "Board" menu to the menu bar.
        menubar.add_cascade(label="Board", menu=board_menu)

        # Add the menu bar to the root window.
        self.root.config(menu=menubar)

    # -----------------------------------------------------------------------------
    # Function: init_canvas
    # This function initializes the canvas.
    # -----------------------------------------------------------------------------
    def init_canvas(self, dimension):

        # Destroy the canvas if it already exists.
        if self.canvas is not None:
            self.canvas.destroy()

        # Create the canvas.
        self.canvas = tk.Canvas(self.root, width=dimension * SQUARE_SIZE, height=dimension * SQUARE_SIZE)
        self.canvas.pack()

    # -----------------------------------------------------------------------------
    # Function: draw_grid
    # This function draws the grid.
    # -----------------------------------------------------------------------------
    def draw_grid(self, dimension, color="black"):

        # Start with a blank list of rectangles.
        self.rectangles = []
        for i in range(dimension):
            for j in range(dimension):
                x1 = j * SQUARE_SIZE
                y1 = i * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE
                rectangle = self.canvas.create_rectangle(x1, y1, x2, y2, 
                                                        fill="white", outline=color)
                self.rectangles.append(rectangle)
    
    # -----------------------------------------------------------------------------
    # Function: draw_circle
    # This function draws a circle on the square.
    # -----------------------------------------------------------------------------
    def draw_circle(self, row, column, color):
        x = column * SQUARE_SIZE + SQUARE_SIZE // 2
        y = row * SQUARE_SIZE + SQUARE_SIZE // 2
        radius = SQUARE_SIZE // 8
        circle = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=color,
            outline="black")
        return circle

    # -----------------------------------------------------------------------------
    # Function: move_circle
    # This function moves a circle to a new location.
    # -----------------------------------------------------------------------------
    def move_circle(self, item_id, new_x, new_y):

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
    # Function: change_circle_color
    # This function changes the color of a circle.
    # -----------------------------------------------------------------------------
    def change_circle_color(self, item_id, new_color):
        self.canvas.itemconfig(item_id, fill=new_color)

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
    # Method: set_internal_positions
    # This method takes a list of beetles and sets their internal positions
    # based on the number of beetles in the square.
    # -------------------------------------------------------------------------
    def set_internal_positions(self, row, column):

        # Get the square at the specified location
        square = self.game.board.get_square_by_location(row, column)

        # Get the circles by getting the beetles in the square
        circles_in_square = []
        for beetle in square.beetles:
            circles_in_square.append(self.circles[beetle.id])

        # Get the center of the square
        center_x = (square.location.column * SQUARE_SIZE) + (SQUARE_SIZE // 2)
        center_y = (square.location.row * SQUARE_SIZE) + (SQUARE_SIZE // 2)
    
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
        count = len(circles_in_square)
        circle_positions = positions[count - 1]
        for i in range(count):
            x, y = circle_positions[i]
            self.move_circle(circles_in_square[i], x, y)
        
        self.canvas.update()

    # -----------------------------------------------------------------------------
    # Function: on_canvas_click
    # This function is called when the canvas is clicked on a certain square.
    # -----------------------------------------------------------------------------
    def on_canvas_click(self, event):

        # Calculate the row and column number
        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE
            
        # Disable the canvas while the beetles are jumping.
        self.canvas.unbind("<Button-1>")

        # Set all squares to white.
        self.set_color_of_squares()

        self.game.do_move( row, col )

        # Set all squares to white.
        self.set_color_of_squares(self.game.turn)
        
        # Enable the canvas again.
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    # -----------------------------------------------------------------------------
    # Function: center_window
    # This function centers a window on the screen.
    # -----------------------------------------------------------------------------
    def center_window(self, window, width=300, height=200):

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
    def set_window_title(self, turn = None):
        if turn is None:
            self.root.title("Beetle Battle")
            return
        self.root.title("Beetle Battle - " + turn + "'s turn")

    # -----------------------------------------------------------------------------
    # Method: set_background_color_of_squares
    # This method sets the valid moves for the current turn. It does this by 
    # temporarily changing the background color of the square to light gray for 
    # those squares on which the player cannot make a move.
    # -----------------------------------------------------------------------------
    def set_background_color_of_squares(self, turn=None):

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
    # Method: save_game
    # This method saves the game by saving the moves to a CSV file.
    # The format is as follows:
    #   move_number, color, row, column
    # -----------------------------------------------------------------------------
    def save_game(self, calling_window):

        # Create a CSV string from the moves.
        csv_data = [("move_number", "color", "row", "column")]  # Start with the header
        for index, move in enumerate(self.game.moves):
            csv_data.append((index + 1, move[0], move[1].row, move[1].column))

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
    # Method: turn_changed
    # -------------------------------------------------------------------------
    def turn_changed(self, color: str) -> None:
        self.set_window_title(color)

    # -------------------------------------------------------------------------
    # Method: beetle_moved
    # -------------------------------------------------------------------------
    def beetle_moved(self, 
                     source_row: int, source_column: int,
                     destination_row: int, destination_colum: int) -> None:
        self.set_internal_positions(source_row, source_column)
        self.set_internal_positions(destination_row, destination_colum)

    # -------------------------------------------------------------------------
    # Method: new_beetle_added
    # -------------------------------------------------------------------------
    def new_beetle_added(self, beetle_id: int, color: str, row: int, column: int) -> None:
        new_circle = self.draw_circle(row, column, color)
        self.circles.append(new_circle)
        self.set_internal_positions(row, column)

    # -------------------------------------------------------------------------
    # Method: set_beetle_color
    # -------------------------------------------------------------------------
    def set_beetle_color(self, beetle_id: int, color: str) -> None:
        circle = self.circles[beetle_id]
        self.change_circle_color(circle, color)

    # -------------------------------------------------------------------------
    # Method: announce_winner
    # -------------------------------------------------------------------------
    def announce_winner(self, color: str) -> None:
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
        message_window.protocol("WM_DELETE_WINDOW", lambda: [message_window.destroy(), self.new_game()])

# =============================================================================