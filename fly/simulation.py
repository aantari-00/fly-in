class Simulation:
    def __init__(self, graph, drones):
        self.graph = graph
        self.drones = drones
        self.turn = 0
        self.occupied_hubs = {}

    def can_move(self, current_hub, next_hub):
        pass
    
    def run(self):
        for drone in self.drones:
            if drone.finished:
                continue
            current_hub = drone.current_hub()
            next_hub = drone.next_hub()
