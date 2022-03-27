"""Functions for parsing patterns into RuleDef objects"""

from __future__ import annotations

import re
from typing import List, Tuple, Union

import voluptuous as vol  # type: ignore

import remoteprotocols.validators as val
from remoteprotocols.codecs import TOGGLE_ARG, RuleDef

# Functions for parsing a pattern


def get_argn(name: str, args: list[str]) -> int:
    """Returns the index number of a named argument"""
    argn = 0
    if name == TOGGLE_ARG:
        argn = 0
    else:
        try:
            vol.Schema(vol.Any(*args))(name)
            argn = args.index(name) + 1
        except vol.Invalid:
            raise vol.Invalid(f"Argument '{name}' not defined")

    return argn


def check_timings(value: str, timings: list[str]) -> None:
    """Validate that a reference is a valid timming slot"""
    try:
        vol.In(timings)(value)
    except vol.Invalid:
        raise vol.Invalid(f"Reference to undefined timings group '{value}'")


def parse_rule(
    pattern: str, timings: List[str], args: List[str]
) -> Tuple[str, Union[RuleDef, None]]:
    """Parse the first rule of the pattern, and returns the rest of the string.
    It errors if there is no valid pattern.
    """
    re_timing = re.compile(r"^\s*([a-z_][a-z0-9_]*)")
    re_data = re.compile(
        r"^\s*\{\s*(?:(~?)([a-z_][a-z0-9_]*)|(0x[0-9a-fA-F]+|0b[01]+|[0-9]+))\s*(?:(>>|<<|\+|-|\*|\/|&|\^|\|)\s*(0x[0-9a-fA-F]+|0b[01]+|[0-9]+))?\s+(LSB|MSB)\s+(?:([a-z_][a-z0-9_]*)|(0x[0-9a-fA-F]+|0b[01]+|[0-9]+))\s*\}"
    )
    # m1:complement m2:arg_data m3:const_data m4:operator m5: op_arg m6:bitorder m7:arg_nbits m8:arg_const

    re_condition = re.compile(
        r"^\s*\(\s*(~?)([a-z_][a-z0-9_]*)\s*(?:(>>|<<|\+|-|\*|\/|&|\^|\|)\s*(0x[0-9a-fA-F]+|0b[01]+|[0-9]+))?\s*(>|<|=)\s*(0x[0-9a-fA-F]+|0b[01]+|[0-9]+)\s*\?"
    )
    re_condition_alternate = re.compile(r"^\s*:")
    # m1:complement m2:arg_data m3: operation m4: op_arg m5:comparison m5: ref value
    re_condition_close = re.compile(r"^\s*\)")
    re_empty = re.compile(r"^\s*")

    rule: Union[RuleDef, None]
    rule = RuleDef()
    consumed: int = 0

    # 1) check if it is a named timing slot
    match = re_timing.match(pattern)
    if match:
        check_timings(match[1], timings)
        rule.type = timings.index(match[1]) + 1  # timing number
        consumed = match.end()
    else:
        # check if it is a data block
        match = re_data.match(pattern)

        if match:
            rule.type = 0  # data
            rule.negate = match[1] == "~"
            rule.data.arg = get_argn(match[2], args) if match[2] else 0
            rule.data.value = val.integer(match[3]) if match[3] else 0
            rule.operation = match[4][0] if match[4] else "0"
            rule.op_arg = val.integer(match[5]) if match[5] else 0
            rule.action = match[6][0] if match[6] else "0"
            rule.nbits.arg = get_argn(match[7], args) if match[7] else 0
            rule.nbits.value = val.integer(match[8]) if match[8] else 0
            consumed = match.end()

        else:
            match = re_condition.match(pattern)
            if match:
                rule.type = -1  # conditional
                rule.negate = match[1] == "~"
                rule.data.arg = get_argn(match[2], args) if match[2] else 0
                rule.operation = match[3][0] if match[3] else "0"
                rule.op_arg = val.integer(match[4]) if match[4] else 0
                rule.action = match[5][0]
                rule.nbits.value = val.integer(match[6]) if match[6] else 0

                pattern, subexp = parse_subexp(pattern[match.end() :], timings, args)
                if not subexp:
                    raise vol.Invalid(f"Missing consequent in conditional: {pattern}")
                rule.consequent = subexp

                match = re_condition_alternate.match(pattern)
                if match:
                    pattern, subexp = parse_subexp(
                        pattern[match.end() :], timings, args
                    )
                    if not subexp:
                        raise vol.Invalid(
                            f"Missing alternate in conditional: {pattern}"
                        )
                    rule.alternate = subexp

                match = re_condition_close.match(pattern)
                if match:
                    consumed = match.end()

            # consume empty string
            else:
                match = re_empty.match(pattern)
                if match:
                    consumed = match.end()
                    match = None

    if not match:
        rule = None

    return (pattern[consumed:], rule)


def parse_subexp(
    pattern: str, timings: List[str], args: List[str]
) -> Tuple[str, list[RuleDef]]:
    """Parse a susecion of o or more consecutive rules"""
    subexp: list[RuleDef] = []

    while pattern:

        pattern, rule = parse_rule(pattern, timings, args)

        if rule is not None:
            subexp.append(rule)
        else:
            break

    return (pattern, subexp)


def parse_pattern(pattern: str, timings: List[str], args: List[str]) -> list[RuleDef]:
    """Parse a pattern string and returns a list of rules.
    It must have at least one valid rule and consume the whole pattern
    """

    pattern, rules = parse_subexp(pattern, timings, args)

    if pattern:
        raise vol.Invalid(f"Invalid pattern format at: {pattern}")

    return rules
