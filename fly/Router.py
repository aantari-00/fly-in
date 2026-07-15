from dijkstra import Dijkstra


class Router:

    def __init__(self, graph):
        self.graph = graph
        self.dijkstra = Dijkstra(graph)

def find_paths(self, max_path=10):
    first = self.dijkstra.get_path()
    if first is None:
        return []

    accepted = [first]

    while len(accepted) < max_path:
        candidates = []

        previous_path, _ = accepted[-1]

        for i in range(len(previous_path) - 1):

            spur_node = previous_path[i]
            root_path = previous_path[:i + 1]

            removed_edges = self.block_known_edges(accepted, root_path, i)
            removed_nodes = self.block_root_nodes(root_path)

            spur = self.dijkstra.get_path(source=spur_node)

            self.restore_root_nodes(removed_nodes)
            self.restore_known_edges(removed_edges)

            if spur is None:
                continue

            spur_path, spur_cost = spur

            total_path = root_path[:-1] + spur_path

            total_cost = len(total_path) - 1

            self.add_candidate(
                candidates,
                accepted,
                total_path,
                total_cost
            )

        if not candidates:
            break

        candidates.sort(key=lambda x: x[1])

        accepted.append(candidates.pop(0))

    return accepted

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
        self.graph.restore_edge(removed)

    def block_root_nodes(self, root_path):
        removed_nodes = []
        for hub in root_path[:-1]:
            removed = self.graph.removed_node(hub)
            removed_nodes.append(removed)
        return removed_nodes

    def restore_root_nodes(self, removed_nodes):
        for removed in removed_nodes:
            self.graph.restore_node(removed_nodes)

    def add_candidate(self, candidates, accepted, path, cost):
        if path is None:
            return
    
        for accepted_path, _ in accepted:
            if accepted_path == path:
                return
    
        for candidate_path, _ in candidates:
            if candidate_path == path:
                return
    
        candidates.append((path, cost))
