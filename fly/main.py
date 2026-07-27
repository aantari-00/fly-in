"""Entry point for running the fly-in simulation."""

from parser import parse_map
from graph import Graph
from router import Router
from simulation import Simulation
from visualization import Visualization
from types import FrameType
import signal
import sys


def main() -> None:
    """Run the parsing, routing, simulation, and visualization pipeline."""

    def handler(signum: int, frame: FrameType | None) -> None:
        if signum == signal.SIGQUIT:
            sys.exit(1)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGQUIT, handler)
    # parsing
    if len(sys.argv) != 2:
        print("Usage: python main.py <map_file>")
        return
    data = parse_map(sys.argv[1])
    if data is None:
        print("Error parsing map")
        return
    # graph
    graph = Graph(data)
    # router
    router = Router(graph)
    # path
    paths = router.find_paths()
    print(len(paths))
    if not paths:
        print("No path found")
        return

    drones = router.assign_drones(paths, graph.nb_drones)
    simulation = Simulation(graph, drones)
    turns = simulation.run()
    print(turns)

    for i, turn in enumerate(turns, start=1):
        print(f"Turn {i}: {' '.join(turn)}")
    view = Visualization(graph, drones, turns, turn_duration=0.3)
    view.run()
    return


if __name__ == "__main__":
    main()
