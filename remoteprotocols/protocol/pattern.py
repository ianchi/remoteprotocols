import re
from typing import List, Tuple, Union

import voluptuous as vol  # type: ignore

import remoteprotocols.validators as val
from remoteprotocols.protocol.definition import TOGGLE_ARG, RuleDef

# Functions for parsing a pattern


def get_argn(name: str, args: list[str]) -> int:
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
    m = re_timing.match(pattern)
    if m:
        check_timings(m[1], timings)
        rule.type = timings.index(m[1]) + 1  # timing number
        consumed = m.end()
    else:
        # check if it is a data block
        m = re_data.match(pattern)

        if m:
            rule.type = 0  # data
            rule.negate = m[1] == "~"
            rule.data.arg = get_argn(m[2], args) if m[2] else 0
            rule.data.value = val.integer(m[3]) if m[3] else 0
            rule.operation = m[4][0] if m[4] else "0"
            rule.op_arg = val.integer(m[5]) if m[5] else 0
            rule.action = m[6][0] if m[6] else "0"
            rule.nbits.arg = get_argn(m[7], args) if m[7] else 0
            rule.nbits.value = val.integer(m[8]) if m[8] else 0
            consumed = m.end()

        else:
            m = re_condition.match(pattern)
            if m:
                rule.type = -1  # conditional
                rule.negate = m[1] == "~"
                rule.data.arg = get_argn(m[2], args) if m[2] else 0
                rule.operation = m[3][0] if m[3] else "0"
                rule.op_arg = val.integer(m[4]) if m[4] else 0
                rule.action = m[5][0]
                rule.nbits.value = val.integer(m[6]) if m[6] else 0

                pattern, subexp = parse_subexp(pattern[m.end() :], timings, args)
                if not subexp:
                    raise vol.Invalid(f"Missing consequent in conditional: {pattern}")
                rule.consequent = subexp

                m = re_condition_alternate.match(pattern)
                if m:
                    pattern, subexp = parse_subexp(pattern[m.end() :], timings, args)
                    if not subexp:
                        raise vol.Invalid(
                            f"Missing alternate in conditional: {pattern}"
                        )
                    rule.alternate = subexp

                m = re_condition_close.match(pattern)
                if m:
                    consumed = m.end()

            # consume empty string
            else:
                m = re_empty.match(pattern)
                if m:
                    consumed = m.end()
                    m = None

    if not m:
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
