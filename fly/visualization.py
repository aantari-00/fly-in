import math

import pygame

# --- colors -----------------------------------------------------------
BACKGROUND_COLOR = (12, 12, 16)
PANEL_COLOR = (20, 20, 26)
LINE_COLOR = (235, 235, 235)
TEXT_COLOR = (235, 235, 235)
DIM_TEXT_COLOR = (40, 140, 150)
DRONE_COLOR = (255, 176, 9)
FINISHED_COLOR = (90, 200, 130)
ZONE_COLORS = {
    "restricted": (90, 150, 235),
    "blocked": (200, 70, 70),
    "priority": (235, 200, 90),
    "normal": (235, 235, 235),
}


class Visualization:
    def __init__(self, graph, drones, turns, width=1100,
                 height=650, turn_duration=0.5, fps=60):
        self.graph = graph
        self.drones = drones
        self.turns = turns

        self.width = width
        self.height = height
        self.sidebar_width = 260
        self.turn_duration = turn_duration
        self.fps = fps

        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 2.5
        self.zoom_step = 0.1

        pygame.init()
        pygame.display.set_caption("Fly-in - Drone Network")
        self.screen = pygame.display.set_mode((self.width, self.height),
                                              pygame.RESIZABLE)

        self.title_font = pygame.font.SysFont("segoeui", 26, bold=True)
        self.label_font = pygame.font.SysFont("segoeui", 16)
        self.small_font = pygame.font.SysFont("segoeui", 14)

        self.node_positions = self.compute_node_positions()
        self.schedule = self.build_schedule()

        # Playback state.
        self.current_turn = 0
        self.turn_timer = 0.0
        self.turn_progress = 0.0
        self.paused = False
        self.running = True
        self.status = "Running" if self.turns else "Finished"

    def get_hub_coordinates(self):
        coords = {
            self.graph.start: (
                self.graph.start_data["x"],
                self.graph.start_data["y"],
            ),
            self.graph.end: (
                self.graph.end_data["x"],
                self.graph.end_data["y"],
            ),
        }
        for hub in self.graph.hubs:
            coords[hub["name"]] = (hub["x"], hub["y"])
        return coords

    def compute_node_positions(self):
        coords = self.get_hub_coordinates()

        xs = [pos[0] for pos in coords.values()]
        ys = [pos[1] for pos in coords.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        x_range = max(max_x - min_x, 1)
        y_range = max(max_y - min_y, 1)

        margin = 90
        play_width = self.width - self.sidebar_width - margin * 2
        play_height = self.height - margin * 2

        positions = {}
        for name, (x, y) in coords.items():
            px = margin + (x - min_x) / x_range * play_width
            py = margin + (y - min_y) / y_range * play_height
            positions[name] = (px, py)

        self.zoom_center = (
            margin + play_width / 2,
            margin + play_height / 2,
        )

        return positions

    def apply_zoom(self, position):
        # Scale a point around the graph's center by the current zoom.
        cx, cy = self.zoom_center
        x, y = position
        zx = cx + (x - cx) * self.zoom
        zy = cy + (y - cy) * self.zoom
        return zx, zy

    def parse_move(self, move_text):
        # Read one move string and say what it means.
        # kind == "arrive"        -> data is the hub the drone reached
        # kind == "direct"        -> data is the hub the drone moved to
        #                            in a single turn
        # kind == "start_transit" -> data is (from_hub, to_hub), the
        #                            drone begins crossing a slow link
        if "->" in move_text:
            left, target_hub = move_text.split("->")
            drone_id = int(left[1:])
            return drone_id, "arrive", target_hub

        body = move_text[1:]  # drop the leading "D"
        parts = body.split("-")
        drone_id = int(parts[0])
        hubs = parts[1:]

        if len(hubs) == 1:
            return drone_id, "direct", hubs[0]
        return drone_id, "start_transit", (hubs[0], hubs[1])

    def build_schedule(self):
        # Precompute where every drone is, turn by turn. This only reads
        # data that already exists (the turns list, the drones' paths,
        # and graph.get_cost). It does not run any pathfinding or
        # simulation logic itself.
        schedule = {}
        state = {}

        for drone in self.drones:
            state[drone.drone_id] = {
                "hub": drone.path[0],
                "transit_from": None,
                "transit_to": None,
                "transit_total": 1,
                "transit_elapsed": 0,
            }
            schedule[drone.drone_id] = []

        for turn_moves in self.turns:
            events = {}
            for move_text in turn_moves:
                drone_id, kind, data = self.parse_move(move_text)
                events[drone_id] = (kind, data)

            for drone in self.drones:
                entry = self.advance_drone_state(
                    state[drone.drone_id], events.get(drone.drone_id)
                )
                schedule[drone.drone_id].append(entry)

        return schedule

    def advance_drone_state(self, state, event):
        # Move one drone's state forward by a single turn.
        # Returns the schedule entry describing the drone's motion
        # during this turn.
        if event is None:
            return self.advance_without_event(state)

        kind, data = event

        if kind == "direct":
            from_hub = state["hub"]
            to_hub = str(data)
            state["hub"] = to_hub
            state["transit_to"] = None
            return from_hub, to_hub, 0.0, 1.0

        if kind == "start_transit":
            from_hub, to_hub = data
            total_turns = self.graph.get_cost(to_hub) or 1
            state["transit_from"] = from_hub
            state["transit_to"] = to_hub
            state["transit_total"] = total_turns
            state["transit_elapsed"] = 1
            end_fraction = min(1.0 / total_turns, 1.0)
            return from_hub, to_hub, 0.0, end_fraction

        # kind == "arrive": confirms the drone reached the target hub.
        to_hub = str(data)
        from_hub = state["transit_from"] or state["hub"]
        total_turns = state["transit_total"]
        start_fraction = min(state["transit_elapsed"] / total_turns, 1.0)
        state["hub"] = to_hub
        state["transit_from"] = None
        state["transit_to"] = None
        return from_hub, to_hub, start_fraction, 1.0

    def advance_without_event(self, state):
        # Handle a turn where a drone had no move (waiting, or finished).
        if state["transit_to"] is None:
            # Idle: staying at the same hub (finished, or blocked/waiting).
            return state["hub"], state["hub"], 0.0, 0.0

        # Mid-way through a multi-turn link, keep gliding toward the target.
        total_turns = state["transit_total"]
        start_fraction = state["transit_elapsed"] / total_turns
        state["transit_elapsed"] += 1
        end_fraction = min(state["transit_elapsed"] / total_turns, 1.0)

        from_hub = state["transit_from"]
        to_hub = state["transit_to"]

        if state["transit_elapsed"] >= total_turns:
            state["hub"] = to_hub
            state["transit_from"] = None
            state["transit_to"] = None

        return from_hub, to_hub, start_fraction, end_fraction

    def handle_events(self):
        # React to window, keyboard and mouse events.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode(
                    (self.width, self.height), pygame.RESIZABLE
                )
                self.node_positions = self.compute_node_positions()

            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

            elif event.type == pygame.MOUSEWHEEL:
                self.handle_zoom(event.y)

    def handle_key(self, key):
        # Apply a single key press to the playback state.
        if key in (pygame.K_q, pygame.K_ESCAPE):
            self.running = False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_s:
            self.current_turn = 0
            self.turn_timer = 0.0
            self.paused = False
            self.status = "Running" if self.turns else "Finished"

    def handle_zoom(self, wheel_direction):
        # Zoom in or out around the center of the graph.
        self.zoom += wheel_direction * self.zoom_step
        self.zoom = max(self.min_zoom, min(self.zoom, self.max_zoom))

    def update(self, dt):
        # Advance the animation clock by dt seconds.
        if self.paused or self.status == "Finished":
            return

        self.turn_timer += dt
        self.turn_progress = min(self.turn_timer / self.turn_duration, 1.0)

        if self.turn_timer >= self.turn_duration:
            self.turn_timer = 0.0
            self.turn_progress = 0.0
            if self.current_turn < len(self.turns) - 1:
                self.current_turn += 1
            else:
                self.status = "Finished"

    def get_drone_position(self, drone_id):
        # Return the current pixel position of one drone, zoomed.
        entries = self.schedule[drone_id]
        index = min(self.current_turn, len(entries) - 1)
        from_hub, to_hub, start_fraction, end_fraction = entries[index]

        fraction = start_fraction + self.turn_progress * (end_fraction - start_fraction)
        fraction = max(0.0, min(fraction, 1.0))

        from_pos = self.node_positions[from_hub]
        to_pos = self.node_positions[to_hub]
        x = from_pos[0] + (to_pos[0] - from_pos[0]) * fraction
        y = from_pos[1] + (to_pos[1] - from_pos[1]) * fraction
        return self.apply_zoom((x, y))

    def draw_background(self):
        # Fill the whole window with the dark background color.
        self.screen.fill(BACKGROUND_COLOR)

    def hexagon_points(self, center, radius):
        # Compute the 6 corner points of a flat-top hexagon.
        points = []
        for i in range(6):
            angle = math.radians(60 * i)
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            points.append((x, y))
        return points

    def draw_edges(self):
        # Draw a white line for every connection between two hubs.
        drawn = set()
        for hub_name, neighbors in self.graph.adjacency.items():
            for neighbor in neighbors:
                other = neighbor["to"]
                edge_key = frozenset((hub_name, other))
                if edge_key in drawn:
                    continue
                drawn.add(edge_key)

                start_pos = self.apply_zoom(self.node_positions[hub_name])
                end_pos = self.apply_zoom(self.node_positions[other])
                pygame.draw.line(self.screen, LINE_COLOR, start_pos, end_pos, 2)

    def get_hub_color(self, hub_name):
        # Read the explicit "color" attribute for a hub, if the map
        # file provided one. Returns None when no color was set.
        if hub_name == self.graph.start:
            return self.graph.start_data.get("color")
        if hub_name == self.graph.end:
            return self.graph.end_data.get("color")
        for hub in self.graph.hubs:
            if hub["name"] == hub_name:
                return hub.get("color")
        return None

    def get_node_color(self, hub_name, zone):
        # Prefer the explicit color from the map. Only fall back to the
        # default zone color when no color was given.
        explicit_color = self.get_hub_color(hub_name)
        if explicit_color:
            try:
                return pygame.Color(explicit_color)
            except ValueError:
                pass
        return ZONE_COLORS.get(zone, LINE_COLOR)

    def draw_nodes(self):
        # Draw every hub as an outlined hexagon with its name.
        radius = 46 * self.zoom
        for hub_name, position in self.node_positions.items():
            zoomed_position = self.apply_zoom(position)
            zone = self.graph.get_zone(hub_name)
            outline_color = self.get_node_color(hub_name, zone)

            points = self.hexagon_points(zoomed_position, radius)
            pygame.draw.polygon(self.screen, BACKGROUND_COLOR, points)
            pygame.draw.polygon(self.screen, outline_color, points, 2)

            label = self.small_font.render(hub_name, True, TEXT_COLOR)
            label_rect = label.get_rect(
                center=(zoomed_position[0], zoomed_position[1] - 6)
            )
            self.screen.blit(label, label_rect)

            if zone != "normal":
                tag = self.small_font.render(zone, True, outline_color)
                tag_rect = tag.get_rect(
                    center=(zoomed_position[0], zoomed_position[1] + 14)
                )
                self.screen.blit(tag, tag_rect)

    def group_drone_positions(self):
        # Group drones that are currently very close together. This lets
        # us spread overlapping drones apart a little so they stay
        # readable, instead of drawing them exactly on top of each other.
        groups = {}
        for drone in self.drones:
            x, y = self.get_drone_position(drone.drone_id)
            bucket = (round(x / 12), round(y / 12))
            groups.setdefault(bucket, []).append(drone.drone_id)
        return groups

    def draw_drones(self):
        # Draw every drone as a small circle at its current position.
        groups = self.group_drone_positions()
        drone_radius = 8 * self.zoom
        spread = 14 * self.zoom

        for drone_ids in groups.values():
            count = len(drone_ids)
            for slot, drone_id in enumerate(drone_ids):
                x, y = self.get_drone_position(drone_id)

                if count > 1:
                    angle = math.radians(360 * slot / count)
                    x += math.cos(angle) * spread
                    y += math.sin(angle) * spread

                drone = next(d for d in self.drones if d.drone_id == drone_id)
                color = (
                    FINISHED_COLOR if self.drone_is_finished(drone_id) else DRONE_COLOR
                )
                pygame.draw.circle(self.screen, color, (x, y), drone_radius)
                pygame.draw.circle(
                    self.screen, BACKGROUND_COLOR, (x, y), drone_radius, 1
                )

                tag = self.small_font.render(
                    str(drone.drone_id), True, BACKGROUND_COLOR
                )
                self.screen.blit(tag, tag.get_rect(center=(x, y)))

    def drone_is_finished(self, drone_id):
        # Check, from the schedule, whether a drone has reached the end.
        entries = self.schedule[drone_id]
        index = min(self.current_turn, len(entries) - 1)
        _, to_hub, _, end_fraction = entries[index]
        drone = next(d for d in self.drones if d.drone_id == drone_id)
        at_last_turn = index == len(entries) - 1
        return to_hub == drone.path[-1] and end_fraction >= 1.0 and at_last_turn

    def draw_turn(self):
        # Draw the current turn number and simulation status.
        panel_x = self.width - self.sidebar_width
        turn_text = f"Turn: {self.current_turn + 1} / {max(len(self.turns), 1)}"
        turn_surface = self.label_font.render(turn_text, True, TEXT_COLOR)
        self.screen.blit(turn_surface, (panel_x + 24, 96))

        status_surface = self.label_font.render(
            f"Status: {self.status}", True, TEXT_COLOR
        )
        self.screen.blit(status_surface, (panel_x + 24, 126))

    def draw_sidebar(self):
        # Draw the right-side information panel.
        panel_x = self.width - self.sidebar_width
        panel_rect = pygame.Rect(panel_x, 0, self.sidebar_width, self.height)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel_rect)
        pygame.draw.line(
            self.screen, LINE_COLOR, (panel_x, 0), (panel_x, self.height), 2
        )

        title_surface = self.title_font.render("Fly-in", True, TEXT_COLOR)
        self.screen.blit(title_surface, (panel_x + 24, 30))

        self.draw_turn()

        drones_text = f"nb_drones: {len(self.drones)}"
        drones_surface = self.label_font.render(drones_text, True, TEXT_COLOR)
        self.screen.blit(drones_surface, (panel_x + 24, 170))

        finished_count = sum(
            1 for drone in self.drones if self.drone_is_finished(drone.drone_id)
        )
        landed_text = f"landed: {finished_count} / {len(self.drones)}"
        landed_surface = self.small_font.render(landed_text, True, DIM_TEXT_COLOR)
        self.screen.blit(landed_surface, (panel_x + 24, 196))

        controls_title = self.label_font.render("Controls", True, TEXT_COLOR)
        self.screen.blit(controls_title, (panel_x + 24, self.height - 130))

        controls = [
            "space : pause / resume",
            "s : restart",
            "q : quit",
            "scroll : zoom",
        ]
        for i, line in enumerate(controls):
            surface = self.small_font.render(line, True, DIM_TEXT_COLOR)
            self.screen.blit(surface, (panel_x + 24, self.height - 100 + i * 22))

    def draw(self):
        # Draw one full frame: background, graph, drones, then sidebar.
        self.draw_background()
        self.draw_edges()
        self.draw_nodes()
        self.draw_drones()
        self.draw_sidebar()
        pygame.display.flip()

    def run(self):
        # Run the visualization until the window is closed.
        clock = pygame.time.Clock()

        while self.running:
            dt = clock.tick(self.fps) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()


def visualize(graph, drones, turns, use_pygame=True, delay=0.5):
    # Small compatibility wrapper so main.py does not need to change.
    # Builds a Visualization and runs it. use_pygame is accepted for
    # backward compatibility with the previous function signature.
    if not use_pygame:
        return
    view = Visualization(graph, drones, turns, turn_duration=delay)
    view.run()
