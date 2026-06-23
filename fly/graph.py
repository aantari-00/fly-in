class Graph:
    def __init__(self, data):
        self.nb_droes = data["count"]
        self.start = data["start_hub"]
        self.end = data["end_hub"]
        self.hubs = data["Hubs"]
        self.connections = data["Connections"]
        # adjacency list
        self.adjacency = self.build_adj()

    def build_adj(self):
        adj = {}
        adj[self.start[0]["name"]] = []
        adj[self.end[0]["name"]] = []
        for hub in self.hubs:
            adj[hub["name"]] = []
        for conn in self.connections:
            hub1 = conn["from_zone"]
            hub2 = conn["to_zone"]
            adj[hub1].append(hub2)
            adj[hub2].append(hub1)
        return adj
