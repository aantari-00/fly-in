from parser import parse_map
from graph import Graph
from router import Router
from simulation import Simulation
from visualization import Visualization
import sys


def main() -> None:
    """Run the parsing, routing, simulation, and visualization pipeline."""

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
    if not paths:
        print("No path found")
        return

    drones = router.assign_drones(paths, graph.nb_drones)
    simulation = Simulation(graph, drones)
    print("\033[H\033[J", end="\n")
    turns = simulation.run()

    for i, turn in enumerate(turns, start=1):
        print(f"Turn {i}: {' '.join(turn)}")
    view = Visualization(graph, drones, turns, turn_duration=0.3)
    view.run()
    return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
        sys.exit(0)
