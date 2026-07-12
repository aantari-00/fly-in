from dijkstra import Dijkstra


class Router:

    def __init__(self, graph):
        self.graph = graph
        self.dijkstra = Dijkstra(graph)

    def find_paths(self, max_path=10):
        first_path = self.dijkstra.get_path()
        if first_path is None:
            return []

        accepted = [first_path]
        candidates = []

        while len(accepted) < max_path:
            previous_path, _ = accepted[-1]
            for i in range(len(previous_path) - 1):
                spur_node = previous_path[i]
                root_path = previous_path[:i + 1]

                hub1 = previous_path[i]
                hub2 = previous_path[i + 1]
                removed = self.graph.remove_edge(hub1, hub2)

                new_path = self.dijkstra.get_path(source=spur_node)
                self.graph.restore_edge(removed)
                if new_path is not None:
                    if new_path not in accepted and new_path not in candidates:
                        candidates.append(new_path)
            if not candidates:
                break
            candidates.sort(key=lambda x: x[1])
            accepted.append(candidates.pop(0))

                         
def block_known_edges(self, accepted, root_path, spur_index):

    removed = []

    for path, _ in accepted:

        if path[:spur_index + 1] == root_path:

            if len(path) > spur_index + 1:

                hub1 = path[spur_index]
                hub2 = path[spur_index + 1]

                removed += self.graph.remove_edge(hub1, hub2)

    return removed 

    def restore_known_edges(self, removed):
        ...

    def block_root_nodes(self, root_path):
        ...

    def restore_root_nodes(self, removed_nodes):
        ...

    def add_candidate(self, candidates, accepted, path, cost):
        pass