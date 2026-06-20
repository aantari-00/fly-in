from pyparsing import (Suppress, one_of, alphanums, Optional, ParseException,
                       Word, printables, nums, ZeroOrMore)

# tokens
NAME = Word(printables, exclude_chars=" -")
INTEGER = Word(nums)

# nb drones
NB_DRONES = (Suppress("nb_drones") + Suppress(":") + INTEGER("count"))

# HUB BASIC
HUB_BASIC = (NAME("name") + INTEGER("x") + INTEGER("y"))
# ZONE METADATA
ZONE = (Suppress("zone") + Suppress("=") +
        one_of("restricted normal blocked priority")("zone"))
# COLOR METADATA
COLOR = (Suppress("color") + Suppress("=") + Word(alphanums)("color"))
# MAX_DRONES
MAX_DRONES = (Suppress("max_drones") + Suppress("=") + INTEGER("max_drones"))

# ALL META_DATA
METADATA = (Suppress("[") + ZeroOrMore(ZONE | COLOR | MAX_DRONES)
            + Suppress("]"))

# HUB COMPLETE
HUB = (Suppress("hub") + Suppress(":") + HUB_BASIC + Optional(METADATA))

# START_HUB
START_HUB = (Suppress("start_hub") + Suppress(":") + HUB_BASIC
             + Optional(METADATA))

# END_HUB
END_HUB = (Suppress("end_hub") + Suppress(":") + HUB_BASIC
           + Optional(METADATA))

# CONNECTION METADATA
MAX_LINK_CAPACITY = (Suppress("max_link_capacity") + Suppress("=")
                     + INTEGER("max_link_capacity"))

CONNECTION_METADATA = (Suppress("[") + MAX_LINK_CAPACITY + Suppress("]"))

# CONNECTION COMPLETE
CONNECTION = (Suppress("connection") + Suppress(":") + NAME("from_zone") +
              Suppress("-") + NAME("to_zone") + Optional(CONNECTION_METADATA))

# STORAGE
hubs = []
connections = []
start_hub = None
end_hub = None
nb_drones = None
# PARSING
with open("map.txt") as f:
    for line in f:

        line = line.split("#")[0].strip()
        if not line:
            continue

        try:
            if line.startswith("nb_drones"):
                nb_drones = NB_DRONES.parse_string(line)["count"]

            elif line.startswith("start_hub"):
                start_hub = START_HUB.parse_string(line)

            elif line.startswith("end_hub"):
                end_hub = END_HUB.parse_string(line)

            elif line.startswith("hub"):
                hubs.append(HUB.parse_string(line))

            elif line.startswith("connection"):
                connections.append(CONNECTION.parse_string(line))

            else:
                raise ValueError("Unknown line")

        except ParseException as e:
            print("ERROR in line:", line)
            print(e)
            exit(1)


try:
    if start_hub is None:
        raise ValueError("Missing required field: start_hub")

    if end_hub is None:
        raise ValueError("Missing required field: end_hub")

    if nb_drones is None:
        raise ValueError("Missing required field: nb_drones")
except Exception as e:
    print(e)
    






























