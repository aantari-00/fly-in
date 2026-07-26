"""Shortest-path utilities for the drone routing project."""


class Dijkstra:
    """Solve shortest paths over the graph structure."""

    def __init__(self, graph: object) -> None:
        """Initialize the solver with a graph instance."""
        self.graph = graph

    def initialize(self, source: str) -> tuple:
        """Create the initial distance, previous, and visited state."""
        distance = {}
        previous = {}
        visited = set()

        for hub in self.graph.adjacency:
            distance[hub] = (float("inf"), float("inf"))
            previous[hub] = None

        distance[source] = (0, 0)

        return distance, previous, visited

    def get_min_node(self, distance: dict, visited: set) -> object:
        """Return the unvisited node with the smallest known distance."""
        min_node = None

        for hub in distance:
            if hub in visited:
                continue

            if min_node is None or distance[hub] < distance[min_node]:
                min_node = hub

        return min_node

    def shortest_path(self, source: str) -> tuple:
        """Compute the shortest path information from the given source."""
        distance, previous, visited = self.initialize(source)

        while True:
            current = self.get_min_node(distance, visited)
            if current is None:
                break
            visited.add(current)
            for neighbor in self.graph.adjacency[current]:
                hub = neighbor["to"]
                cost = neighbor["cost"]

                if hub in visited:
                    continue

                priority_score = distance[current][1]

                if self.graph.get_zone(hub) == "priority":
                    priority_score -= 1

                new_distance = (distance[current][0] + cost, priority_score)

                if new_distance < distance[hub]:
                    distance[hub] = new_distance
                    previous[hub] = current

        return distance, previous

    def get_path(self, source: object = None) -> object:
        """Return a path from the source to the graph end node."""
        if source is None:
            source = self.graph.start

        distance, previous = self.shortest_path(source)

        path = []
        current = self.graph.end

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()

        if not path or path[0] != source:
            return None

        return path, distance[self.graph.end][0]
