from collections.abc import Iterator
import re


class MapError(Exception):
    """Base class for every error raised while reading a map file."""

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        """Store the location and build the final error message."""
        self.line = line
        self.column = column
        location = ""
        if line is not None and column is not None:
            location = f" (line {line}, column {column})"
        elif line is not None:
            location = f" (line {line})"
        super().__init__(f"{message}{location}")


class MapSyntaxError(MapError):
    """A statement does not match the grammar of any known rule."""


class MapValidationError(MapError):
    """A statement is syntactically valid but breaks a business rule."""


class MapStructureError(MapError):
    """Missing or duplicated mandatory section
    (nb_drones/start_hub/end_hub)."""


ZONE_TYPES: tuple[str, ...] = ("normal", "priority", "restricted", "blocked")
HUB_METADATA_KEYS = {"zone", "color", "max_drones"}
CONNECTION_METADATA_KEYS = {"max_link_capacity"}

_KEYWORD_RE = re.compile(r"^(?P<keyword>[A-Za-z_]+)\s*:")
_NB_DRONES_RE = re.compile(r"^nb_drones\s*:\s*(?P<value>\S+)\s*$")
_HUB_RE = re.compile(
    r"^(?P<kind>start_hub|end_hub|hub)\s*:\s*"
    r"(?P<name>\S+)\s+(?P<x>\S+)\s+(?P<y>\S+)"
    r"(?:\s+\[(?P<metadata>.*)\])?\s*$"
)
_CONNECTION_RE = re.compile(
    r"^connection\s*:\s*(?P<hub1>[^\s-]+)-(?P<hub2>[^\s\-]+)"
    r"(?:\s+\[(?P<metadata>.*)\])?\s*$"
)
_INT_RE = re.compile(r"^[+-]?\d+$")


class MapReader:
    """Turn a map file into a stream of ready-to-parse statements."""

    def __init__(self, filename: str) -> None:
        """Store the path of the file to read."""
        self.filename = filename

    def statements(self) -> Iterator[tuple[int, str]]:
        """Yield (line_number, text) for every non-comment, non-blank line."""
        with open(self.filename, "r", encoding="utf-8") as handle:
            for line_no, raw_line in enumerate(handle, start=1):
                text = raw_line.split("#", 1)[0].strip()
                if text:
                    yield line_no, text


class MetadataParser:
    """Parse the optional ``[key=value ...]`` block of a statement."""

    @staticmethod
    def parse(
        line_no: int,
        raw: str | None,
        allowed_keys: set[str],
        context: str,
    ) -> dict[str, str]:
        """Parse a '[key=value ...]' block into a {key: raw_value} mapping."""
        metadata: dict[str, str] = {}
        if not raw:
            return metadata

        for token in raw.split():
            if "=" not in token:
                raise MapSyntaxError(
                    f"Malformed metadata token '{token}' in {context}: "
                    "expected 'key=value'",
                    line_no,
                )
            key, _, value = token.partition("=")
            if key not in allowed_keys:
                raise MapValidationError(
                    f"Unknown metadata key '{key}' in {context}. "
                    f"Allowed keys: {', '.join(sorted(allowed_keys))}",
                    line_no,
                )
            if not value:
                raise MapSyntaxError(
                    f"Metadata key '{key}' in {context} is missing a " "value",
                    line_no,
                )
            if key in metadata:
                raise MapValidationError(
                    f"Duplicate metadata key '{key}' in {context}",
                    line_no,
                )
            metadata[key] = value

        return metadata


