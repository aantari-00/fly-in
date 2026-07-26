"""Alternative routing implementation for the sample project."""

from dijkstra import Dijkstra


class Router:
    """Build candidate paths for the sample routing flow."""

    def __init__(self, graph: object) -> None:
        """Initialize the router with a graph instance."""
        self.graph = graph
        self.dijkstra = Dijkstra(graph)

    def find_paths(self, k: int = 3) -> list:
        """Find candidate paths up to the requested maximum count."""
        first = self.dijkstra.get_path()
        if first is None:
            return []

        accepted = [first]

        candidates = []

        while len(accepted) < k:
            previous_path, _ = accepted[-1]

            for spur_index in range(len(previous_path) - 1):
                spur_node = previous_path[spur_index]
                root_path = previous_path[: (spur_index + 1)]

                removed_edges = self.block_known_edges(
                    accepted, root_path, spur_index)

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

        accepted.sort(key=lambda path_and_cost: path_and_cost[1])
        return accepted

    def block_known_edges(self, accepted: list, root_path: list, spur_index: int) -> list:
        """Remove edges already used by accepted paths for this root."""
        removed = []
        for path, _ in accepted:
            same_root = path[:spur_index + 1] == root_path
            if same_root and len(path) > spur_index + 1:
                hub1 = path[spur_index]
                hub2 = path[spur_index + 1]
                removed += self.graph.remove_edge(hub1, hub2)
        return removed

    def restore_known_edges(self, removed: list) -> None:
        """Restore edges removed during candidate exploration."""
        self.graph.restore_edge(removed)

    def block_root_nodes(self, root_path: list) -> list:
        """Remove the root path nodes to avoid reusing them."""
        removed_nodes = []
        for hub in root_path[:-1]:
            removed_nodes.append((hub, self.graph.remove_node(hub)))
        return removed_nodes

    def restore_root_nodes(self, removed_nodes: list) -> None:
        """Restore nodes removed during candidate exploration."""
        for hub, removed in reversed(removed_nodes):
            self.graph.restore_node(removed)

    def add_candidate(self, candidates: list, accepted: list, path: list, cost: int) -> None:
        """Add a candidate path if it is not already known."""
        for existing_path, _ in accepted:
            if existing_path == path:
                return
        for existing_path, _ in candidates:
            if existing_path == path:
                return
        candidates.append((path, cost))
