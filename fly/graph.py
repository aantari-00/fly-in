"""Graph representation and helper methods for routing."""

from typing import Any

HubData = dict[str, Any]
AdjacencyEntry = dict[str, Any]
Adjacency = dict[str, list[AdjacencyEntry]]


class Graph:
    """Store map data and expose graph operations."""

    def __init__(self, data: dict[str, Any]) -> None:
        """Initialize the graph from parsed map data."""
        self.nb_drones: int = data["count"]
        self.start: str = data["start_hub"][0]["name"]
        self.end: str = data["end_hub"][0]["name"]
        self.hubs: list[HubData] = data["Hubs"]
        # data (start & end)
        self.start_data: HubData = data["start_hub"][0]
        self.end_data: HubData = data["end_hub"][0]

        self.connections: list[dict[str, Any]] = data["Connections"]
        # adjacency list
        self.adjacency: Adjacency = self.build_adj()

    def get_zone(self, name: str) -> str:
        """Return the zone of the requested hub."""
        if name == self.start:
            return str(self.start_data.get("zone", "normal"))

        if name == self.end:
            return str(self.end_data.get("zone", "normal"))

        for hub in self.hubs:
            if hub["name"] == name:
                return str(hub.get("zone", "normal"))

        return "normal"

    def get_cost(self, name: str) -> int | None:
        """Return the traversal cost for a hub."""
        zone = self.get_zone(name)
        if zone in ["normal", "priority"]:
            return 1
        if zone == "restricted":
            return 2
        if zone == "blocked":
            return None
        return 1

    def get_capacity(self, name: str) -> float | int:
        """Return the maximum number of drones allowed at a hub."""
        if name == self.start or name == self.end:
            return float("inf")
        for hub in self.hubs:
            if hub["name"] == name:
                val = hub.get("max_drones", 1)
                return int(val)
        return 1

    def get_link_capacity(self, hub1: str, hub2: str) -> int:
        """Return the capacity of the link between two hubs."""
        for neighbor in self.adjacency[hub1]:
            if neighbor["to"] == hub2:
                return int(neighbor["capacity"])
        return 1

    def build_adj(self) -> Adjacency:
        """Build the adjacency list for the graph."""
        adj: Adjacency = {}

        adj[self.start] = []
        adj[self.end] = []

        for hub in self.hubs:
            adj[str(hub["name"])] = []

        for conn in self.connections:
            hub1 = str(conn["from_zone"])
            hub2 = str(conn["to_zone"])

            if (
                self.get_zone(hub1) == "blocked"
                or self.get_zone(hub2) == "blocked"
            ):
                continue

            cost_to_hub2 = self.get_cost(hub2)
            cost_to_hub1 = self.get_cost(hub1)

            adj[hub1].append(
                {
                    "to": hub2,
                    "cost": cost_to_hub2,
                    "capacity": conn.get("max_link_capacity", 1),
                }
            )

            adj[hub2].append(
                {
                    "to": hub1,
                    "cost": cost_to_hub1,
                    "capacity": conn.get("max_link_capacity", 1),
                }
            )

        return adj

    def remove_edge(
        self, hub1: str, hub2: str
    ) -> list[tuple[str, AdjacencyEntry]]:
        """Remove the edge b etween two hubs from the graph."""
        removed: list[tuple[str, AdjacencyEntry]] = []
        for entry in list(self.adjacency[hub1]):
            if entry["to"] == hub2:
                self.adjacency[hub1].remove(entry)
                removed.append((hub1, entry))

        for entry in list(self.adjacency[hub2]):
            if entry["to"] == hub1:
                self.adjacency[hub2].remove(entry)
                removed.append((hub2, entry))

        return removed

    def restore_edge(self, removed: list[tuple[str, AdjacencyEntry]]) -> None:
        """Restore an edge removed from the graph."""
        for hub, entry in removed:
            self.adjacency[hub].append(entry)

    def remove_node(self, hub: str) -> dict[str, Any]:
        """Remove a node from the graph and return the removed state."""
        removed: dict[str, Any] = {"node": None, "edges": []}

        if hub not in self.adjacency:
            return removed

        removed["node"] = (hub, self.adjacency.pop(hub))
        for current in list(self.adjacency):
            for entry in list(self.adjacency[current]):
                if entry["to"] == hub:
                    self.adjacency[current].remove(entry)
                    removed["edges"].append((current, entry))
        return removed

    def restore_node(self, removed: dict[str, Any]) -> None:
        """Restore a node removed from the graph."""
        hub, adjacency = removed["node"]

        self.adjacency[hub] = adjacency

        for current, entry in removed["edges"]:
            self.adjacency[current].append(entry)

    def path_cost(self, path: list[str]) -> int:
        """Compute the total path cost for a route."""
        cost = 0

        for hub in path[1:]:
            cost += self.get_cost(hub) or 0
        return cost
