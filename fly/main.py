from parser import parse_map
from graph import Graph

from drone import Drone
from simulation import Simulation
from Router import Router

def main():
    # parsing
    data = parse_map("map.txt")
    if data is None:
        print("Error: could not parse the map file.")
        return

    # graph
    graph = Graph(data)

    # algo
    router = Router(graph)
    paths = router.find_paths()
    if not paths:
        print("Error: no path found between start and end.")
        return
    path, cost = paths[0]
    print(path)
    # drones
    drones = []
    for i in range(graph.nb_drones):
        drones.append(Drone(i + 1, path))

    # simulation
    simulation = Simulation(graph, drones)
    try:
        turns = simulation.run()
    except RuntimeError as e:
        print(f"Error: {e}")
        return
    i = 1
    for turn_moves in turns:
        print(f"turn{i}: "+" ".join(turn_moves))
        i += 1


if __name__ == "__main__":
    main()
