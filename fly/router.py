from typing import Any
from dijkstra import Dijkstra
from drone import Drone

PathCandidate = tuple[list[str], float]


class Router:
    """Build candidate paths and assign drones to them."""

    def __init__(self, graph: Any) -> None:
        """Initialize the router with a graph and a shortest-path solver."""
        self.graph = graph
        self.dijkstra = Dijkstra(graph)

    def find_paths(self, max_path: int = 20) -> list[PathCandidate]:
        """Find candidate paths up to the requested maximum count."""
        first = self.dijkstra.get_path()
        if first is None:
            return []

        accepted: list[PathCandidate] = [first]
        candidates: list[PathCandidate] = []
        while len(accepted) < max_path:
            previous_path, _ = accepted[-1]

            for i in range(len(previous_path) - 1):
                spur_node = previous_path[i]
                root_path = previous_path[: i + 1]
                removed_edges = self.block_known_edges(accepted, root_path, i)
                removed_nodes = self.block_root_nodes(root_path)
                new_path = self.dijkstra.get_path(source=spur_node)
                self.restore_root_nodes(removed_nodes)
                self.restore_known_edges(removed_edges)
                if new_path is None:
                    continue
                n_path, _ = new_path
                total_path = root_path[:-1] + n_path
                total_cost = float(self.graph.path_cost(total_path))
                self.add_candidate(
                    candidates, accepted, total_path, total_cost
                )

            if not candidates:
                break

            candidates.sort(key=lambda x: x[1])
            accepted.append(candidates.pop(0))
        path_cost = [
            (path, cost) for path, cost in accepted if cost == first[1]
        ]
        if not path_cost:
            return accepted

        return path_cost or accepted

    def block_known_edges(
        self,
        accepted: list[PathCandidate],
        root_path: list[str],
        spur_index: int,
    ) -> list[tuple[str, dict[str, Any]]]:
        """Remove edges already used by accepted paths for this root."""
        removed: list[tuple[str, dict[str, Any]]] = []

        for path, _ in accepted:
            if path[: spur_index + 1] == root_path:
                if len(path) > spur_index + 1:
                    hub1 = path[spur_index]
                    hub2 = path[spur_index + 1]
                    removed += self.graph.remove_edge(hub1, hub2)

        return removed

    def restore_known_edges(
        self, removed: list[tuple[str, dict[str, Any]]]
    ) -> None:
        """Restore edges removed during path exploration."""
        self.graph.restore_edge(removed)

    def block_root_nodes(self, root_path: list[str]) -> list[dict[str, Any]]:
        """Remove the root path nodes to avoid reusing them."""
        removed_nodes: list[dict[str, Any]] = []
        for hub in root_path[:-1]:
            removed = self.graph.remove_node(hub)
            removed_nodes.append(removed)
        return removed_nodes

    def restore_root_nodes(self, removed_nodes: list[dict[str, Any]]) -> None:
        """Restore nodes removed during path exploration."""
        for removed in reversed(removed_nodes):
            self.graph.restore_node(removed)

    def add_candidate(
        self,
        candidates: list[PathCandidate],
        accepted: list[PathCandidate],
        path: list[str],
        cost: float,
    ) -> None:
        """Add a new candidate path if it is not already known."""
        for accepted_path, _ in accepted:
            if accepted_path == path:
                return
        for candidate_path, _ in candidates:
            if candidate_path == path:
                return

        candidates.append((path, cost))

    def assign_drones(
        self, paths: list[PathCandidate], nb_drones: int
    ) -> list[Drone]:
        """Assign drones to the available paths using simple load balancing."""
        loads: list[int] = [0] * len(paths)
        drones: list[Drone] = []

        for drone_id in range(1, nb_drones + 1):
            best = loads.index(min(loads))

            path, _ = paths[best]
            drones.append(Drone(drone_id, path))

            loads[best] += 1

        return drones
