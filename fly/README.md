*This project has been created as part of the 42 curriculum by aantari.*

# Fly-In

## Description

Fly-In is a drone traffic simulation project.

The goal of the project is to route multiple drones from a starting hub to a destination while respecting the constraints of the network, including hub capacities, connection limits, and restricted zones.

The program parses a map description, computes routes for each drone, simulates their movements turn by turn, and provides a graphical visualization of the simulation.

## Features

- Load the drone network map from a configuration file.
- Parse and validate the map to ensure a clean and consistent input.
- Build a graph representation of the network.
- Compute the shortest paths using Dijkstra's algorithm based on traversal cost.
- Find multiple optimal paths with the same minimum cost.
- Simulate drone movements turn by turn while respecting network constraints.
- Visualize the simulation, including drone movements and network state.

## Architecture overview

The project follows a modular pipeline:

- `parser.py` reads and validates the input map.
- `graph.py` stores the graph model and exposes graph operations.
- `dijkstra.py` computes shortest paths.
- `router.py` generates candidate routes and assigns drones.
- `simulation.py` executes the turn-based movement logic.
- `visualization.py` renders the process in a window.
- `main.py` connects the modules and starts the workflow.

The main runtime flow is:

```text
parse map -> build graph -> generate routes -> assign drones -> simulate -> visualize.
```

## Project structure
```text
fly-in/
├── README.md
├── Makefile
├── main.py
├── parser.py
├── graph.py
├── dijkstra.py
├── router.py
├── simulation.py
├── visualization.py
├── map.txt
├── requirements.txt
├── Makefile
├── maps/
│  ├── easy/
│  ├── medium/
│  ├── hard/
│  └── challenger/
```

## Installation

The project is intended to run with Python 3 and the dependencies listed in `requirements.txt`.

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
You can also use the provided Makefile:

```bash
make run
or
make run MAP=../all/maps/easy/01_linear_path.txt
```
he current entry point uses `map.txt` by default.

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

The project includes a Dijkstra-based shortest-path solver in `dijkstra.py`. It evaluates path cost using the graph cost model and gives priority to zones marked as `priority` by adjusting the scoring logic.

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

## Error handling

The project includes basic error handling:

- The parser reports invalid or inconsistent input and returns `None` on parse failure.
- The main entry point prints an error if the map cannot be parsed.
- The main entry point prints a message if no path is found.
- The simulation can raise a runtime error when the map appears deadlocked or the turn limit is exceeded.

## Technologies used

- Python 3
- `pygame` for visualization
- `flake8` and `mypy` for linting and type checking support

## Learning Resources

This project is based on several algorithms and technologies. The following resources were used to understand and implement the project.

### Graph Theory

- William Fiset – Graph Theory
  https://www.youtube.com/playlist?list=PLDV1Zeh2NRsD06x59fxczdWLhDDszUHKt

### Dijkstra's Algorithm

- VisuAlgo – Single Source Shortest Path
  https://visualgo.net/en/sssp

- CP-Algorithms – Dijkstra
  https://cp-algorithms.com/graph/dijkstra.html

- Abdul Bari – Dijkstra Algorithm
  https://www.youtube.com/watch?v=XB4MIexjvY0

### Yen's Algorithm

- Wikipedia – Yen's Algorithm
  https://en.wikipedia.org/wiki/Yen%27s_algorithm

- Neo4j – Yen's Shortest Paths
  https://neo4j.com/docs/graph-data-science/current/algorithms/yens/

- NetworkX – shortest_simple_paths
  https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.simple_paths.shortest_simple_paths.html

### Pygame

- Official Documentation
  https://www.pygame.org/docs/

- Clear Code – Pygame Tutorial
  https://www.youtube.com/watch?v=AY9MnQ4x3zk

- Tech With Tim – Pygame Playlist
  https://www.youtube.com/playlist?list=PLzMcBGfZo4-lp3jAExUCewBfMx3UZFkh5


## AI usage