class StatementParser:
    """Turn a single statement's raw text into structured data."""

    @staticmethod
    def parse_nb_drones(line_no: int, text: str) -> int:
        """Parse a ``nb_drones: <n>`` statement into its integer value."""
        match = _NB_DRONES_RE.match(text)
        if not match:
            raise MapSyntaxError(
                f"Malformed 'nb_drones' declaration: '{text}'", line_no
            )
        return StatementParser._parse_positive_int(line_no,
                                                   match.group("value"),
                                                   "nb_drones")

    @staticmethod
    def parse_hub(line_no: int, text: str) -> tuple[str, dict[str, object]]:
        """Parse a hub:/start_hub:/end_hub: statement into (kind, hub data)."""
        match = _HUB_RE.match(text)
        if not match:
            raise MapSyntaxError(f"Malformed hub declaration: '{text}'",
                                 line_no)

        kind = match.group("kind")
        name = match.group("name")
        if "-" in name:
            raise MapValidationError(
                f"Hub name '{name}' cannot contain a dash '-'", line_no
            )

        x = StatementParser._parse_coordinate(line_no, match, "x", name)
        y = StatementParser._parse_coordinate(line_no, match, "y", name)

        context = f"hub '{name}'"
        metadata = MetadataParser.parse(
            line_no, match.group("metadata"), HUB_METADATA_KEYS, context
        )
        if kind in ("start_hub", "end_hub"):
            if "max_drones" in metadata:
                nb_max_drones = StatementParser._parse_non_negative_int( # noqa
                    line_no,
                    str(metadata["max_drones"]),
                    "max_drones",
                )
                metadata.pop("max_drones", None)
        StatementParser._validate_hub_metadata(line_no, name, metadata)

        hub: dict[str, object] = {"name": name, "x": x, "y": y}
        hub.update(metadata)
        return kind, hub

    @staticmethod
    def parse_connection(line_no: int, text: str) -> dict[str, object]:
        """Parse a ``connection: <a>-<b> [metadata]`` statement."""
        match = _CONNECTION_RE.match(text)
        if not match:
            raise MapSyntaxError(f"Malformed connection declaration: '{text}'",
                                 line_no)

        hub1, hub2 = match.group("hub1"), match.group("hub2")
        context = f"connection '{hub1}-{hub2}'"
        raw_metadata = match.group("metadata")
        metadata = MetadataParser.parse(
            line_no, raw_metadata, CONNECTION_METADATA_KEYS, context
        )

        if raw_metadata is not None and "max_link_capacity" not in metadata:
            raise MapValidationError(
                f"Metadata block for {context} must specify "
                "'max_link_capacity'",
                line_no,
            )

        connection: dict[str, object] = {"from_zone": hub1, "to_zone": hub2}
        if "max_link_capacity" in metadata:
            connection["max_link_capacity"] = StatementParser._parse_positive_int(  # noqa
                line_no,
                metadata["max_link_capacity"],
                f"max_link_capacity for {context}",
            )
        return connection

    @staticmethod
    def _parse_coordinate(
        line_no: int, match: "re.Match[str]", field: str, hub_name: str
    ) -> int:
        """Validate and convert a hub's ``x`` or ``y`` coordinate."""
        token = match.group(field)
        if not _INT_RE.match(token):
            column = match.start(field) + 1
            raise MapValidationError(
                f"Invalid {field} coordinate '{token}' for hub "
                f"'{hub_name}': expected an integer",
                line_no,
                column,
            )
        return int(token)

    @staticmethod
    def _validate_hub_metadata(
        line_no: int, name: str, metadata: dict[str, str]
    ) -> None:
        """Validate and normalise the metadata of a hub, in place."""
        if "zone" in metadata:
            zone = metadata["zone"]
            if zone not in ZONE_TYPES:
                raise MapValidationError(
                    f"Invalid zone '{zone}'. Allowed values: "
                    f"{', '.join(ZONE_TYPES)}",
                    line_no,
                )

        if "color" in metadata:
            color = metadata["color"]
            if not color.isalpha():
                raise MapValidationError(
                    f"Invalid color '{color}' for hub '{name}': color "
                    "must contain letters only",
                    line_no,
                )

        if "max_drones" in metadata:
            metadata["max_drones"] = str(
                StatementParser._parse_positive_int(
                    line_no,
                    metadata["max_drones"],
                    f"max_drones for hub '{name}'",
                )
            )

    @staticmethod
    def _parse_positive_int(line_no: int, token: str, label: str) -> int:
        """Parse ``token`` as a strictly positive integer."""
        if not _INT_RE.match(token):
            raise MapValidationError(
                f"Invalid {label} value '{token}': expected a positive "
                "integer",
                line_no,
            )
        value = int(token)
        if value <= 0:
            raise MapValidationError(
                f"{label} must be greater than 0, got {value}", line_no
            )
        return value

    @staticmethod
    def _parse_non_negative_int(line_no: int, value: str, field: str) -> int:
        if not _INT_RE.match(value):
            raise MapValidationError(
                f"{field} must be an integer",
                line_no,
            )

        number = int(value)

        if number < 0:
            raise MapValidationError(
                f"{field} cannot be negative",
                line_no,
            )

        return number


