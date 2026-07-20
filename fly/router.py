from dijkstra import Dijkstra
from drone import Drone


class Router:

    def __init__(self, graph):
        self.graph = graph
        self.dijkstra = Dijkstra(graph)

    def find_paths(self, max_path=20):
        first = self.dijkstra.get_path()
        if first is None:
            return []

        accepted = [first]
        candidates = []
        while len(accepted) < max_path:
            previous_path, _ = accepted[-1]

            for i in range(len(previous_path) - 1):
                spur_node = previous_path[i]
                root_path = previous_path[:i + 1]
                removed_edges = self.block_known_edges(accepted, root_path, i)
                removed_nodes = self.block_root_nodes(root_path)
                new_path = self.dijkstra.get_path(source=spur_node)
                self.restore_root_nodes(removed_nodes)
                self.restore_known_edges(removed_edges)
                if new_path is None:
                    continue
                n_path, _ = new_path
                total_path = root_path[:-1] + n_path
                total_cost = self.graph.path_cost(total_path)
                self.add_candidate(candidates, accepted,
                                   total_path, total_cost)

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
            removed = self.graph.remove_node(hub)
            removed_nodes.append(removed)
        return removed_nodes

    def restore_root_nodes(self, removed_nodes):
        for removed in reversed(removed_nodes):
            self.graph.restore_node(removed)

    def add_candidate(self, candidates, accepted, path, cost):
        for accepted_path, _ in accepted:
            if accepted_path == path:
                return
        for candidate_path, _ in candidates:
            if candidate_path == path:
                return

        candidates.append((path, cost))

    def assign_drones(self, paths, nb_drones):
        loads = [0] * len(paths)
        drones = []

        for drone_id in range(1, nb_drones + 1):
            best = min(range(len(paths)), key=lambda i: paths[i][1] + loads[i])

            path, _ = paths[best]
            drones.append(Drone(drone_id, path))

            loads[best] += 1

        return drones
