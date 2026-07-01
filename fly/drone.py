class Drone:
    def __init__(self, drone_id, path):
        self.drone_id = drone_id
        self.path = path
        self.path_index = 0
        self.finished = False

    def current_hub(self):
        return self.path[self.path_index]

    def next_hub(self):
        if self.path_index + 1 < len(self.path):
            return self.path[self.path_index + 1]
        return None

    def move(self):
        if self.finished:
            return

        if self.path_index < len(self.path) - 1:
            self.path_index += 1

        if self.path_index == len(self.path) - 1:
            self.finished = True
