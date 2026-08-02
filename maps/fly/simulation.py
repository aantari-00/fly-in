from typing import Any
from drone import Drone


class Simulation:
    """Advance drone movement turn by turn while respecting capacities."""

    def __init__(self, graph: Any, drones: list[Drone]) -> None:
        """Initialize the simulation with a graph and drone list."""
        self.graph = graph
        self.drones = drones
        self.in_transit: dict[int, dict[str, Any]] = {}
        self.turns: list[list[str]] = []

    def zone_occupancy(self) -> dict[str, int]:
        """Return the current occupancy count for each hub."""
        occupancy: dict[str, int] = {}
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

    def link_occupancy(self) -> dict[tuple[str, str], int]:
        """Return the number of drones currently occupying each link."""
        occupancy: dict[tuple[str, str], int] = {}
        for info in self.in_transit.values():
            link = info["link"]
            occupancy[link] = occupancy.get(link, 0) + 1
        return occupancy

    def resolve_arrivals(self, turn_moves: list[str]) -> set[int]:
        """Advance drones that are currently completing transit moves."""
        landed: set[int] = set()
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

    def try_move(
        self,
        drone: Drone,
        zone_occupancy: dict[str, int],
        link_occupancy: dict[tuple[str, str], int],
        turn_moves: list[str],
    ) -> None:
        """Attempt to move a ready drone if the capacity rules allow it."""
        current = drone.current_hub()
        next_hub = drone.next_hub()
        if next_hub is None:
            return

        cost = self.graph.get_cost(next_hub)
        capacity = self.graph.get_capacity(next_hub)

        if zone_occupancy.get(next_hub, 0) >= capacity:
            return

        if current <= next_hub:
            link: tuple[str, str] = (current, next_hub)
        else:
            link = (next_hub, current)

        link_capacity = self.graph.get_link_capacity(current, next_hub)
        if link_occupancy.get(link, 0) >= link_capacity:
            return

        zone_occupancy[next_hub] = zone_occupancy.get(next_hub, 0) + 1
        link_occupancy[link] = link_occupancy.get(link, 0) + 1

        zone_occupancy[current] = zone_occupancy.get(current, 1) - 1

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

    def get_ready_drones(self, landed: set[int]) -> list[Drone]:
        """Return the drones that are ready to move in the current turn."""
        ready: list[Drone] = [
            drone
            for drone in self.drones
            if not drone.finished
            and drone.drone_id not in self.in_transit
            and drone.drone_id not in landed
        ]

        def remaining_cost(drone: Drone) -> int:
            index = drone.path_index + 1
            remaining_hubs = drone.path[index:]
            return sum(self.graph.get_cost(hub) or 0 for hub in remaining_hubs)

        ready.sort(key=remaining_cost)

        return ready

    def run(self) -> list[list[str]]:
        """Run the full simulation until all drones are finished."""
        max_turns = len(self.graph.adjacency) * len(self.drones) * 10

        while not all(drone.finished for drone in self.drones):
            turn_moves: list[str] = []

            landed = self.resolve_arrivals(turn_moves)
            zone_occupancy = self.zone_occupancy()
            link_occupancy = self.link_occupancy()

            for drone in self.get_ready_drones(landed):
                self.try_move(
                    drone, zone_occupancy, link_occupancy, turn_moves
                )
            self.turns.append(turn_moves)

            if len(self.turns) > max_turns:
                raise RuntimeError(
                    "Simulation exceeded the maximum number of turns, "
                    "the map might be deadlocked"
                )

        return self.turns
