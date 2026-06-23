from pyparsing import (
    Word, alphas, Optional,
    Suppress, Group, OneOrMore, ParseException, pyparsing_common,
    one_of, pythonStyleComment
)
import pyparsing


class Connection:
    def __init__(self, hub1, hub2, max_connections=1) -> None:
        self.hub1 = hub1
        self.hub2 = hub2
        self.max_connections = max_connections

    def __eq__(self, value):
        return (
            (self.hub1 == value.hub2 and self.hub2 == value.hub1)
            or
            (self.hub1 == value.hub1 and self.hub2 == value.hub2)
        )

    def __hash__(self):
        return hash(frozenset([self.hub1, self.hub2]))


class Hub:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y

    def __eq__(self, value):
        return self.name == value.name

    def __hash__(self):
        return hash((self.name))


connections = set()
hubs = set()


def save_hub(text, loc, tokens):
    hub_info = tokens[0]

    name = hub_info["name"]
    x = int(hub_info["x"])
    y = int(hub_info["y"])

    hub = Hub(name, x, y)

    if hub in hubs:
        raise pyparsing.ParseFatalException(text, loc,
                                            f"Error: repeated hub '{name}'"
                                            f" ({x}, {y})!")

    hubs.add(hub)


def save_connection(text, loc, tokens):
    connection_info = tokens[0]

    hub1 = connection_info["from_zone"]
    hub2 = connection_info["to_zone"]

    hubs_name = [hub.name for hub in hubs]

    connection = Connection(hub1, hub2)
    if hub1 == hub2:
        raise pyparsing.ParseFatalException(text, loc, tokens)

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
POS_INT = pyparsing_common.integer
SIGNED_INT = pyparsing_common.signed_integer

# NB_DRONES
NB_DRONES = (Suppress("nb_drones") + Suppress(":") + POS_INT("count"))
NB_DRONES.add_condition(
    lambda tokens: int(tokens.get("count")) > 0,
    message="Logical Error: The number of drones must be greater than 0!",
    fatal=True
)

# HUB BASIC
HUB_BASIC = (NAME("name") + SIGNED_INT("x") + SIGNED_INT("y"))

# METADATA
ZONE = (Suppress("zone") + Suppress("=") +
        one_of("restricted normal blocked priority")("zone"))
COLOR = (Suppress("color") + Suppress("=") + Word(alphas)("color"))
MAX_DRONES = (Suppress("max_drones") +
              Suppress("=") + POS_INT("max_drones"))
MAX_DRONES.add_condition(
    lambda tokens: int(tokens.get("max_drones")) > 0,
    message="Logical Error: The number of max_drones "
    "must be greater than 0!",
    fatal=True
)
METADATA = (Suppress("[") + (Optional(ZONE) & Optional(COLOR) &
                             Optional(MAX_DRONES)) + Suppress("]"))

# HUB
HUB = Group(Suppress("hub") + Suppress(":")
            + HUB_BASIC + Optional(METADATA))("hub").set_results_name(
                "Hubs", list_all_matches=True)
HUB.set_parse_action(save_hub)

# START_HUB
START_HUB = Group(Suppress("start_hub") + Suppress(":")
                  + HUB_BASIC + Optional(METADATA)).set_results_name(
                      "start_hub", list_all_matches=True)
START_HUB.set_parse_action(save_hub)

#  END_HUB
END_HUB = Group(Suppress("end_hub") + Suppress(":") + HUB_BASIC
                + Optional(METADATA)).set_results_name(
                    "end_hub", list_all_matches=True)
END_HUB.set_parse_action(save_hub)

# CONNECTION METADATA
MAX_LINK_CAPACITY = (Suppress("max_link_capacity") + Suppress("=")
                     + POS_INT("max_link_capacity"))
MAX_LINK_CAPACITY.add_condition(
    lambda tokens: int(tokens.get("max_link_capacity")) > 0,
    message="Logical Error: The number of max_link_capacity"
    "must be greater than 0!",
    fatal=True
)
CONNECTION_METADATA = (Suppress("[") + MAX_LINK_CAPACITY + Suppress("]"))

# CONNECTION
CONNECTION = Group(Suppress("connection")
                   + Suppress(":") + NAME("from_zone")
                   + Suppress("-") + NAME("to_zone")
                   + Optional(CONNECTION_METADATA)).set_results_name(
                       "Connections", list_all_matches=True)
CONNECTION.set_parse_action(save_connection)
STATEMENTS = (END_HUB | START_HUB | HUB | CONNECTION)

# GLOBAL RULES
rules = (NB_DRONES - OneOrMore(STATEMENTS))
rules.ignore(pythonStyleComment)


def parse_map(filename: str):
    try:
        result = rules.parse_file("map.txt", parse_all=True)
        res = result.as_dict()
        if len(res.get("start_hub", [])) != 1:
            raise pyparsing.ParseFatalException(
                "logical Error: expected one start_hub !")
        if len(res.get("end_hub", [])) != 1:
            raise pyparsing.ParseFatalException(
                "logical Error: expected one end_hub !")
        print("parsing ok")
    except (ParseException, pyparsing.exceptions.ParseBaseException) as e:
        print(e.explain())
