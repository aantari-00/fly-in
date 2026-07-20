from parser import parse_map
from graph import Graph
from router import Router
from drone import Drone
from simulation import Simulation


def main():
    # parsing
    data = parse_map("map.txt")
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
    turns = simulation.run()

    for i, turn in enumerate(turns, start=1):
        print(f"Turn {i}: {' '.join(turn)}")


if __name__ == "__main__":
    main()
