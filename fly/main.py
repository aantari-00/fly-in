from parser import parse_map
from graph import Graph
from dijkstra import Dijkstra
from drone import Drone
from simulation import Simulation


def main():
    # parsing
    data = parse_map("map.txt")
    # graph
    graph = Graph(data)
    # algo
    dijkstra = Dijkstra(graph)
    path, cost = dijkstra.get_path()
    # drones
    drones = []
    for i in range(graph.nb_drones):
        drones.append(Drone(i + 1, path))
    # simulation
    simulation = Simulation(graph, drones)
        

if __name__ == "__main__":
    main()
