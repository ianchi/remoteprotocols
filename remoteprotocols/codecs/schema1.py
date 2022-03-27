"""First pass of protocol schema validation, at element level
Validates basic structure and performs first type conversion and feeds it into
the second pass (at object level)
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol  # type: ignore

import remoteprotocols.validators as val
from remoteprotocols.codecs import TOGGLE_ARG
from remoteprotocols.codecs.schema2 import (
    protocol_class,
    validate_arg_pass2,
    validate_protocol_pass2,
)

PROTO_TYPES = ["IR", "RF", "IR/RF"]

ARG_SCHEMA = vol.Schema(
    {
        vol.Required("name"): vol.Any(TOGGLE_ARG, val.valid_name),
        vol.Required("desc"): val.coerce_string,
        vol.Optional("default"): val.integer,
        vol.Optional("example"): val.integer,
        vol.Optional("print", default="X"): val.coerce_string,
        vol.Optional("min", default=0): val.integer,
        vol.Required("max"): val.integer,
        vol.Optional("values"): [val.integer],
    }
)

TIMING_SCHEMA = vol.All([val.value_or_arg], val.alternating_signs)
TIMINGS_SCHEMA = vol.Schema(
    {
        vol.Required("frequency"): val.value_or_arg,
        vol.Required("one"): TIMING_SCHEMA,
        vol.Required("zero"): TIMING_SCHEMA,
        vol.Optional("unit", default=1): val.value_or_arg,
        val.valid_name: TIMING_SCHEMA,
    }
)

PATTERN_SCHEMA = vol.Schema(
    {
        vol.Optional("pre"): val.string_strict,
        vol.Required("data"): val.string_strict,
        vol.Optional("mid"): val.string_strict,
        vol.Optional("post"): val.string_strict,
        vol.Optional("repeat"): val.value_or_arg,
        vol.Optional("repeat_send"): val.value_or_arg,
    }
)


def pattern_or_string(value: Any) -> dict[(str, Any)]:
    """Converts direct string definition of pattern into an object"""
    if isinstance(value, str):
        value = {"data": value}
    elif not isinstance(value, dict):
        raise vol.Invalid(
            f"Pattern definition must be a string or an object but got {value}"
        )

    return PATTERN_SCHEMA(value)  # type: ignore


PROTOCOL_DEF_SCHEMA = vol.All(
    # First Pass
    {
        vol.Required("desc"): val.coerce_string,
        vol.Required("type"): vol.In(PROTO_TYPES),
        vol.Optional("link"): [val.coerce_string],
        vol.Optional("note"): val.string_strict,
        vol.Required("pattern"): pattern_or_string,
        vol.Required("args"): vol.All(
            [ARG_SCHEMA],
            vol.Length(min=1),
            val.unique_field_value("name"),
            [validate_arg_pass2],  # second pass
        ),
        vol.Required("timings"): vol.All(
            val.coerce_list(), [TIMINGS_SCHEMA], vol.Length(min=1)
        ),
        vol.Optional("preset", default=0): val.value_or_arg,
    },
    # Second Pass
    validate_protocol_pass2,
)

PROTOCOLS_DEF_SCHEMA = vol.All({val.valid_name: PROTOCOL_DEF_SCHEMA}, protocol_class)
