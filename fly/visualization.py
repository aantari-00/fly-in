import os
import time
import math


class VisualizationError(RuntimeError):
    """Raised when the visualization layer cannot render a frame."""


def parse_turn_move(move):
    parts = move.split("-")
    if not parts or not parts[0].startswith("D"):
        return None

    try:
        drone_id = int(parts[0][1:])
    except ValueError:
        return None

    target = parts[-1] if len(parts) >= 2 else None
    return drone_id, target


def build_animation_frames(graph, drones, turns):
    positions = {}
    for drone in drones:
        path = getattr(drone, "path", None) or []
        positions[drone.drone_id] = path[0] if path else None

    frames = []
    for turn_number, turn_moves in enumerate(turns, start=1):
        next_positions = dict(positions)
        for move in turn_moves:
            parsed = parse_turn_move(move)
            if parsed is None:
                continue
            drone_id, target = parsed
            if target is None:
                continue
            next_positions[drone_id] = target

        positions = next_positions
        frames.append({
            "turn": turn_number,
            "moves": list(turn_moves),
            "positions": dict(positions),
        })

    return frames


def render_text_frame(frame):
    lines = [f"Turn {frame['turn']}"]
    if frame["moves"]:
        lines.append("Moves: " + ", ".join(frame["moves"]))
    else:
        lines.append("Moves: none")

    for drone_id in sorted(frame["positions"]):
        hub = frame["positions"][drone_id]
        lines.append(f"  D{drone_id} -> {hub}")

    return "\n".join(lines)


def visualize(graph, drones, turns, *, use_pygame=False, delay=0.3,
              clear_screen=True):
    """Entry point used by ``main.py``.

    Only the *rendering* backend is chosen here. Whatever backend is used,
    it only reads ``graph``/``drones``/``turns`` - the routing/simulation
    result computed beforehand by ``Router``/``Simulation`` - and never
    changes it.
    """
    if use_pygame:
        try:
            import pygame  # noqa: F401
        except ImportError:
            use_pygame = False

    if use_pygame:
        _visualize_pygame(graph, drones, turns, delay)
        return

    frames = build_animation_frames(graph, drones, turns)
    _visualize_terminal(frames, delay=delay, clear_screen=clear_screen)


def _visualize_terminal(frames, *, delay=0.3, clear_screen=True):
    for frame in frames:
        if clear_screen:
            os.system("clear")
        print(render_text_frame(frame))
        if delay:
            time.sleep(delay)


BG_COLOR = (6, 7, 9)
PANEL_BG = (6, 7, 9)
PANEL_BORDER = (232, 234, 237)
EDGE_COLOR = (140, 145, 153)
EDGE_LABEL_COLOR = (120, 125, 133)
TEXT_COLOR = (235, 237, 240)
TEXT_MUTED = (148, 153, 161)

ZONE_COLORS = {
    "normal": (214, 218, 224),
    "restricted": (239, 83, 80),
    "priority": (38, 198, 173),
    "blocked": (95, 99, 107),
}
START_COLOR = (76, 217, 123)
END_COLOR = (250, 197, 61)

PANEL_WIDTH = 300


def _clamp(value, low, high):
    return max(low, min(high, value))


def _lerp(a, b, t):
    return a + (b - a) * t


def _ease(t):
    """Smoothstep easing so drone motion accelerates/decelerates."""
    t = _clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


