from parser import parse_map
from graph import Graph
from dijkstra import Dijkstra


def main():
    data = parse_map("map.txt")
    graph = Graph(data)
    dijkstra = Dijkstra(graph)
    path, cost = dijkstra.get_path()
    print(path)
    print(cost)


if __name__ == "__main__":
    main()
