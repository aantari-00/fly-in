from dijkstra import Dijkstra


class Router:
    # Finds several good start-to-end routes using Yen's algorithm, so
    # drones can be spread across different paths instead of all being
    # funneled through the single best one. It only orchestrates repeated
    # Dijkstra calls on a temporarily modified Graph, it does not know
    # anything about turns, drones or the simulation itself.

    def __init__(self, graph):
        self.graph = graph
        self.dijkstra = Dijkstra(graph)

    def find_paths(self, number_of_path):
        first = self.dijkstra.get_path()
        if first is None:
            return []

        accepted = [first]
        candidates = []

        while len(accepted) < number_of_path:
            previous_path, _ = accepted[-1]

            for i in range(len(previous_path) - 1):
                spur_node = previous_path[i]
                root_path = previous_path[:i + 1]

                removed_edges = self.block_known_edges(accepted, root_path, i)
                removed_nodes = self.block_root_nodes(root_path)

                spur_result = self.dijkstra.get_path(source=spur_node)

                if spur_result is not None:
                    spur_path, _ = spur_result
                    total_path = root_path[:-1] + spur_path
                    total_cost = self.graph.path_cost(total_path)
                    self.add_candidate(
                        candidates, accepted, total_path, total_cost)

                self.restore_root_nodes(removed_nodes)
                self.restore_known_edges(removed_edges)

            if not candidates:
                break

            candidates.sort(key=lambda candidate: candidate[1])
            accepted.append(candidates.pop(0))

        return accepted

    def block_known_edges(self, accepted, root_path, spur_index):
        # if an already-accepted path shares this same root, its next
        # step must be blocked so Dijkstra is forced to explore an
        # actually different spur path instead of re-finding it
        removed = []
        for path, _ in accepted:
            same_root = path[:spur_index + 1] == root_path
            if same_root and len(path) > spur_index + 1:
                hub1 = path[spur_index]
                hub2 = path[spur_index + 1]
                removed += self.graph.remove_edge(hub1, hub2)
        return removed

    def restore_known_edges(self, removed):
        self.graph.restore_edge(removed)

    def block_root_nodes(self, root_path):
        # every hub of the root path, except the spur node itself, is
        # removed so the spur path cannot loop back through it
        removed_nodes = []
        for hub in root_path[:-1]:
            removed_nodes.append((hub, self.graph.remove_node(hub)))
        return removed_nodes

    def restore_root_nodes(self, removed_nodes):
        for hub, removed in reversed(removed_nodes):
            self.graph.restore_node(removed)

    def add_candidate(self, candidates, accepted, path, cost):
        for existing_path, _ in accepted:
            if existing_path == path:
                return
        for existing_path, _ in candidates:
            if existing_path == path:
                return
        candidates.append((path, cost))