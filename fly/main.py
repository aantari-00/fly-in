from parser import parse_map
from graph import Graph
from Router import Router


def main():
    data = parse_map("map.txt")

    if data is None:
        print("Error: could not parse the map.")
        return

    graph = Graph(data)

    router = Router(graph)
    paths = router.find_paths()

    if not paths:
        print("No path found.")
        return

    print(f"Found {len(paths)} path(s):\n")

    for i, (path, cost) in enumerate(paths, start=1):
        print(f"Path {i}: {' -> '.join(path)}")
        print(f"Cost: {cost}")
        print()


if __name__ == "__main__":
    main()
