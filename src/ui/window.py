"""
PyGame window management module.
"""

import pygame


class Window:
    """Manages the PyGame window."""

    def __init__(self, width: int = 800, height: int = 600, title: str = "Project Atom"):
        """
        Initialize window.

        Args:
            width: Window width in pixels.
            height: Window height in pixels.
            title: Window title.
        """
        self.width = width
        self.height = height
        self.title = title
        self.screen = None
        self.clock = None
        self.running = False

    def start(self):
        """Initialize PyGame and create window."""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()
        self.running = True

    def start_fullscreen(self):
        """Initialize PyGame in fullscreen mode."""
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()
        self.running = True

    def handle_events(self) -> bool:
        """
        Process PyGame events.

        Returns:
            False if window should close, True otherwise.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    self.running = False

        return self.running

    def clear(self, color: tuple = (0, 0, 0)):
        """Fill screen with a color (default black)."""
        self.screen.fill(color)

    def update(self, fps: int = 60):
        """Update display and maintain frame rate."""
        pygame.display.flip()
        self.clock.tick(fps)

    def stop(self):
        """Clean up and close PyGame."""
        pygame.quit()


def run_window_demo():
    """Demo: Basic PyGame window with a shape. Press 'q' or ESC to quit."""
    window = Window(800, 600, "Project Atom - PyGame Demo")
    window.start()

    print("PyGame window started! Press 'q' or ESC to quit.")

    while window.running:
        # Handle events
        window.handle_events()

        # Clear screen (dark gray background)
        window.clear((30, 30, 30))

        # Draw a rectangle
        pygame.draw.rect(window.screen, (0, 255, 0), (100, 100, 200, 150))

        # Draw a circle
        pygame.draw.circle(window.screen, (255, 0, 0), (500, 300), 80)

        # Update display
        window.update(60)

    window.stop()
    print("PyGame window closed.")


if __name__ == "__main__":
    run_window_demo()
