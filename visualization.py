import math
import random
from typing import Any
import pygame

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
HUB_PAUSE_SECONDS = 1.0


class Visualization:
    """Render the simulation state as an animated map."""

    def __init__(
        self,
        graph: Any,
        drones: list[Any],
        turns: list[list[str]],
        width: int = 1600,
        height: int = 950,
        turn_duration: float = 1.0,
        fps: int = 60,
    ) -> None:
        self.graph = graph
        self.drones = drones
        self.turns = turns
        self.width = width
        self.height = height
        self.turn_duration = turn_duration
        self.fps = fps
        self.sidebar_width = 200
        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 2.5
        self.zoom_step = 0.1
        self.hub_pause_duration = HUB_PAUSE_SECONDS / 3.0

        pygame.init()
        pygame.display.set_caption("Fly-in -> (safe🐍)")
        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.RESIZABLE
        )
        self.title_font = pygame.font.SysFont("Courier New", 26, bold=True)
        self.label_font = pygame.font.SysFont("Courier New", 16)
        self.small_font = pygame.font.SysFont("segoeui", 14)

        self.node_positions = self.compute_node_positions()
        self.timeline = self.build_timeline()
        self.drone_playback = self.init_drone_playback()

        self.paused = False
        self.running = True
        self.status = "Running" if any(self.timeline.values()) else "Finished"
        self.starfield_surface = self.generate_starfield(self.width,
                                                         self.height)

    def generate_starfield(self, width: int, height: int) -> pygame.Surface:
        surface = pygame.Surface((width, height))
        surface.fill(BACKGROUND_COLOR)
        for _ in range((width * height) // 2500):
            x, y = random.randint(0, width), random.randint(0, height)
            radius = random.choices([1, 2, 3], weights=[85, 10, 5])[0]
            shade = random.randint(100, 255)
            color = (shade, shade, random.randint(shade, 255))
            pygame.draw.circle(surface, color, (x, y), radius)
        return surface

    def get_hub_coordinates(self) -> dict[str, tuple[int, int]]:
        coords = {
            self.graph.start: (self.graph.start_data["x"],
                               self.graph.start_data["y"]),
            self.graph.end: (self.graph.end_data["x"],
                             self.graph.end_data["y"]),
        }
        for hub in self.graph.hubs:
            coords[hub["name"]] = (hub["x"], hub["y"])
        return coords

    def compute_node_positions(self) -> dict[str, tuple[float, float]]:
        coords = self.get_hub_coordinates()
        xs, ys = [p[0] for p in coords.values()], [p[1]
                                                   for p in coords.values()]
        min_x, min_y = min(xs), min(ys)
        x_range, y_range = max(max(xs) - min_x, 1), max(max(ys) - min_y, 1)

        margin = 80
        play_width = self.width - self.sidebar_width - margin * 2
        play_height = self.height - margin * 2

        positions = {
            name: (
                margin + (x - min_x) / x_range * play_width,
                margin + (y - min_y) / y_range * play_height,
            )
            for name, (x, y) in coords.items()
        }
        self.zoom_center = (margin + play_width / 2, margin + play_height / 2)
        return positions

    def parse_move(self, move_text: str) -> tuple[int, str, Any]:
        """Parse a move string into (drone_id, kind, data)."""
        raw_id, *hubs = move_text[1:].split("-")
        drone_id = int(raw_id)
        if len(hubs) == 1:
            return drone_id, "direct", hubs[0]
        return drone_id, "start_transit", (hubs[0], hubs[1])

    def per_turn_events(self) -> list[dict[int, tuple[str, Any]]]:
        """Return, per turn, a dict of drone_id -> (kind, data)."""
        events_by_turn = []
        for turn_moves in self.turns:
            events = {}
            for move in turn_moves:
                drone_id, kind, data = self.parse_move(move)
                events[drone_id] = (kind, data)
            events_by_turn.append(events)
        return events_by_turn

    def occupied_hubs_per_turn(
        self,
        drone_id: int,
        start_hub: str,
        events_by_turn: list[dict[int, tuple[str, Any]]],
    ) -> list[tuple[str, str]]:
        """Return the (from_hub, to_hub) pair the drone occupies each turn."""
        hub = start_hub
        transit: tuple[str, str, int, int] | None = None
        occupied: list[tuple[str, str]] = []

        for events in events_by_turn:
            event = events.get(drone_id)

            if transit and event:
                kind, data = event
                if (kind == "direct" and data == transit[1]) or (
                    kind == "start_transit" and data == transit[:2]
                ):
                    event = None

            if event is None:
                if transit:
                    frm, to, total, elapsed = transit
                    elapsed += 1
                    occupied.append((frm, to))
                    transit = None if elapsed >= total else (
                        frm, to, total, elapsed)
                    if transit is None:
                        hub = to
                else:
                    occupied.append((hub, hub))
                continue

            kind, data = event
            if kind == "direct":
                occupied.append((hub, data))
                hub = data
                transit = None
            else:  # start_transit
                frm, to = data
                total = self.graph.get_cost(to) or 1
                transit = (frm, to, total, 1)
                occupied.append((frm, to))

        return occupied

    def encode_segments(
        self, occupied: list[tuple[str, str]], final_hub: str
    ) -> list[dict[str, Any]]:
        """Run-length encode per-turn
        (from, to) pairs into move/wait segments."""
        segments: list[dict[str, Any]] = []
        i, n = 0, len(occupied)
        while i < n:
            frm, to = occupied[i]
            run = 1
            while i + run < n and occupied[i + run] == (frm, to):
                run += 1

            if frm == to:
                segments.append(
                    {"type": "wait", "hub": frm,
                     "duration": run * self.turn_duration}
                )
            else:
                segments.append(
                    {
                        "type": "move",
                        "from": frm,
                        "to": to,
                        "duration": run * self.turn_duration,
                    }
                )
                if to != final_hub:
                    segments.append(
                        {"type": "wait", "hub": to,
                            "duration": self.hub_pause_duration}
                    )
            i += run
        return segments

    def build_timeline(self) -> dict[int, list[dict[str, Any]]]:
        events_by_turn = self.per_turn_events()
        timeline = {}
        for drone in self.drones:
            occupied = self.occupied_hubs_per_turn(
                drone.drone_id, drone.path[0], events_by_turn
            )
            timeline[drone.drone_id] = self.encode_segments(
                occupied, drone.path[-1])
        return timeline

    def init_drone_playback(self) -> dict[int, dict[str, Any]]:
        return {
            drone.drone_id: {"segment_index": 0, "segment_elapsed": 0.0}
            for drone in self.drones
        }

    def handle_zoom(self, wheel_direction: int) -> None:
        self.zoom = max(
            self.min_zoom,
            min(self.zoom + wheel_direction * self.zoom_step, self.max_zoom),
        )

    def apply_zoom(self, position: tuple) -> tuple:
        cx, cy = self.zoom_center
        x, y = position
        return cx + (x - cx) * self.zoom, cy + (y - cy) * self.zoom

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode(
                    (self.width, self.height), pygame.RESIZABLE
                )
                self.node_positions = self.compute_node_positions()
                self.starfield_surface = self.generate_starfield(
                    self.width, self.height)
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)
            elif event.type == pygame.MOUSEWHEEL:
                self.handle_zoom(event.y)

    def handle_key(self, key: int) -> None:
        if key in (pygame.K_q, pygame.K_ESCAPE):
            self.running = False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
        elif key == pygame.K_s:
            self.drone_playback = self.init_drone_playback()
            self.paused = False
            self.status = "Running" if any(
                self.timeline.values()) else "Finished"

    def update(self, dt: float) -> None:
        if self.paused or self.status == "Finished":
            return

        all_finished = True
        for drone in self.drones:
            segments = self.timeline[drone.drone_id]
            state = self.drone_playback[drone.drone_id]
            if state["segment_index"] >= len(segments):
                continue

            all_finished = False
            state["segment_elapsed"] += dt
            while (
                state["segment_index"] < len(segments)
                and state["segment_elapsed"] >= segments[
                    state["segment_index"]]["duration"]
            ):
                state["segment_elapsed"] -= segments[state[
                    "segment_index"]]["duration"]
                state["segment_index"] += 1

        if all_finished:
            self.status = "Finished"

    def drone_is_finished(self, drone_id: int) -> bool:
        state = self.drone_playback[drone_id]
        return int(state["segment_index"]) >= len(self.timeline[drone_id])

    def get_drone_position(self, drone_id: int) -> tuple:
        segments = self.timeline[drone_id]
        if not segments:
            drone = next(d for d in self.drones if d.drone_id == drone_id)
            return self.apply_zoom(self.node_positions[drone.path[0]])

        state = self.drone_playback[drone_id]
        finished = state["segment_index"] >= len(segments)
        segment = segments[-1 if finished else state["segment_index"]]

        if segment["type"] == "wait":
            return self.apply_zoom(self.node_positions[segment["hub"]])

        duration = max(segment["duration"], 1e-6)
        elapsed = segment["duration"] if finished else state["segment_elapsed"]
        fraction = max(0.0, min(elapsed / duration, 1.0))

        from_pos = self.node_positions[segment["from"]]
        to_pos = self.node_positions[segment["to"]]
        x = from_pos[0] + (to_pos[0] - from_pos[0]) * fraction
        y = from_pos[1] + (to_pos[1] - from_pos[1]) * fraction
        return self.apply_zoom((x, y))

    def get_hub_color(self, hub_name: str) -> Any:
        if hub_name == self.graph.start:
            return self.graph.start_data.get("color")
        if hub_name == self.graph.end:
            return self.graph.end_data.get("color")
        for hub in self.graph.hubs:
            if hub["name"] == hub_name:
                return hub.get("color")
        return None

    def get_node_color(self, hub_name: str, zone: str) -> Any:
        explicit_color = self.get_hub_color(hub_name)
        if explicit_color:
            try:
                return pygame.Color(explicit_color)
            except ValueError:
                pass
        return ZONE_COLORS.get(zone, LINE_COLOR)

    def draw_edges(self) -> None:
        drawn = set()
        for hub_name, neighbors in self.graph.adjacency.items():
            for neighbor in neighbors:
                edge_key = frozenset((hub_name, neighbor["to"]))
                if edge_key in drawn:
                    continue
                drawn.add(edge_key)
                pygame.draw.line(
                    self.screen, LINE_COLOR,
                    self.apply_zoom(self.node_positions[hub_name]),
                    self.apply_zoom(self.node_positions[neighbor["to"]]),
                    2,
                )

    def draw_nodes(self) -> None:
        radius = 46 * self.zoom
        for hub_name, position in self.node_positions.items():
            pos = self.apply_zoom(position)
            zone = self.graph.get_zone(hub_name)
            color = self.get_node_color(hub_name, zone)

            pygame.draw.circle(self.screen, BACKGROUND_COLOR, pos, radius)
            pygame.draw.circle(self.screen, color, pos, radius, 2)

            label = self.small_font.render(hub_name, True, TEXT_COLOR)
            self.screen.blit(label, label.get_rect(
                center=(pos[0], pos[1] - 6)))

            if zone != "normal":
                tag = self.small_font.render(zone, True, color)
                self.screen.blit(tag, tag.get_rect(
                    center=(pos[0], pos[1] + 14)))

    def group_drone_positions(self) -> dict[tuple[int, int], list[int]]:
        groups: dict[tuple[int, int], list[int]] = {}
        for drone in self.drones:
            x, y = self.get_drone_position(drone.drone_id)
            groups.setdefault((round(x / 12), round(y / 12)),
                              []).append(drone.drone_id)
        return groups

    def draw_drones(self) -> None:
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

                color = FINISHED_COLOR if self.drone_is_finished(
                    drone_id) else DRONE_COLOR
                pygame.draw.circle(self.screen, color, (x, y), drone_radius)
                pygame.draw.circle(
                    self.screen, BACKGROUND_COLOR, (x, y), drone_radius, 1)

                tag = self.small_font.render(
                    str(drone_id), True, BACKGROUND_COLOR)
                self.screen.blit(tag, tag.get_rect(center=(x, y)))

    def draw_sidebar(self) -> None:
        panel_x = self.width - self.sidebar_width
        pygame.draw.rect(
            self.screen, PANEL_COLOR, (panel_x, 0,
                                       self.sidebar_width, self.height)
        )
        pygame.draw.line(self.screen, LINE_COLOR,
                         (panel_x, 0), (panel_x, self.height), 2)

        self.screen.blit(self.title_font.render(
            "Fly-in", True, TEXT_COLOR), (panel_x + 24, 30))

        landed = sum(
            1 for d in self.drones if self.drone_is_finished(d.drone_id))
        info_lines = [
            f"Landed: {landed} / {len(self.drones)}",
            f"Status: {self.status}",
        ]
        for i, text in enumerate(info_lines):
            self.screen.blit(
                self.label_font.render(
                    text, True, TEXT_COLOR), (panel_x + 24, 96 + i * 30)
            )

        self.screen.blit(
            self.label_font.render(
                f"nb_drones: {len(self.drones)}", True, TEXT_COLOR),
            (panel_x + 24, 170),
        )

        self.screen.blit(
            self.label_font.render("Controls", True, TEXT_COLOR),
            (panel_x + 24, self.height - 130),
        )
        controls = ["space : pause / resume",
                    "s : restart", "q : quit", "scroll : zoom"]
        for i, line in enumerate(controls):
            self.screen.blit(
                self.small_font.render(line, True, DIM_TEXT_COLOR),
                (panel_x + 24, self.height - 100 + i * 22),
            )

    def draw(self) -> None:
        self.screen.blit(self.starfield_surface, (0, 0))
        self.draw_edges()
        self.draw_nodes()
        self.draw_drones()
        self.draw_sidebar()
        pygame.display.flip()

    def run(self) -> None:
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(self.fps) / 3000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()


def visualize(
    graph: object,
    drones: list,
    turns: list,
    use_pygame: bool = True,
    delay: float = 0.5,
) -> None:
    """Create and run the visualization if pygame is enabled."""
    if not use_pygame:
        return
    Visualization(graph, drones, turns, turn_duration=delay).run()