class _Camera:
    """Maps world (map-file) coordinates to screen pixels.

    Handles auto-fit to the map, mouse-wheel zoom (around the cursor) and
    click-and-drag panning. Pure arithmetic, no pygame dependency, so this
    class stays importable even on machines without pygame installed.
    """

    def __init__(self, bounds, viewport):
        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._set_bounds(bounds)
        self.set_viewport(viewport)

    def _set_bounds(self, bounds):
        min_x, min_y, max_x, max_y = bounds
        self.center_x = (min_x + max_x) / 2
        self.center_y = (min_y + max_y) / 2
        self.world_w = max(max_x - min_x, 1)
        self.world_h = max(max_y - min_y, 1)

    def set_viewport(self, viewport):
        self.viewport_w, self.viewport_h = viewport
        margin = 130
        avail_w = max(self.viewport_w - margin * 2, 100)
        avail_h = max(self.viewport_h - margin * 2, 100)
        self.base_scale = min(avail_w / self.world_w,
                              avail_h / self.world_h)

    def world_to_screen(self, x, y):
        scale = self.base_scale * self.zoom
        sx = self.viewport_w / 2 + (x - self.center_x) * scale
        sy = self.viewport_h / 2 + (y - self.center_y) * scale
        return sx + self.offset_x, sy + self.offset_y

    def screen_to_world(self, pos):
        scale = self.base_scale * self.zoom
        x = (pos[0] - self.offset_x - self.viewport_w / 2)
        y = (pos[1] - self.offset_y - self.viewport_h / 2)
        return x / scale + self.center_x, y / scale + self.center_y

    def zoom_at(self, screen_pos, factor):
        world_pos = self.screen_to_world(screen_pos)
        self.zoom = _clamp(self.zoom * factor, 0.25, 6.0)
        new_screen = self.world_to_screen(*world_pos)
        self.offset_x += screen_pos[0] - new_screen[0]
        self.offset_y += screen_pos[1] - new_screen[1]

    def pan(self, dx, dy):
        self.offset_x += dx
        self.offset_y += dy


def _build_hub_coords(graph):
    coords = {
        graph.start: (graph.start_data["x"], graph.start_data["y"]),
        graph.end: (graph.end_data["x"], graph.end_data["y"]),
    }
    for hub in graph.hubs:
        coords[hub["name"]] = (hub["x"], hub["y"])
    return coords


def _build_edges(graph):
    seen = set()
    edges = []
    for hub_name, neighbors in graph.adjacency.items():
        for neighbor in neighbors:
            other = neighbor["to"]
            key = frozenset((hub_name, other))
            if key in seen:
                continue
            seen.add(key)
            edges.append((hub_name, other, neighbor.get("capacity", 1)))
    return edges


def _parse_drone_move(move):
    """Parse one entry of a simulation turn's move list.

    Recognises the three formats produced by ``Simulation``:
      ``D<id>-<zone>``        instantaneous move (cost 1)
      ``D<id>-<from>-<to>``   start of a multi-turn transit
      ``D<id>-><zone>``       arrival after a multi-turn transit
    """
    if not move or move[0] != "D":
        return None

    idx = 1
    while idx < len(move) and move[idx].isdigit():
        idx += 1
    if idx == 1:
        return None

    drone_id = int(move[1:idx])
    rest = move[idx:]

    if rest.startswith("->"):
        return drone_id, "arrival", rest[2:], None
    if rest.startswith("-"):
        parts = rest[1:].split("-")
        if len(parts) == 1:
            return drone_id, "single", parts[0], None
        return drone_id, "transit_start", parts[-1], parts[0]
    return None


def _build_drone_timeline(graph, drones, turns):
    """Rebuild, frame by frame, the exact position of every drone.

    Returns a list (index 0 = before the first turn) of dicts mapping
    ``drone_id`` to a state tuple:
      ``("at", hub_name)``                  drone sitting at a hub
      ``("transit", from_hub, to_hub, t)``  ``t`` (0..1) through a
                                             multi-turn move

    This only replays the moves already produced by ``Simulation.run()``;
    it makes no scheduling decision of its own.
    """
    state = {drone.drone_id: ("at", graph.start) for drone in drones}
    timeline = [state]
    pending = {}

    for frame_index, turn_moves in enumerate(turns, start=1):
        current = dict(timeline[frame_index - 1])
        arrived = set()

        for move in turn_moves:
            parsed = _parse_drone_move(move)
            if parsed is None:
                continue
            drone_id, kind, target, source = parsed

            if kind == "single":
                current[drone_id] = ("at", target)
                pending.pop(drone_id, None)
            elif kind == "transit_start":
                cost = graph.get_cost(target) or 1
                pending[drone_id] = {
                    "from": source,
                    "to": target,
                    "start_frame": frame_index - 1,
                    "cost": max(cost, 1),
                }
                current[drone_id] = ("at", source)
            elif kind == "arrival":
                current[drone_id] = ("at", target)
                pending.pop(drone_id, None)
                arrived.add(drone_id)

        for drone_id, info in pending.items():
            if drone_id in arrived:
                continue
            t = (frame_index - info["start_frame"]) / info["cost"]
            current[drone_id] = ("transit", info["from"], info["to"],
                                 _clamp(t, 0.0, 1.0))

        timeline.append(current)

    return timeline


