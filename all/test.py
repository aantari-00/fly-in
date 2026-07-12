class Router:

    def __init__(self, graph):
        self.graph = graph
        self.dijkstra = Dijkstra(graph)

    def find_paths(self, k=5):
        ...

    def block_known_edges(self, accepted, root_path, spur_index):
        ...

    def restore_known_edges(self, removed):
        ...

    def block_root_nodes(self, root_path):
        ...

    def restore_root_nodes(self, removed_nodes):
        ...

    def add_candidate(self, candidates, accepted, path, cost):
        .