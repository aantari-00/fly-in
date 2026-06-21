from pyparsing import (
    Word, alphas, nums, Optional,
    Suppress, Group, OneOrMore, ParseException,
    one_of, pythonStyleComment
)
import pyparsing


class Connection:
    def __init__(self, hub1, hub2, max_connections=1) -> None:
        self.hub1 = hub1
        self.hub2 = hub2
        self.max_connections = max_connections

    def __eq__(self, value):
        if not isinstance(value, Connection):
            return NotImplemented
        return (
            (self.hub1 == value.hub2 and self.hub2 == value.hub1)
            or
            (self.hub1 == value.hub1 and self.hub2 == value.hub2)
        )

    def __hash__(self):
        return hash(frozenset([self.hub1, self.hub2]))

    def __str__(self):
        return f"{self.hub1}-{self.hub2}"


class Hub:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y

    def __eq__(self, value):
        return (
            self.name == value.name
            or
            (self.x == value.x and self.y == value.y)
        )

    def __hash__(self):
        return hash((self.name, self.x, self.y))


connections = set()
hubs = set()


def save_hub(text, loc, tokens):
    hub_info = tokens[0]

    name = hub_info["name"]
    x = int(hub_info["x"])
    y = int(hub_info["y"])

    hub = Hub(name, x, y)

    if hub in hubs:
        raise pyparsing.ParseFatalException(
            text,
            loc,
            f"Error: repeated hub '{name}' ({x}, {y})!"
        )

    hubs.add(hub)


def save_connection(text, loc, tokens):
    connection_info = tokens[0]

    hub1 = connection_info["from_zone"]
    hub2 = connection_info["to_zone"]

    hubs_name = [hub.name for hub in hubs]

    connection = Connection(hub1, hub2)

    if connection in connections:
        raise pyparsing.ParseFatalException(
            text,
            loc,
            f"Error: repeated connection '{hub1}-{hub2}'!"
        )

    if hub1 not in hubs_name:
        raise pyparsing.ParseFatalException(
            text,
            loc,
            f"Error: hub '{hub1}' not declared!"
        )

    if hub2 not in hubs_name:
        raise pyparsing.ParseFatalException(
            text,
            loc,
            f"Error: hub '{hub2}' not declared!"
        )

    connections.add(connection)


# TOKENS
NAME = Word(pyparsing.printables, exclude_chars=" -")
INTEGER = Word(nums)

# NB_DRONES
NB_DRONES = (Suppress("nb_drones") + Suppress(":") + INTEGER("count"))

# HUB BASIC
HUB_BASIC = (NAME("name") + INTEGER("x") + INTEGER("y"))

# METADATA
ZONE = (Suppress("zone") + Suppress("=") +
        one_of("restricted normal blocked priority")("zone"))

COLOR = (Suppress("color") + Suppress("=") + Word(alphas)("color"))

MAX_DRONES = (Suppress("max_drones") + Suppress("=") + INTEGER("max_drones"))

METADATA = (Suppress("[") + (Optional(ZONE) & Optional(COLOR) &
                             Optional(MAX_DRONES)) + Suppress("]"))

# HUB
HUB = Group(Suppress("hub") + Suppress(":") + HUB_BASIC + Optional(METADATA))
HUB.set_parse_action(save_hub)

# START_HUB
START_HUB = Group(Suppress("start_hub") + Suppress(":")
                  + HUB_BASIC + Optional(METADATA))("start_hub")
START_HUB.set_parse_action(save_hub)

# END_HUB
END_HUB = Group(Suppress("end_hub") + Suppress(":") + HUB_BASIC
                + Optional(METADATA))("end_hub")
END_HUB.set_parse_action(save_hub)

# CONNECTION METADATA
MAX_LINK_CAPACITY = (Suppress("max_link_capacity") + Suppress("=")
                     + INTEGER("max_link_capacity"))

CONNECTION_METADATA = (Suppress("[") + MAX_LINK_CAPACITY + Suppress("]"))

# CONNECTION
CONNECTION = Group(Suppress("connection") + Suppress(":") + NAME("from_zone")
                   + Suppress("-") + NAME("to_zone")
                   + Optional(CONNECTION_METADATA))
CONNECTION.set_parse_action(save_connection)

# GLOBAL RULES
rules = (NB_DRONES - (END_HUB & START_HUB &
                      Group(OneOrMore(HUB))("liste_hubs") &
                      Group(OneOrMore(CONNECTION))("liste_connections")))

rules.ignore(pythonStyleComment)

try:
    import sys

    result = rules.parse_file(sys.argv[1], parse_all=True)

    for key, value in result.asDict().items():
        print(f"{key}: {value}")

    print(*connections)

except (ParseException, pyparsing.exceptions.ParseBaseException) as e:
    print(e.explain())