def _state_position(state, hub_coords):
    if state[0] == "at":
        return hub_coords[state[1]]
    _, from_hub, to_hub, t = state
    fx, fy = hub_coords[from_hub]
    tx, ty = hub_coords[to_hub]
    return _lerp(fx, tx, t), _lerp(fy, ty, t)


def _drone_color(index):
    import pygame
    color = pygame.Color(0)
    color.hsva = ((index * 47) % 360, 65, 100, 100)
    return color.r, color.g, color.b


def _hexagon_points(cx, cy, r):
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 90)
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


def _draw_rounded_panel(pg, surface, rect, fill, border, radius=14,
                        border_width=2):
    pg.draw.rect(surface, fill, rect, border_radius=radius)
    pg.draw.rect(surface, border, rect, width=border_width,
                 border_radius=radius)


def _text(pg, font, value, color):
    return font.render(value, True, color)


def _zone_color(graph, hub_name):
    zone = graph.get_zone(hub_name)
    return ZONE_COLORS.get(zone, ZONE_COLORS["normal"])


def _visualize_pygame(graph, drones, turns, delay):
    """Render the already-computed simulation with a polished pygame UI.

    Reads ``graph``/``drones``/``turns`` only. No algorithm, scheduling or
    simulation state is modified anywhere in this function.
    """
    import pygame
    import pygame.gfxdraw

    pygame.init()
    pygame.display.set_caption("Fly-in - Drone Routing Visualization")
    screen = pygame.display.set_mode((1600, 900), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("arial,segoeui,helvetica", 24,
                                     bold=True)
    font_label = pygame.font.SysFont("arial,segoeui,helvetica", 16)
    font_small = pygame.font.SysFont("arial,segoeui,helvetica", 13)
    font_drone = pygame.font.SysFont("arial,segoeui,helvetica", 12,
                                     bold=True)

    hub_coords = _build_hub_coords(graph)
    edges = _build_edges(graph)
    timeline = _build_drone_timeline(graph, drones, turns)
    total_frames = len(timeline) - 1
    total_drones = len(drones)
    drone_colors = {d.drone_id: _drone_color(i) for i, d in
                    enumerate(drones)}

    xs = [c[0] for c in hub_coords.values()]
    ys = [c[1] for c in hub_coords.values()]
    bounds = (min(xs), min(ys), max(xs), max(ys))
    camera = _Camera(bounds, (1600 - PANEL_WIDTH, 900))

    state = "idle"  # idle -> playing -> finished ; space toggles paused
    paused = False
    playhead = 0.0
    dragging = False
    last_mouse = (0, 0)

    def capacity_label(name):
        capacity = graph.get_capacity(name)
        return "inf" if capacity == float("inf") else str(int(capacity))

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        viewport_w = screen.get_width() - PANEL_WIDTH

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                new_w = max(event.w, 900)
                new_h = max(event.h, 500)
                screen = pygame.display.set_mode((new_w, new_h),
                                                 pygame.RESIZABLE)
                camera.set_viewport((new_w - PANEL_WIDTH, new_h))
                viewport_w = new_w - PANEL_WIDTH
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_s and state == "idle":
                    state = "playing"
                elif event.key == pygame.K_SPACE and state != "idle":
                    paused = not paused
                elif event.key == pygame.K_r:
                    playhead = 0.0
                    state = "playing"
                    paused = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and event.pos[0] < viewport_w:
                    dragging = True
                    last_mouse = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    dx = event.pos[0] - last_mouse[0]
                    dy = event.pos[1] - last_mouse[1]
                    camera.pan(dx, dy)
                    last_mouse = event.pos
            elif event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                if mouse_pos[0] < viewport_w:
                    factor = 1.1 if event.y > 0 else 1 / 1.1
                    camera.zoom_at(mouse_pos, factor)

        if state == "playing" and total_frames > 0:
            if not paused:
                playhead = min(playhead + dt / max(delay, 0.05),
                               total_frames)
                if playhead >= total_frames:
                    state = "finished"
        elif state == "playing" and total_frames == 0:
            state = "finished"

        frame_lo = int(playhead)
        frame_hi = min(frame_lo + 1, total_frames)
        local_t = _ease(playhead - frame_lo)

        screen.fill(BG_COLOR)

        for hub_a, hub_b, capacity in edges:
            ax, ay = camera.world_to_screen(*hub_coords[hub_a])
            bx, by = camera.world_to_screen(*hub_coords[hub_b])
            pygame.draw.aaline(screen, EDGE_COLOR, (ax, ay), (bx, by))
            if capacity and capacity > 1:
                mx, my = (ax + bx) / 2, (ay + by) / 2
                badge = _text(pygame, font_small, f"x{capacity}",
                              EDGE_LABEL_COLOR)
                screen.blit(badge, (mx - badge.get_width() / 2,
                                    my - badge.get_height() / 2))

        hex_radius = _clamp(26 * camera.zoom, 14, 46)
        for name, (wx, wy) in hub_coords.items():
            sx, sy = camera.world_to_screen(wx, wy)
            is_start = name == graph.start
            is_end = name == graph.end
            if is_start:
                color, width = START_COLOR, 3
            elif is_end:
                color, width = END_COLOR, 3
            else:
                color, width = _zone_color(graph, name), 2

            points = _hexagon_points(sx, sy, hex_radius)
            pygame.draw.polygon(screen, BG_COLOR, points)
            pygame.draw.aalines(screen, color, True, points)
            pygame.draw.polygon(screen, color, points, width)

            label_text = name.upper() if (is_start or is_end) else name
            label = _text(pygame, font_label, label_text, TEXT_COLOR)
            screen.blit(label, (sx - label.get_width() / 2,
                                sy - hex_radius - 20))

            if not (is_start or is_end):
                cap = capacity_label(name)
                if cap != "1":
                    cap_label = _text(pygame, font_small, f"cap {cap}",
                                      TEXT_MUTED)
                    screen.blit(cap_label,
                                (sx - cap_label.get_width() / 2,
                                 sy + hex_radius + 4))

        active_count = 0
        finished_count = 0
        cluster_slots = {}
        for drone in drones:
            drone_id = drone.drone_id
            state_lo = timeline[frame_lo].get(drone_id,
                                              ("at", graph.start))
            state_hi = timeline[frame_hi].get(drone_id, state_lo)
            px_lo, py_lo = _state_position(state_lo, hub_coords)
            px_hi, py_hi = _state_position(state_hi, hub_coords)
            wx = _lerp(px_lo, px_hi, local_t)
            wy = _lerp(py_lo, py_hi, local_t)

            settled_state = state_hi if local_t > 0.999 else state_lo
            is_finished = (settled_state[0] == "at"
                           and settled_state[1] == graph.end)
            if is_finished:
                finished_count += 1
            else:
                active_count += 1

            cluster_key = (round(wx, 2), round(wy, 2))
            slot = cluster_slots.get(cluster_key, 0)
            cluster_slots[cluster_key] = slot + 1
            jitter_radius = 9 if slot else 0
            jitter_angle = slot * 2.4

            sx, sy = camera.world_to_screen(wx, wy)
            sx += math.cos(jitter_angle) * jitter_radius
            sy += math.sin(jitter_angle) * jitter_radius

            color = drone_colors[drone_id]
            radius = int(_clamp(7 * camera.zoom, 5, 12))
            pygame.gfxdraw.filled_circle(screen, int(sx), int(sy),
                                         radius, color)
            pygame.gfxdraw.aacircle(screen, int(sx), int(sy), radius,
                                    (10, 10, 10))
            id_label = _text(pygame, font_drone, f"D{drone_id}",
                             TEXT_COLOR)
            screen.blit(id_label, (sx + radius + 2, sy - radius - 4))

        panel_rect = pygame.Rect(screen.get_width() - PANEL_WIDTH + 16,
                                 16, PANEL_WIDTH - 32,
                                 screen.get_height() - 32)
        _draw_rounded_panel(pygame, screen, panel_rect, PANEL_BG,
                            PANEL_BORDER)

        pad = 20
        x0 = panel_rect.x + pad
        y = panel_rect.y + pad

        title_by_state = {
            "idle": "READY",
            "playing": "PAUSED" if paused else "RUNNING",
            "finished": "COMPLETE",
        }
        color_by_state = {
            "idle": TEXT_MUTED,
            "playing": START_COLOR,
            "finished": END_COLOR,
        }
        screen.blit(_text(pygame, font_title, title_by_state[state],
                          color_by_state[state]), (x0, y))
        y += 40
        pygame.draw.line(screen, PANEL_BORDER, (panel_rect.x, y),
                         (panel_rect.right, y), 1)
        y += 20

        current_turn = min(frame_lo + 1, total_frames) if total_frames \
            else 0
        stats = [
            ("Turn", f"{current_turn} / {total_frames}"),
            ("Total drones", str(total_drones)),
            ("Active", str(active_count)),
            ("Finished", str(finished_count)),
        ]
        for label_text, value_text in stats:
            screen.blit(_text(pygame, font_label, label_text, TEXT_MUTED),
                        (x0, y))
            value = _text(pygame, font_label, value_text, TEXT_COLOR)
            screen.blit(value, (panel_rect.right - pad - value.get_width(),
                                y))
            y += 25

        y += 10
        pygame.draw.line(screen, PANEL_BORDER, (panel_rect.x, y),
                         (panel_rect.right, y), 1)
        y += 18

        screen.blit(_text(pygame, font_label, "Legend", TEXT_COLOR),
                    (x0, y))
        y += 26
        legend_items = [
            ("Start", START_COLOR),
            ("End", END_COLOR),
            ("Normal", ZONE_COLORS["normal"]),
            ("Priority", ZONE_COLORS["priority"]),
            ("Restricted", ZONE_COLORS["restricted"]),
            ("Blocked", ZONE_COLORS["blocked"]),
        ]
        for label_text, color in legend_items:
            pygame.draw.circle(screen, color, (x0 + 6, y + 7), 6, 2)
            screen.blit(_text(pygame, font_small, label_text, TEXT_MUTED),
                        (x0 + 20, y))
            y += 20

        y += 8
        pygame.draw.line(screen, PANEL_BORDER, (panel_rect.x, y),
                         (panel_rect.right, y), 1)
        y += 18
        screen.blit(_text(pygame, font_label, "Controls", TEXT_COLOR),
                    (x0, y))
        y += 26
        controls = [
            ("start", "S"),
            ("pause", "space"),
            ("restart", "R"),
            ("quit", "Q / Esc"),
            ("zoom", "scroll"),
            ("pan", "drag"),
        ]
        for action, key in controls:
            screen.blit(_text(pygame, font_small, action, TEXT_MUTED),
                        (x0, y))
            key_label = _text(pygame, font_small, key, TEXT_COLOR)
            screen.blit(key_label,
                        (panel_rect.right - pad - key_label.get_width(),
                         y))
            y += 20

        if state == "idle":
            hint = _text(pygame, font_label, "Press S to start",
                         END_COLOR)
            screen.blit(hint, (x0, panel_rect.bottom - pad - 24))

        pygame.display.flip()

    pygame.quit()
