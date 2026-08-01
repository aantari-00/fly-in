"""Graph representation and helper methods for routing."""


class Graph:
    """Store map data and expose graph operations."""

    def __init__(self, data: dict) -> None:
        """Initialize the graph from parsed map data."""
        self.nb_drones: int = data["count"]
        self.start: str = data["start_hub"][0]["name"]
        self.end: str = data["end_hub"][0]["name"]
        self.hubs: list = data["Hubs"]
        # data (start & end)
        self.start_data: dict = data["start_hub"][0]
        self.end_data: dict = data["end_hub"][0]

        self.connections: list = data["Connections"]
        # adjacency list
        self.adjacency: dict = self.build_adj()

    def get_zone(self, name: str) -> str:
        """Return the zone of the requested hub."""
        if name == self.start:
            return self.start_data.get("zone", "normal")

        if name == self.end:
            return self.end_data.get("zone", "normal")

        for hub in self.hubs:
            if hub["name"] == name:
                return hub.get("zone", "normal")

        return "normal"

    def get_cost(self, name: str) -> object:
        """Return the traversal cost for a hub."""
        zone = self.get_zone(name)
        if zone in ["normal", "priority"]:
            return 1
        if zone == "restricted":
            return 2
        if zone == "blocked":
            return None
        return 1

    def get_capacity(self, name: str) -> object:
        """Return the maximum number of drones allowed at a hub."""
        if name == self.start or name == self.end:
            return float("inf")
        for hub in self.hubs:
            if hub["name"] == name:
                val = hub.get("max_drones", 1)
                return int(val)
        return 1

    def get_link_capacity(self, hub1: str, hub2: str) -> object:
        """Return the capacity of the link between two hubs."""
        for neighbor in self.adjacency[hub1]:
            if neighbor["to"] == hub2:
                return int(neighbor["capacity"])
        return 1

    def build_adj(self) -> dict:
        """Build the adjacency list for the graph."""
        adj = {}

        adj[self.start] = []
        adj[self.end] = []

        for hub in self.hubs:
            adj[hub["name"]] = []

        for conn in self.connections:
            hub1 = conn["from_zone"]
            hub2 = conn["to_zone"]

            if self.get_zone(
                hub1
            ) == "blocked" or self.get_zone(hub2) == "blocked":
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

    def remove_edge(self, hub1: str, hub2: str) -> list:
        """Remove the edge between two hubs from the graph."""
        removed = []
        for entry in list(self.adjacency[hub1]):
            if entry["to"] == hub2:
                self.adjacency[hub1].remove(entry)
                removed.append((hub1, entry))

        for entry in list(self.adjacency[hub2]):
            if entry["to"] == hub1:
                self.adjacency[hub2].remove(entry)
                removed.append((hub2, entry))

        return removed

    def restore_edge(self, removed: list) -> None:
        """Restore an edge removed from the graph."""
        for hub, entry in removed:
            self.adjacency[hub].append(entry)

    def remove_node(self, hub: str) -> dict:
        """Remove a node from the graph and return the removed state."""
        removed = {"node": None, "edges": []}

        if hub not in self.adjacency:
            return removed

        removed["node"] = (hub, self.adjacency.pop(hub))
        for current in list(self.adjacency):
            for entry in list(self.adjacency[current]):
                if entry["to"] == hub:
                    self.adjacency[current].remove(entry)
                    removed["edges"].append((current, entry))
        return removed

    def restore_node(self, removed: dict) -> None:
        """Restore a node removed from the graph."""
        hub, adjacency = removed["node"]

        self.adjacency[hub] = adjacency

        for current, entry in removed["edges"]:
            self.adjacency[current].append(entry)

    def path_cost(self, path: list) -> int:
        """Compute the total path cost for a route."""
        cost = 0

        for hub in path[1:]:
            cost += self.get_cost(hub)
        return cost
