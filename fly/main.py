from parser import parse_map
from graph import Graph


def main():
    data = parse_map("map.txt")
    graph = Graph(data)
    print(graph.adjacency)


if __name__ == "__main__":
    main()
