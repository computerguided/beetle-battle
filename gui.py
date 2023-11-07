import tkinter as tk

# Define the size of the grid and the squares
GRID_SIZE = 10
SQUARE_SIZE = 50  # Adjust the size of the squares as needed

# Create the main window
root = tk.Tk()
root.title("Board Game")

# Set up the canvas where the grid will be drawn
canvas = tk.Canvas(root, width=GRID_SIZE * SQUARE_SIZE, height=GRID_SIZE * SQUARE_SIZE)
canvas.pack()

class Square:
    def __init__(self):
        self.circle_count = 0
        self.circle_objects = []  # Keep track of circle objects

    def add_circle(self, circle):
        self.circle_objects.append(circle)

    def clear_circles(self):
        for circle in self.circle_objects:
            canvas.delete(circle)
        self.circle_objects = []

# Initialize a 10x10 grid of Square objects
squares = [[Square() for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# Function to draw circles in the given square
def draw_circles(canvas, row, col, square):
    # Clear existing circles
    square.clear_circles()

    # Define the center of the square
    center_x = (col * SQUARE_SIZE) + (SQUARE_SIZE // 2)
    center_y = (row * SQUARE_SIZE) + (SQUARE_SIZE // 2)
    # Define the radius of the circles
    radius = SQUARE_SIZE // 8  # Small enough to fit four in a square

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

    # Draw the specified number of circles
    circle_positions = positions[square.circle_count-1]
    for i in range(square.circle_count):
        x, y = circle_positions[i]
        circle = canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill="red"
        )

        # Store the circle object
        square.add_circle(circle)

# Function to handle mouse clicks
def on_canvas_click(event):
    # Calculate the row and column number
    col = event.x // SQUARE_SIZE
    row = event.y // SQUARE_SIZE
    square = squares[row][col]

    # Add a circle if the square has less than 4
    if square.circle_count < 4:
        square.circle_count += 1
    else:
        # Reset the count and clear circles if 4 are already present
        square.circle_count = 1
    draw_circles(canvas, row, col, square)

# Bind the click event to the handler function
canvas.bind("<Button-1>", on_canvas_click)

# Draw the grid
for i in range(GRID_SIZE):
    for j in range(GRID_SIZE):
        x1 = j * SQUARE_SIZE
        y1 = i * SQUARE_SIZE
        x2 = x1 + SQUARE_SIZE
        y2 = y1 + SQUARE_SIZE
        canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black")

# Start the GUI loop
root.mainloop()
