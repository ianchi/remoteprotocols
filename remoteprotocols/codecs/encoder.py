"""Classes and functions to perform encoding"""

from __future__ import annotations

# pylint: disable=cyclic-import
from remoteprotocols import codecs


def encode_rule(
    rule: codecs.RuleDef, args: list[int], timings: codecs.TimingsDef
) -> list[int]:
    """Converts a single rule into signal pulses"""

    # Case named timings rule:
    if rule.type > 0:
        return timings.get_slot(rule.type - 1, args)

    # Case data rule
    if rule.type == 0:
        data = rule.eval_op(rule.data.get(args))
        nbits = rule.nbits.get(args)
        if rule.action == "M":
            bits = range(nbits - 1, -1, -1)
        else:
            bits = range(0, nbits, 1)

        signal = []
        for i in bits:
            signal += timings.get_bit(data & (1 << i), args)

        return signal

    # Case condition rule
    if rule.type == -1:

        if rule.eval_cond(args):
            return encode_rules(rule.consequent, args, timings)  # type: ignore
        if rule.alternate:
            return encode_rules(rule.alternate, args, timings)

    return []


def encode_rules(
    rules: list[codecs.RuleDef], args: list[int], timings: codecs.TimingsDef
) -> list[int]:
    """Converts a list of rules into signal pulses"""
    signal = []

    for rule in rules:
        signal += encode_rule(rule, args, timings)

    return signal


def encode_pattern(
    pattern: codecs.PatternDef, args: list[int], timings: codecs.TimingsDef
) -> list[int]:
    """Converts a pattern into the corresponding signal"""

    result = []

    repeat = 1
    if hasattr(pattern, "repeat_send"):
        repeat = pattern.repeat_send.get(args)
    elif hasattr(pattern, "repeat"):
        repeat = pattern.repeat.get(args)

    if hasattr(pattern, "pre"):
        result += encode_rules(pattern.pre, args, timings)
    for _ in range(repeat):
        result += encode_rules(pattern.data, args, timings)
        if hasattr(pattern, "mid"):
            result += encode_rules(pattern.mid, args, timings)

    if hasattr(pattern, "post"):
        result += encode_rules(pattern.post, args, timings)

    return result
