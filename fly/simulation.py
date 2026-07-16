class Simulation:
    def __init__(self, graph, drones):
        self.graph = graph
        self.drones = drones
        self.in_transit = {}
        self.turns = []

    def zone_occupancy(self):
        occupancy = {}
        for drone in self.drones:
            if drone.finished:
                continue
            if drone.drone_id in self.in_transit:
                target = self.in_transit[drone.drone_id]["target"]
                occupancy[target] = occupancy.get(target, 0) + 1
            else:
                hub = drone.current_hub()
                occupancy[hub] = occupancy.get(hub, 0) + 1
        return occupancy

    def link_occupancy(self):
        occupancy = {}
        for info in self.in_transit.values():
            link = info["link"]
            occupancy[link] = occupancy.get(link, 0) + 1
        return occupancy

    def resolve_arrivals(self, turn_moves):
        landed = set()
        for drone in self.drones:
            if drone.finished or drone.drone_id not in self.in_transit:
                continue

            info = self.in_transit[drone.drone_id]
            info["turns_left"] -= 1

            if info["turns_left"] == 0:
                drone.move()
                turn_moves.append(f"D{drone.drone_id}-{info['target']}")
                del self.in_transit[drone.drone_id]
                landed.add(drone.drone_id)

        return landed

    def try_move(self, drone, zone_occupancy, link_occupancy, turn_moves):
        current = drone.current_hub()
        next_hub = drone.next_hub()
        if next_hub is None:
            return

        cost = self.graph.get_cost(next_hub)
        capacity = self.graph.get_capacity(next_hub)

        if zone_occupancy.get(next_hub, 0) >= capacity:
            return

        link = tuple(sorted([current, next_hub]))
        link_capacity = self.graph.get_link_capacity(current, next_hub)

        if link_occupancy.get(link, 0) >= link_capacity:
            return

        zone_occupancy[next_hub] = zone_occupancy.get(next_hub, 0) + 1
        link_occupancy[link] = link_occupancy.get(link, 0) + 1

        if cost == 1:
            drone.move()
            turn_moves.append(f"D{drone.drone_id}-{next_hub}")
        else:
            self.in_transit[drone.drone_id] = {
                "target": next_hub,
                "turns_left": cost - 1,
                "link": link,
            }
            turn_moves.append(f"D{drone.drone_id}-{current}-{next_hub}")

    def run(self):
        max_turns = len(self.graph.adjacency) * len(self.drones) * 10

        while not all(drone.finished for drone in self.drones):
            turn_moves = []

            zone_occupancy = self.zone_occupancy()
            link_occupancy = self.link_occupancy()

            landed = self.resolve_arrivals(turn_moves)

            for drone in self.drones:
                if drone.finished or drone.drone_id in self.in_transit:
                    continue
                if drone.drone_id in landed:
                    continue
                self.try_move(
                    drone, zone_occupancy, link_occupancy, turn_moves)

            self.turns.append(turn_moves)

            if len(self.turns) > max_turns:
                raise RuntimeError(
                    "Simulation exceeded the maximum number of turns, "
                    "the map might be deadlocked")

        return self.turns
