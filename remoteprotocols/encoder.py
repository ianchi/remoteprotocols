from remoteprotocols.protocol.definition import (
    PatternDef,
    ProtocolDef,
    RuleDef,
    SignalData,
    TimingsDef,
)


def encode_rule(rule: RuleDef, args: list[int], timings: TimingsDef) -> list[int]:

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
    rules: list[RuleDef], args: list[int], timings: TimingsDef
) -> list[int]:
    signal = []

    for rule in rules:
        signal += encode_rule(rule, args, timings)

    return signal


def encode_pattern(
    pattern: PatternDef, args: list[int], timings: TimingsDef
) -> list[int]:

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


def encode_proto(proto: ProtocolDef, args: list[int]) -> SignalData:
    proto._toggle ^= 1
    args = [proto._toggle] + args

    signal = SignalData()
    preset = proto.preset.get(args)

    if preset >= len(proto.timings):
        return signal

    timings = proto.timings[preset]

    signal.frequency = timings.get_frequency(args)
    signal.bursts = encode_pattern(proto.pattern, args, timings)
    return signal
