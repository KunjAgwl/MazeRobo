import pygame
import time

# Movement directions and their coordinate offsets
DIRECTIONS = {
    'left': (-1, 0),
    'right': (1, 0),
    'up': (0, -1),
    'down': (0, 1)
}

# Turn mappings for robot navigation
LEFT_TURNS = {'left': 'down', 'down': 'right', 'right': 'up', 'up': 'left'}
RIGHT_TURNS = {'left': 'up', 'up': 'right', 'right': 'down', 'down': 'left'}
OPPOSITE_DIRECTIONS = {'left': 'right', 'right': 'left', 'up': 'down', 'down': 'up'}

# Display settings
CELL_SIZE = 40
ROBOT_RADIUS = 15
PATH_WIDTH = 3
ANIMATION_DELAY = 0.1
FPS = 60

# Colors for different elements
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (200, 200, 200)
GREEN = (0, 255, 0)      # Start position
RED = (255, 0, 0)        # End position
BLUE = (0, 0, 255)       # Robot path
ORANGE = (255, 165, 0)   # Robot

# Maze cell types
EMPTY_CELL = 0
WALL_CELL = 1


class Maze:
    """Represents the maze structure with walls and pathways."""
    
    def __init__(self, maze_grid, start_position, end_position):
        """
        Initialize the maze.
        
        maze_grid: 2D list where 0=empty path, 1=wall
        start_position: (x, y) coordinates for start
        end_position: (x, y) coordinates for goal
        """
        self.grid = maze_grid
        self.width = len(maze_grid[0])
        self.height = len(maze_grid)
        self.start = start_position
        self.end = end_position
    
    def is_within_bounds(self, position):
        """Check if position is inside maze boundaries."""
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height
    
    def is_wall(self, position):
        """
        Check if the given position is a wall or outside maze bounds.
        Returns True if position is blocked, False if passable.
        """
        if not self.is_within_bounds(position):
            return True
        
        x, y = position
        return self.grid[y][x] == WALL_CELL


class MazeRobot:
    """Robot that navigates through the maze using left-hand wall following."""
    
    def __init__(self, maze):
        """Initialize robot at maze start position."""
        self.maze = maze
        self.current_pos = maze.start
        self.facing_direction = 'up'
        self.path_taken = [maze.start]
        self.move_history = []
    
    def get_next_position(self, direction):
        """Calculate the next position if moving in given direction."""
        dx, dy = DIRECTIONS[direction]
        current_x, current_y = self.current_pos
        return (current_x + dx, current_y + dy)
    
    def can_move_to(self, direction):
        """
        Check if robot can move in the specified direction.
        Returns (can_move, next_position) tuple.
        """
        next_pos = self.get_next_position(direction)
        is_passable = not self.maze.is_wall(next_pos)
        return is_passable, next_pos
    
    def move_to_direction(self, direction):
        """
        Move robot in the specified direction if possible.
        Returns True if move was successful, False otherwise.
        """
        can_move, next_pos = self.can_move_to(direction)
        
        if can_move:
            self.current_pos = next_pos
            self.path_taken.append(next_pos)
            return True
        
        return False
    
    def try_move_with_turn(self, new_direction, move_symbol):
        """
        Try to move in new direction and record the move type.
        Returns True if successful move was made.
        """
        can_move, _ = self.can_move_to(new_direction)
        
        if can_move:
            if self.move_to_direction(new_direction):
                self.facing_direction = new_direction
                self.move_history.append(move_symbol)
                return True
        
        return False
    
    def execute_next_step(self):
        """
        Execute one step of the left-hand wall following algorithm.
        Priority: Left -> Straight -> Right -> Back
        """
        # Calculate possible directions based on current facing
        left_direction = LEFT_TURNS[self.facing_direction]
        straight_direction = self.facing_direction
        right_direction = RIGHT_TURNS[self.facing_direction]
        back_direction = OPPOSITE_DIRECTIONS[self.facing_direction]
        
        # Try left turn first (left-hand rule)
        if self.try_move_with_turn(left_direction, 'L'):
            return
        
        # Try moving straight
        can_go_straight, _ = self.can_move_to(straight_direction)
        if can_go_straight:
            if self.move_to_direction(straight_direction):
                self.move_history.append('S')
                return
        
        # Try right turn
        if self.try_move_with_turn(right_direction, 'R'):
            return
        
        # Last resort: turn around and go back
        self.facing_direction = back_direction
        if self.move_to_direction(back_direction):
            self.move_history.append('B')
    
    def has_reached_goal(self):
        """Check if robot has reached the maze exit."""
        return self.current_pos == self.maze.end


