class Dijkstra:

    def __init__(self, graph):
        self.graph = graph

    def initialize(self):
        distance = {}
        previous = {}
        visited = set()

        for hub in self.graph.adjacency:
            distance[hub] = float("inf")
            previous[hub] = None

        distance[self.graph.start] = 0

        return distance, previous, visited

    def get_min_node(self, distance, visited):
        min_node = None

        for hub in distance:
            if hub in visited:
                continue

            if min_node is None or distance[hub] < distance[min_node]:
                min_node = hub

        return min_node

    def shortest_path(self):
        distance, previous, visited = self.initialize()

        while True:
            current = self.get_min_node(distance, visited)

            if current is None:
                break

            if current == self.graph.end:
                break

            visited.add(current)

            for edge in self.graph.adjacency[current]:

                neighbor = edge["to"]
                cost = edge["cost"]

                if neighbor in visited:
                    continue

                new_distance = distance[current] + cost

                if new_distance < distance[neighbor]:
                    distance[neighbor] = new_distance
                    previous[neighbor] = current

        return distance, previous

    def get_path(self):
        distance, previous = self.shortest_path()

        path = []
        current = self.graph.end

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()

        if path[0] != self.graph.start:
            return None

        return path, distance[self.graph.end]