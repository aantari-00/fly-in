"""Drone state and movement helpers."""


class Drone:
    """Represent a drone following a predefined path."""

    def __init__(self, drone_id: int, path: list[str]) -> None:
        """Initialize the drone with an identifier and route."""
        self.drone_id = drone_id
        self.path = path
        self.path_index = 0
        self.finished = False

    def current_hub(self) -> str:
        """Return the current hub of the drone."""
        return self.path[self.path_index]

    def next_hub(self) -> str | None:
        """Return the next hub in the route if one exists."""
        if self.path_index + 1 < len(self.path):
            return self.path[self.path_index + 1]
        return None

    def move(self) -> None:
        """Advance the drone along its path."""
        if self.finished:
            return

        if self.path_index < len(self.path) - 1:
            self.path_index += 1

        if self.path_index == len(self.path) - 1:
            self.finished = True