class MazeRenderer:
    """Handles all pygame rendering for the maze visualization."""
    
    def __init__(self, maze):
        """Initialize pygame display based on maze dimensions."""
        self.screen_width = maze.width * CELL_SIZE
        self.screen_height = maze.height * CELL_SIZE
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Maze Solving Robot - Left-Hand Wall Following")
    
    def draw_maze_background(self, maze):
        """Draw the basic maze grid with walls and empty spaces."""
        self.screen.fill(WHITE)
        
        for row in range(maze.height):
            for col in range(maze.width):
                cell_rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                if maze.grid[row][col] == WALL_CELL:
                    pygame.draw.rect(self.screen, BLACK, cell_rect)
                else:
                    pygame.draw.rect(self.screen, LIGHT_GRAY, cell_rect)
    
    def draw_start_and_goal(self, maze):
        """Draw start position in green and goal position in red."""
        start_x, start_y = maze.start
        goal_x, goal_y = maze.end
        
        start_rect = pygame.Rect(start_x * CELL_SIZE, start_y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        goal_rect = pygame.Rect(goal_x * CELL_SIZE, goal_y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        
        pygame.draw.rect(self.screen, GREEN, start_rect)
        pygame.draw.rect(self.screen, RED, goal_rect)
    
    def draw_robot_trail(self, robot):
        """Draw the path the robot has taken as blue lines."""
        if len(robot.path_taken) < 2:
            return
        
        for i in range(len(robot.path_taken) - 1):
            start_point = self.get_cell_center(robot.path_taken[i])
            end_point = self.get_cell_center(robot.path_taken[i + 1])
            pygame.draw.line(self.screen, BLUE, start_point, end_point, PATH_WIDTH)
    
    def draw_robot(self, robot):
        """Draw the robot as an orange circle at its current position."""
        robot_center = self.get_cell_center(robot.current_pos)
        pygame.draw.circle(self.screen, ORANGE, robot_center, ROBOT_RADIUS)
    
    def get_cell_center(self, position):
        """Get the pixel coordinates of the center of a maze cell."""
        x, y = position
        center_x = x * CELL_SIZE + CELL_SIZE // 2
        center_y = y * CELL_SIZE + CELL_SIZE // 2
        return (center_x, center_y)
    
    def render_complete_scene(self, maze, robot):
        """Draw everything: maze, start/goal, robot trail, and robot."""
        self.draw_maze_background(maze)
        self.draw_start_and_goal(maze)
        self.draw_robot_trail(robot)
        self.draw_robot(robot)
        pygame.display.flip()


def create_example_maze():
    """Create a sample maze layout for testing."""
    return [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        [1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
        [1, 0, 1, 0, 0, 0, 0, 1, 0, 1],
        [1, 0, 1, 1, 1, 1, 0, 1, 0, 1],
        [1, 0, 0, 0, 0, 1, 0, 1, 0, 1],
        [1, 0, 1, 1, 0, 1, 0, 1, 0, 1],
        [1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
        [1, 1, 0, 0, 0, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]


def main():
    """Main function that runs the maze solving simulation."""
    # Initialize pygame
    pygame.init()
    clock = pygame.time.Clock()
    
    # Create maze and robot
    maze_layout = create_example_maze()
    start_pos = (1, 1)
    goal_pos = (8, 8)
    
    maze = Maze(maze_layout, start_pos, goal_pos)
    robot = MazeRobot(maze)
    renderer = MazeRenderer(maze)
    
    # Main simulation loop
    running = True
    goal_reached = False
    
    print("Starting maze navigation...")
    print("Algorithm: Left-hand wall following")
    
    while running:
        # Handle window close event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Update robot position if goal not reached
        if not goal_reached:
            if robot.has_reached_goal():
                goal_reached = True
                print("\n Success! Robot reached the goal!")
                print(f" Move sequence: {''.join(robot.move_history)}")
                print(f"Total steps taken: {len(robot.move_history)}")
            else:
                robot.execute_next_step()
                time.sleep(ANIMATION_DELAY)
        
        # Render the current state
        renderer.render_complete_scene(maze, robot)
        clock.tick(FPS)
    
    # Clean up
    pygame.quit()
    print("Simulation ended.")


if __name__ == '__main__':
    main()
