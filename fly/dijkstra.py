class Dijkstra:

    def __init__(self, graph):
        self.graph = graph

    def initialize(self):
        distance = {}
        previous = {}
        visited = set()
        for hub in self.graph.adjacency:
            distance[hub] = float('inf')
            previous[hub] = None
        distance[self.graph.start] = 0
        return distance, previous, visited

    def get_min_node(self, distance, visited):
        min_node = None
        for hub in distance:
            if hub in visited:
                continue
            if min_node is None:
                min_node = hub
            if distance[min_node] > distance[hub]:
                min_node = hub
        return min_node
    
    def shortest_path(self):
        distance, previous, visited = self.initialize()
        while True:
            current = self.get_min_node(distance, visited)
            if current is None:
                break
            visited.add(current)
            for neighbor in self.graph.adjacency[current]:
                hub = neighbor["to"]
                cost = neighbor["cost"]
                
                if hub in visited:
                    continue
                new_distance = distance[current] + cost
                if new_distance < distance[hub]:
                    distance[hub] = new_distance
                    previous[hub] = current
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