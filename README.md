# Fly-in

## Project description

Fly-in is a Python-based simulation project for planning and visualizing drone movement across a custom map. The project reads a map description, builds a graph of hubs and connections, generates candidate routes, assigns drones to those routes, simulates movement with occupancy constraints, and renders the result with Pygame.

The repository is structured around a small pipeline:

1. Parse a map file into structured data.
2. Build a graph of hubs and connections.
3. Generate feasible routes.
4. Assign drones to the generated paths.
5. Simulate movement turn by turn.
6. Visualize the simulation.

The implementation is intentionally simple and educational rather than production-oriented.

## Features

The current implementation includes:

- Parsing of map files with the `pyparsing` library.
- Construction of a graph representation with hubs, connections, zones, and capacities.
- Shortest-path computation with a Dijkstra-based solver.
- Generation of multiple candidate routes using a repeated shortest-path strategy with blocked edges and nodes.
- Assignment of drones to routes using a straightforward load-balancing approach.
- Turn-based simulation of drone movement.
- Capacity enforcement for hubs and links.
- Support for zones such as `normal`, `restricted`, `priority`, and `blocked`.
- Pygame-based visualization with animation, zoom, pause/resume, restart, and quit controls.
- Sample map files and a small Makefile for convenience.

## Architecture overview

The project follows a modular pipeline:

- `fly/parser.py` reads and validates the input map.
- `fly/graph.py` stores the graph model and exposes graph operations.
- `fly/dijkstra.py` computes shortest paths.
- `fly/router.py` generates candidate routes and assigns drones.
- `fly/simulation.py` executes the turn-based movement logic.
- `fly/visualization.py` renders the process in a window.
- `fly/main.py` connects the modules and starts the workflow.

The main runtime flow is:

```text
parse map -> build graph -> generate routes -> assign drones -> simulate -> visualize
```

## Project structure

```text
fly-in/
├── README.md
├── Makefile
├── fly/
│   ├── main.py
│   ├── parser.py
│   ├── graph.py
│   ├── dijkstra.py
│   ├── router.py
│   ├── simulation.py
│   ├── visualization.py
│   ├── map.txt
│   ├── requirements.txt
│   ├── Makefile
│   └── maps/
│       ├── easy/
│       ├── medium/
│       ├── hard/
│       └── challenger/
└── all/
    ├── py.py
    └── vis.py
```

The `fly/` folder contains the main implementation. The `all/` directory contains additional prototype or exploratory scripts.

## Installation

The project is intended to run with Python 3 and the dependencies listed in `fly/requirements.txt`.

From the repository root:

```bash
cd fly
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The repository also provides a helper Makefile:

```bash
cd fly
make install
```

## Usage

Run the main simulation from the `fly/` directory:

```bash
cd fly
python3 main.py
```

You can also use the provided Makefile:

```bash
cd fly
make run
```

The current entry point uses `map.txt` by default.

## Input file format

The parser expects a text file describing the number of drones, hubs, zones, and connections.

A typical file uses the following structure:

```text
nb_drones: 6

start_hub: start 0 0 [color=green max_drones=6]
hub: loop_a 1 0 [color=orange max_drones=2]
...

connection: start-loop_a [max_link_capacity=2]
connection: loop_a-loop_b [max_link_capacity=2]
...
```

### Supported declarations

- `nb_drones: <number>`: number of drones to simulate.
- `start_hub: <name> <x> <y> [metadata]`: start node.
- `end_hub: <name> <x> <y> [metadata]`: target node.
- `hub: <name> <x> <y> [metadata]`: regular hub.
- `connection: <hub1>-<hub2> [metadata]`: undirected connection.

### Metadata supported by the parser

- `zone=restricted|normal|blocked|priority`
- `color=<value>`
- `max_drones=<positive integer>`
- `max_link_capacity=<positive integer>`

The parser validates the file structure and returns `None` if the input cannot be parsed correctly.

## Algorithms used

### Dijkstra shortest path

The project includes a Dijkstra-based shortest-path solver in `fly/dijkstra.py`. It evaluates path cost using the graph cost model and gives priority to zones marked as `priority` by adjusting the scoring logic.

### Route generation

The router does not use a full general-purpose k-shortest-path library. Instead, it repeatedly runs shortest-path searches and blocks previously used edges or nodes so that additional candidate routes can be generated. This is a lightweight, implementation-oriented strategy for producing multiple paths.

### Drone assignment

Drones are assigned to routes using a simple balancing strategy. The implementation evaluates the current path cost plus the current load and picks the path with the lowest resulting value.

### Simulation logic

The simulation engine advances drones turn by turn while respecting occupancy and link-capacity rules.

## Simulation rules

The simulation uses the following rules:

- Each drone follows an assigned path.
- A drone can move to the next hub in its route if the destination hub has available capacity.
- The simulation also checks the capacity of the specific link between the current and next hub.
- If a hub is `blocked`, the graph builder skips the corresponding connection.
- If a zone is `restricted`, the cost of moving through that zone is higher.
- If a zone is `priority`, the path scoring logic gives it special attention.
- Some moves can be represented as transit moves with multiple turns when the cost is greater than 1.
- The simulation stops once all drones have reached their final state.

If the simulation cannot make progress, the implementation raises a `RuntimeError` indicating that the map may be deadlocked.

## Visualization

The visualization layer uses Pygame.

### What it shows

- The map graph with hubs and connections.
- Drone markers moving across the network.
- A sidebar with turn information and status.

### Controls

- `Space`: pause or resume the animation.
- `S`: restart the animation from the beginning.
- `Q` or `Esc`: quit the visualization.
- `Mouse wheel`: zoom in or out.

The visualization is started by the main workflow after the simulation has been executed.

## Performance and complexity

This project is designed for small to medium maps and is not optimized for very large graphs.

In practice:

- Path generation repeats shortest-path searches and graph modifications.
- Simulation cost depends on the number of drones, the number of turns, and the size of the graph.
- The implementation favors clarity and correctness over high-performance routing.

No advanced optimization, caching, or parallel processing is implemented.

## Error handling

The project includes basic error handling:

- The parser reports invalid or inconsistent input and returns `None` on parse failure.
- The main entry point prints an error if the map cannot be parsed.
- The main entry point prints a message if no path is found.
- The simulation can raise a runtime error when the map appears deadlocked or the turn limit is exceeded.

## Technologies used

- Python 3
- `pyparsing` for parsing map files
- `pygame` for visualization
- `flake8` and `mypy` for linting and type checking support

## Resources

Useful project assets include:

- `fly/map.txt`: the default sample map used by the main entry point.
- `fly/maps/`: additional example maps organized by difficulty.
- `fly/requirements.txt`: dependencies for the project.
- `fly/Makefile`: convenience commands for installation and execution.

## AI usage

This project was developed with the assistance of AI tools during implementation and documentation. AI was used to help with code generation, debugging, and drafting this README. The runtime behavior and repository content are still grounded in the Python source files present in this repository.

## Authors

- Author: `aantari`

## License

No explicit license file is currently present in the repository. The code is shared as-is for educational and personal use unless otherwise stated by the repository owner.
