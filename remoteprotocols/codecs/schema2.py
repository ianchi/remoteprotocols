"""Second pass of protocol validation, pattern parsing and convertion to class objects.
"""
from __future__ import annotations

from typing import Any, Union

import voluptuous as vol  # type: ignore

from remoteprotocols.codecs import CodecDef, PatternDef, RuleDef, TimingsDef, ValueOrArg
from remoteprotocols.protocol import ArgDef

from .pattern import parse_pattern


def validate_arg_pass2(arg: dict[(str, Any)]) -> ArgDef:
    """Validates that the provided default and example are valid against the argument rules.
    Converts argument to class
    """
    validator = vol.Range(min=arg["min"], max=arg["max"])
    if "values" in arg:
        validator = vol.All(vol.In(arg["values"]), validator)
    vol.Schema(
        {vol.Optional("default"): validator, vol.Optional("example"): validator},
        extra=vol.ALLOW_EXTRA,
    )(arg)

    return ArgDef(arg)


def validate_protocol_pass2(proto: dict[(str, Any)]) -> dict[(str, Any)]:
    """Validates a protocol definition at a integral level.
    Validity of patterns and arguments references
    """

    t_slots = list(proto["timings"][0])
    t_slots.remove("frequency")
    t_slots.remove("unit")
    t_slots.remove("one")
    t_slots.remove("zero")

    args = [a.name for a in proto["args"]]

    # check timings variables and blocks

    def value_or_valid_arg(value: Union[str, int]) -> ValueOrArg:

        data = ValueOrArg()

        if isinstance(value, int):
            data.value = value
        elif isinstance(value, str):
            vol.In(args)(value)
            data.arg = args.index(value) + 1
        else:
            raise vol.Invalid(
                f"Invalid format for timing, should be integer o argument reference but got '{value}'"
            )

        return data

    t_schema = {
        vol.Required("frequency"): value_or_valid_arg,
        vol.Optional("unit", default=ValueOrArg(1)): value_or_valid_arg,
        vol.Required("one"): [value_or_valid_arg],
        vol.Required("zero"): [value_or_valid_arg],
    }

    for slot in t_slots:
        t_schema[vol.Required(slot)] = [value_or_valid_arg]

    # backup original string pattern
    proto["pattern_"] = proto["pattern"].copy()

    # check pattern and replace with parsed data
    def check_pattern(value: str) -> list[RuleDef]:
        return parse_pattern(value, t_slots, args)

    def pattern_class(value: dict[(str, Any)]) -> PatternDef:
        return PatternDef(value)

    def timings_class(value: dict[(str, Any)]) -> TimingsDef:
        return TimingsDef(value, t_slots)

    return vol.Schema(  # type: ignore
        {
            "timings": vol.All([t_schema], [timings_class]),
            "pattern": vol.All(
                {
                    vol.Optional("pre"): check_pattern,
                    vol.Required("data"): check_pattern,
                    vol.Optional("mid"): check_pattern,
                    vol.Optional("post"): check_pattern,
                    vol.Optional("repeat"): value_or_valid_arg,
                    vol.Optional("repeat_send"): value_or_valid_arg,
                },
                pattern_class,
            ),
            "preset": value_or_valid_arg,
        },
        extra=vol.ALLOW_EXTRA,
    )(proto)


def protocol_class(value: dict[(str, Any)]) -> dict[str, CodecDef]:
    """Converts to dict of CodecDef objects"""
    result = {}

    for name, proto in value.items():
        result[name] = CodecDef(proto, name)

    return result
