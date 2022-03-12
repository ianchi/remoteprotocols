import copy
from typing import Any, Optional, Tuple

from remoteprotocols.protocol.definition import (
    TOGGLE_DEF,
    ArgDef,
    ProtocolDef,
    ProtocolRegistry,
    RuleDef,
    SignalData,
    TimingsDef,
    ValueOrArg,
)


class DecodedArg:
    value: int = 0
    mask: int = 0
    decoded_mask: int = 0
    min: int
    max: int
    values: list[int]

    def __init__(self, arg: ArgDef) -> None:
        self.mask = (1 << arg.max.bit_length()) - 1
        self.max = arg.max
        self.min = arg.min
        if hasattr(arg, "values"):
            self.values = arg.values

    def update(self, value: int, mask: Optional[int]) -> bool:

        # if no mask, assume whole value is decoded
        if mask is None:
            mask = self.mask
        # check value is consistent with already decoded part
        if (self.value & mask) != (value & self.decoded_mask):
            return False

        if value > self.max:
            return False

        # TODO: check form min, considering partial mask
        # if value < self.min:

        # TODO: check for values, considering partial mask

        self.decoded_mask |= mask
        self.value |= value

        return True


class DecodeState:

    protocol: ProtocolDef
    signal: SignalData
    decoded: int = 0
    tolerance: float = 0.25
    used_tolerance: float = 0

    args: list[DecodedArg]
    timings: TimingsDef

    def __init__(
        self,
        proto: ProtocolDef,
        signal: SignalData,
        tolerance: float,
        timings: TimingsDef,
    ) -> None:
        self.signal = signal
        self.tolerance = tolerance
        self.timings = timings
        self.protocol = proto

        # generate empty decoded args
        empty_args = [DecodedArg(TOGGLE_DEF)]
        for arg in proto.args:
            empty_args.append(DecodedArg(arg))
        self.args = empty_args

    def __deepcopy__(self, memo=None):  # type: ignore
        dst = copy.copy(self)
        dst.args = copy.deepcopy(self.args, memo)
        return dst

    def update(self, src: Any) -> None:
        self.decoded = src.decoded
        self.args = src.args

    def expect_burst(self, burst: list[int]) -> bool:
        """Check if the following burst of data coincide with the expected.
        If true advances the decoded reference.
        """

        decoded = self.decoded
        if len(burst) == 0:
            return True

        if len(burst) > (len(self.signal.bursts) - self.decoded):
            return False

        for b in burst:
            expect = self.signal.bursts[decoded]
            tolerance = self.tolerance if expect >= 0 else -self.tolerance

            if expect * (1 - tolerance) <= b <= expect * (1 + tolerance):
                decoded += 1
                self.used_tolerance = max(self.used_tolerance, abs(b - expect) / expect)

            else:
                return False

        self.decoded = decoded
        return True

    def read_data(self, expected_bits: ValueOrArg, lsb: bool) -> Tuple[bool, int, int]:
        data = 0
        bit = 0
        nbits = 0
        one = self.timings.get_bit(1, None)
        zero = self.timings.get_bit(0, None)
        while True:
            if self.expect_burst(one):
                bit = 1
            elif self.expect_burst(zero):
                bit = 0
            else:
                break

            if lsb:
                data |= bit << nbits
            else:
                data <<= 1
                data |= bit
            nbits += 1
            if not expected_bits.has_arg() and expected_bits.value == nbits:
                break
            if expected_bits.has_arg() and nbits == self.args[expected_bits.arg].max:
                break

        if (not expected_bits.has_arg() and nbits != expected_bits.value) or nbits == 0:
            return (False, data, nbits)

        return (True, data, nbits)


class DecodeMatch:
    protocol: ProtocolDef
    args: list[int]
    missing_bits: list[int]
    uniquematch: bool = True
    toggle_bit: int
    tolerance: float

    def __repr__(self) -> str:
        return self.__dict__.__str__()

    def __init__(self, state: DecodeState) -> None:
        self.protocol = state.protocol
        self.args = []
        self.missing_bits = []
        self.tolerance = state.used_tolerance

        self.toggle_bit = state.args[0].value
        for arg in state.args[1:]:

            # if any arg is incompletely decoded the match is not unique
            if arg.decoded_mask != arg.mask:
                self.uniquematch = False
            self.args.append(arg.value)
            self.missing_bits.append(arg.decoded_mask ^ arg.mask)