class MapValidator:
    """Accumulate parsed statements and enforce the map's business rules."""

    def __init__(self) -> None:
        """Initialize empty state for a new map."""
        self.nb_drones: int | None = None
        self._nb_drones_line: int | None = None

        self._declared: dict[str, int] = {}
        self.hubs: list[dict[str, object]] = []
        self.start_hub: dict[str, object] | None = None
        self._start_line: int | None = None
        self.end_hub: dict[str, object] | None = None
        self._end_line: int | None = None

        self.connections: list[dict[str, object]] = []
        self._connection_pairs: set[frozenset[str]] = set()

    def register_nb_drones(self, line_no: int, value: int) -> None:
        """Record the (unique) ``nb_drones`` declaration."""
        if self.nb_drones is not None:
            raise MapStructureError(
                "Duplicate 'nb_drones' declaration; it was already set "
                f"on line {self._nb_drones_line}",
                line_no,
            )
        self.nb_drones = value
        self._nb_drones_line = line_no

    def register_hub(self, line_no: int, kind: str,
                     hub: dict[str, object]) -> None:
        """Record a hub, checking name uniqueness and section limits."""
        name = str(hub["name"])
        if name in self._declared:
            raise MapValidationError(f"Hub '{name}' is already defined",
                                     line_no)

        if kind == "start_hub":
            if self.start_hub is not None:
                raise MapStructureError(
                    "Duplicate 'start_hub' declaration; only one is "
                    f"allowed (already declared on line "
                    f"{self._start_line})",
                    line_no,
                )
            self.start_hub = hub
            self._start_line = line_no
        elif kind == "end_hub":
            if self.end_hub is not None:
                raise MapStructureError(
                    "Duplicate 'end_hub' declaration; only one is "
                    f"allowed (already declared on line "
                    f"{self._end_line})",
                    line_no,
                )
            self.end_hub = hub
            self._end_line = line_no
        else:
            self.hubs.append(hub)

        self._declared[name] = line_no

    def register_connection(self, line_no: int,
                            connection: dict[str, object]) -> None:
        """Record a connection, checking endpoints and duplicates."""
        hub1 = str(connection["from_zone"])
        hub2 = str(connection["to_zone"])

        if hub1 == hub2:
            raise MapValidationError(
                f"Connection {hub1}-{hub2} cannot connect a hub to " "itself",
                line_no,
            )
        if hub1 not in self._declared:
            raise MapValidationError(
                f"Connection references undefined hub '{hub1}'", line_no
            )
        if hub2 not in self._declared:
            raise MapValidationError(
                f"Connection references undefined hub '{hub2}'", line_no
            )

        pair = frozenset((hub1, hub2))
        if pair in self._connection_pairs:
            raise MapValidationError(
                f"Connection {hub1}-{hub2} already exists", line_no
            )

        self._connection_pairs.add(pair)
        self.connections.append(connection)

    def finalize(self) -> dict[str, object]:
        """Check the mandatory sections and build the final result."""
        if self.nb_drones is None:
            raise MapStructureError(
                "Missing required 'nb_drones' declaration; it must be "
                "the first line of the file"
            )
        if self.start_hub is None:
            raise MapStructureError("Missing required 'start_hub' declaration")
        if self.end_hub is None:
            raise MapStructureError("Missing required 'end_hub' declaration")

        return {
            "count": self.nb_drones,
            "Hubs": self.hubs,
            "start_hub": [self.start_hub],
            "end_hub": [self.end_hub],
            "Connections": self.connections,
        }


def parse_map(filename: str) -> dict[str, object] | None:
    validator = MapValidator()
    try:
        first_statement = True
        for line_no, text in MapReader(filename).statements():
            keyword_match = _KEYWORD_RE.match(text)
            if not keyword_match:
                raise MapSyntaxError(
                    f"Unrecognized statement '{text}': expected a line "
                    "starting with 'nb_drones:', 'hub:', 'start_hub:', "
                    "'end_hub:' or 'connection:'",
                    line_no,
                )
            keyword = keyword_match.group("keyword")

            if first_statement and keyword != "nb_drones":
                raise MapStructureError(
                    "The file must start with a 'nb_drones: <n>' "
                    "declaration",
                    line_no,
                )
            first_statement = False

            if keyword == "nb_drones":
                value = StatementParser.parse_nb_drones(line_no, text)
                validator.register_nb_drones(line_no, value)
            elif keyword in ("hub", "start_hub", "end_hub"):
                kind, hub = StatementParser.parse_hub(line_no, text)
                validator.register_hub(line_no, kind, hub)
            elif keyword == "connection":
                connection = StatementParser.parse_connection(line_no, text)
                validator.register_connection(line_no, connection)
            else:
                raise MapSyntaxError(
                    f"Unexpected statement '{keyword}': expected one of "
                    "'hub', 'start_hub', 'end_hub', 'connection'",
                    line_no,
                )

        return validator.finalize()

    except MapError as error:
        print(str(error))
        return None
    except OSError as error:
        print(f"Could not read map file '{filename}': {error}")
        return None
