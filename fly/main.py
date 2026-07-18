from parser import parse_map
from graph import Graph
from router import Router
from drone import Drone
from simulation import Simulation


def main():
    data = parse_map("map.txt")

    if data is None:
        print("Error parsing map")
        return

    graph = Graph(data)

    router = Router(graph)
    paths = router.find_paths()

    if not paths:
        print("No path found")
        return

    drones = []

    for i in range(graph.nb_drones):
        path, _ = paths[i % len(paths)]
        drones.append(Drone(i + 1, path))

    simulation = Simulation(graph, drones)
    turns = simulation.run()

    for i, turn in enumerate(turns, start=1):
        print(f"Turn {i}: {' '.join(turn)}")


if __name__ == "__main__":
    main()