# pylint:
def decode_rule(self: DecodeState, rule: RuleDef) -> bool:

    decoded = self.decoded

    # Case named timings rule:
    if rule.type > 0:

        burst = self.timings.get_slot(rule.type - 1, None)
        return self.expect_burst(burst)

    # Case data rule
    if rule.type == 0:

        is_data, data, nbits = self.read_data(rule.nbits, rule.action == "L")

        if not is_data:
            self.decoded = decoded
            return False

        if rule.nbits.has_arg():
            # check compatibility and update arg
            if not self.args[rule.nbits.arg].update(nbits, None):
                self.decoded = decoded
                return False

        arg, mask = rule.invert_op(data, nbits)

        if rule.data.has_arg():
            a = self.args[rule.data.arg]
        else:
            a = DecodedArg(
                ArgDef(
                    {
                        "min": rule.data.value,
                        "max": rule.data.value,
                    }
                )
            )
            a.update(rule.data.value, None)

        if not a.update(arg, mask):
            self.decoded = decoded
            return False

        return True

    # Case conditional rule
    if rule.type < 0:

        subdecoder = copy.deepcopy(self)

        # Try 'True' branch

        if decode_rules(subdecoder, rule.consequent):  # type:ignore

            # confirm arg is consistent with condition
            if confirm_cond(rule, subdecoder.args):
                self.update(subdecoder)
            return True

        # Try 'False' branch
        if rule.alternate:
            subdecoder = copy.deepcopy(self)
            if decode_rules(subdecoder, rule.alternate):

                # TODO confirm arg is consistent with condition
                # if not rule.eval_cond(subdecoder.args):
                self.update(subdecoder)
                return True

    return True


def confirm_cond(rule: RuleDef, args: list[DecodedArg]) -> bool:
    # Only Case conditional rule
    if rule.type != -1:
        return False

    # Case fully decoded arg -> validate
    if not (args[rule.data.arg].decoded_mask ^ args[rule.data.arg].mask):

        data = rule.eval_op(args[rule.data.arg].value)
        cond = rule.nbits.value

        # check operation
        if rule.action == ">":
            return data > cond
        if rule.action == "=":
            return data == cond
        if rule.action == "<":
            return data < cond

    # try to infer
    else:
        # known fixed value
        if rule.action == "=":
            data, mask = rule.invert_op(
                rule.nbits.value, args[rule.data.arg].mask.bit_length()
            )
            if args[rule.data.arg].update(data, mask):
                return True

        # TODO <, > cases
    return False


def decode_rules(state: DecodeState, rules: list[RuleDef]) -> bool:

    for rule in rules:
        if not decode_rule(state, rule):
            return False

    return True


def decode_pattern(state: DecodeState) -> bool:

    decode_repeat = False
    expected_repeat = 1
    # See if we need to consider a minim repeat
    if hasattr(state.protocol.pattern, "repeat"):
        if state.protocol.pattern.repeat.has_arg():
            decode_repeat = True
        else:
            expected_repeat = state.protocol.pattern.repeat.value

    # pre and post are not included in repeat
    if hasattr(state.protocol.pattern, "pre"):
        result = decode_rules(state, state.protocol.pattern.pre)
        if not result:
            return False

    repeat = 0
    while True:
        result = decode_rules(state, state.protocol.pattern.data)
        if result and hasattr(state.protocol.pattern, "mid"):
            result = decode_rules(state, state.protocol.pattern.mid)

        if not result:
            # No match in first pass, always wrong
            if repeat < expected_repeat:
                return False

            # end of match, decode number of repeats
            if decode_repeat:
                if not state.args[state.protocol.pattern.repeat.arg].update(
                    repeat, None
                ):
                    return False
                break

        repeat += 1
        if repeat == expected_repeat and not decode_repeat:
            break

    if hasattr(state.protocol.pattern, "post"):
        result = decode_rules(state, state.protocol.pattern.post)
        if not result:
            return False

    return True


def decode_protocol(
    proto: ProtocolDef, signal: SignalData, tolerance: float = 0.25
) -> list[DecodeMatch]:
    """Checks a signal against a protocol and if it maches returns
    the decoded arguments as list of matches, as potentially more than one timing preset could match.
    If no match the list has zero elements
    """

    decoded: list[DecodeMatch] = []

    # See if we need to decode a preset, if so try every timing info
    if proto.preset.has_arg():
        for preset, timings in enumerate(proto.timings):

            state = DecodeState(proto, signal, tolerance, timings)
            result = decode_pattern(state)
            if result:
                if state.args[proto.preset.arg].update(preset, None):
                    decoded.append(DecodeMatch(state))

    else:
        state = DecodeState(proto, signal, tolerance, proto.timings[proto.preset.value])
        result = decode_pattern(state)
        if result:
            decoded.append(DecodeMatch(state))

    return decoded


def decode(
    signal: SignalData, registry: ProtocolRegistry, tolerance: float = 0.25
) -> list[DecodeMatch]:

    decoded: list[DecodeMatch] = []

    for name in registry.list_protocols():

        decoded += decode_protocol(
            registry.get_protocol(name), signal, tolerance  # type:ignore
        )

    return decoded
