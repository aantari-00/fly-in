from pyparsing import Word, alphas, alphanums, nums, Optional, Suppress, Group, OneOrMore, ParseException, one_of, pythonStyleComment
import pyparsing as parser
import pyparsing

# ser_parse_action()

NB_DRONES = Suppress("nb_drones") - Suppress(":") - Word(nums)("nb_drones")

ZONE = Suppress("zone") - Suppress("=") - one_of(["restricted", "normal", "blocked", "priority"])("zone")
COLOR = Suppress("color") - Suppress("=") - Word(alphas)("color")
MAX_DRONES = Suppress("max_drones") - Suppress("=") - Word(nums)("max_drones")

GLOBAL_META_DATA = Suppress("[") - (Optional(ZONE) & Optional(COLOR) & Optional(MAX_DRONES)) - Suppress("]")

SPECIAL_META_DATA = Suppress("[") - Suppress("color") - Suppress("=") - Word(alphas)("color") - Suppress("]")

GLOBAL_HUB = Word(alphanums)("hub_name") - Word(nums)("x") - Word(nums)("y") 


SPECIAL_HUB = Suppress(":") - GLOBAL_HUB - Optional(SPECIAL_META_DATA)

HUB = Group(Suppress("hub") - Suppress(":") - GLOBAL_HUB - Optional(GLOBAL_META_DATA))
END_HUB = Group(Suppress("end_hub") - SPECIAL_HUB)("end_hub")
START_HUB = Group(Suppress("start_hub") - SPECIAL_HUB)("start_hub")  
CONNECTION_META_DATA = Suppress("[") - Suppress("max_link_capacity") - Suppress("=") - Word(nums)("max_link_capacity") - Suppress("]")
CONNECTION = Group(Suppress("connection") - Suppress(":") - Word(alphanums)("first_link") - Suppress("-") - Word(alphanums)("second_link") - Optional(CONNECTION_META_DATA))

rules = NB_DRONES - (
    END_HUB &
    START_HUB &
    Group(OneOrMore(HUB))("liste_hubs") &
    Group(OneOrMore(CONNECTION))("liste_connections")
)
rules.ignore(pythonStyleComment)

try:
    resultat = rules.parse_file("config", parse_all=True)
    for cle, valeur in resultat.asDict().items():
        print(f"{cle}: {valeur}")

except (ParseException, pyparsing.exceptions.ParseBaseException) as e:
    print(e.explain())