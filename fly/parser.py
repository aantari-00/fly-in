from pyparsing import (
    Word,
    alphas,
    Optional,
    Suppress,
    Group,
    Combine,
    OneOrMore,
    pyparsing_common,
    one_of,
    pythonStyleComment,
)
import pyparsing


class Connection:
    """Represent an undirected connection between two hubs."""

    def __init__(self, hub1: str, hub2: str, max_connections: int = 1) -> None:
        """Initialize the connection with its endpoints."""
        self.hub1 = hub1
        self.hub2 = hub2
        self.max_connections = max_connections

    def __eq__(self, value: object) -> bool:
        """Compare this connection with another connection."""
        return (self.hub1 == value.hub2 and self.hub2 == value.hub1) or (
            self.hub1 == value.hub1 and self.hub2 == value.hub2
        )

    def __hash__(self) -> int:
        """Provide a hash based on the connection endpoints."""
        return hash(frozenset([self.hub1, self.hub2]))


class Hub:
    """Represent a hub node in the map."""

    def __init__(self, name: str, x: int, y: int) -> None:
        """Initialize the hub with its identifier and coordinates."""
        self.name = name
        self.x = x
        self.y = y

    def __eq__(self, value: object) -> bool:
        """Compare hubs by their names."""
        return self.name == value.name

    def __hash__(self) -> int:
        """Provide a hash based on the hub name."""
        return hash((self.name))


connections = set()
hubs = set()


def save_hub(text: str, loc: int, tokens: object) -> None:
    """Store a parsed hub in the global hub set."""
    hub_info = tokens[0]

    name = hub_info["name"]
    x = int(hub_info["x"])
    y = int(hub_info["y"])

    hub = Hub(name, x, y)

    if hub in hubs:
        raise pyparsing.ParseFatalException(
            text, loc, f"Error: repeated hub '{name}'" f" ({x}, {y})!"
        )

    hubs.add(hub)


def save_connection(text: str, loc: int, tokens: object) -> None:
    """Store a parsed connection in the global connection set."""
    connection_info = tokens[0]

    hub1 = connection_info["from_zone"]
    hub2 = connection_info["to_zone"]

    hubs_name = [hub.name for hub in hubs]

    connection = Connection(hub1, hub2)
    if hub1 == hub2:
        raise pyparsing.ParseFatalException(
            text, loc, "Error: self" f"connection '{hub1}-{hub2}'!"
        )

    if connection in connections:
        raise pyparsing.ParseFatalException(
            text, loc, f"Error: repeated connection '{hub1}-{hub2}'!"
        )

    if hub1 not in hubs_name:
        raise pyparsing.ParseFatalException(
            text, loc, f"Error: hub '{hub1}' not declared!"
        )

    if hub2 not in hubs_name:
        raise pyparsing.ParseFatalException(
            text, loc, f"Error: hub '{hub2}' not declared!"
        )

    connections.add(connection)


# TOKENS
NAME = Word(pyparsing.printables, exclude_chars=" -")
POS_INT = pyparsing_common.integer
SIGNED_INT = pyparsing_common.signed_integer

# NB_DRONES
NB_DRONES = Suppress("nb_drones") + Suppress(":") + POS_INT("count")
NB_DRONES.add_condition(
    lambda tokens: int(tokens.get("count")) > 0,
    message="Logical Error: The number of drones must be greater than 0!",
    fatal=True,
)

# HUB BASIC
HUB_BASIC = NAME("name") + SIGNED_INT("x") + SIGNED_INT("y")

# METADATA
ZONE = Combine(
    Suppress("zone")
    + Suppress("=")
    + one_of("restricted normal blocked priority")
)("zone")
COLOR = Combine(Suppress("color") + Suppress("=") + Word(alphas))("color")
MAX_DRONES = Combine(Suppress("max_drones") + Suppress("=") + POS_INT)("max_drones")
MAX_DRONES.add_condition(
    lambda tokens: int(tokens.get("max_drones")) > 0,
    message="Logical Error: The number of max_drones " "must be greater than 0!",
    fatal=True,
)
METADATA = (
    Suppress("[")
    + (Optional(ZONE) & Optional(COLOR) & Optional(MAX_DRONES))
    + Suppress("]")
)

