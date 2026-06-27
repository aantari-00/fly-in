class Graph:
    def __init__(self, data):
        self.nb_drones = data["count"]
        self.start = data["start_hub"][0]["name"]
        self.end = data["end_hub"][0]["name"]
        self.hubs = data["Hubs"]
        # data (start & end)
        self.start_data = data["start_hub"][0]
        self.end_data = data["end_hub"][0]

        self.connections = data["Connections"]
        # adjacency list
        self.adjacency = self.build_adj()

    def get_zone(self, name):

        if name == self.start:
            return self.start_data.get("zone", "normal")

        if name == self.end:
            return self.end_data.get("zone", "normal")

        for hub in self.hubs:
            if hub["name"] == name:
                return hub.get("zone", "normal")

        return "normal"

    def get_cost(self, name):
        zone = self.get_zone(name)
        if zone in ["normal", "priority"]:
            return 1
        if zone == "restricted":
            return 2
        if zone == "blocked":
            return None
        return 1

    def build_adj(self):
        adj = {}

        adj[self.start] = []
        adj[self.end] = []

        for hub in self.hubs:
            adj[hub["name"]] = []

        for conn in self.connections:
            hub1 = conn["from_zone"]
            hub2 = conn["to_zone"]

            if (self.get_zone(hub1) == "blocked"
                    or self.get_zone(hub2) == "blocked"):
                continue

            cost_to_hub2 = self.get_cost(hub2)
            cost_to_hub1 = self.get_cost(hub1)

            adj[hub1].append({
                "to": hub2,
                "cost": cost_to_hub2,
                "capacity": conn.get("max_link_capacity", 1)
            })

            adj[hub2].append({
                "to": hub1,
                "cost": cost_to_hub1,
                "capacity": conn.get("max_link_capacity", 1)
            })

        return adj
