from parser import parse_map
from graph import Graph
from dijkstra import Dijkstra
from drone import Drone
from simulation import Simulation


def main():
    # parsing
    data = parse_map("map.txt")
    if data is None:
        print("Error: could not parse the map file.")
        return

    # graph
    graph = Graph(data)

    # algo
    dijkstra = Dijkstra(graph)
    result = dijkstra.get_path()
    if result is None:
        print("Error: no path found between start and end.")
        return
    path, cost = result

    # drones
    drones = []
    for i in range(graph.nb_drones):
        drones.append(Drone(i + 1, path))

    # simulation
    simulation = Simulation(graph, drones)
    turns = simulation.run()
    i = 1
    for turn_moves in turns:
        print(f"turn{i}: "+" ".join(turn_moves))
        i += 1


if __name__ == "__main__":
    main()