# HUB
HUB = Group(Suppress("hub") + Suppress(":") + HUB_BASIC + Optional(METADATA))(
    "hub"
).set_results_name("Hubs", list_all_matches=True)
HUB.set_parse_action(save_hub)

# START_HUB
START_HUB = Group(
    Suppress("start_hub") + Suppress(":") + HUB_BASIC + Optional(METADATA)
).set_results_name("start_hub", list_all_matches=True)
START_HUB.set_parse_action(save_hub)

#  END_HUB
END_HUB = Group(
    Suppress("end_hub") + Suppress(":") + HUB_BASIC + Optional(METADATA)
).set_results_name("end_hub", list_all_matches=True)
END_HUB.set_parse_action(save_hub)

# CONNECTION METADATA
MAX_LINK_CAPACITY = Combine(
    Suppress("max_link_capacity") + Suppress("=") + POS_INT
)("max_link_capacity")
MAX_LINK_CAPACITY.add_condition(
    lambda tokens: int(tokens.get("max_link_capacity")) > 0,
    message="Logical Error: The number of max_link_capacity" "must be greater than 0!",
    fatal=True,
)
CONNECTION_METADATA = Suppress("[") + MAX_LINK_CAPACITY + Suppress("]")

# CONNECTION
CONNECTION = Group(
    Suppress("connection")
    + Suppress(":")
    + NAME("from_zone")
    + Suppress("-")
    + NAME("to_zone")
    + Optional(CONNECTION_METADATA)
).set_results_name("Connections", list_all_matches=True)
CONNECTION.set_parse_action(save_connection)
STATEMENTS = END_HUB | START_HUB | HUB | CONNECTION

# GLOBAL RULES
rules = NB_DRONES - OneOrMore(STATEMENTS)
rules.ignore(pythonStyleComment)


_CUSTOM_ERROR_PREFIXES = ("Error:", "Logical Error:", "logical Error:")


def _is_custom_error(e: pyparsing.ParseBaseException) -> bool:
    """Check whether a parse exception carries one of our own validation
    messages, as opposed to a pyparsing-generated grammar message.

    We can't rely on the exception *type* for this: the '-' error-stop
    operator in `rules` re-wraps ANY exception raised past that point
    (including our own ParseFatalException from save_hub/save_connection/
    add_condition) into a ParseSyntaxException, while keeping the original
    .msg intact. So we classify by message content instead.
    """
    return e.msg.startswith(_CUSTOM_ERROR_PREFIXES)


def _format_syntax_error(e: pyparsing.ParseBaseException) -> str:
    """Build a short, readable message for a syntax/grammar error."""
    near = e.line.strip() if e.line else ""
    detail = f": '{near}'" if near else ""
    return (
        f"Syntax error (line {e.lineno}, col {e.column}): "
        f"unexpected or malformed input{detail}"
    )


def parse_map(filename: str) -> object:
    """Parse a map file and return the parsed data dictionary."""
    try:
        hubs.clear()
        connections.clear()
        result = rules.parse_file(filename, parse_all=True)
        res = result.as_dict()
        if len(res.get("start_hub", [])) != 1:
            raise pyparsing.ParseFatalException(
                "logical Error: expected one start_hub !"
            )
        if len(res.get("end_hub", [])) != 1:
            raise pyparsing.ParseFatalException("logical Error: "
                                                "expected one end_hub !")
        return res
    except pyparsing.ParseBaseException as e:
        if _is_custom_error(e):
            # Our own logical errors: keep the exact message, only add a
            # line number when it refers to a real position in the file
            # (the start_hub/end_hub count checks raise with no real loc).
            has_location = not e.msg.startswith("logical Error")
            location = f" (line {e.lineno})" if has_location else ""
            print(f"{e.msg}{location}")
        else:
            print(_format_syntax_error(e))
        return None