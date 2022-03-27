"""Module for managing encoded protocols.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

import voluptuous as vol  # type: ignore

from remoteprotocols import validators as val
from remoteprotocols.codecs import decoder, encoder
from remoteprotocols.protocol import ArgDef, DecodeMatch, ProtocolDef, SignalData

TOGGLE_ARG = "_toggle"  # special arg can be referenced but not defined
TOGGLE_DEF = ArgDef({"min": 0, "max": 1, "name": TOGGLE_ARG})


class ValueOrArg:
    """Represents data in a rule, that can be either a constant value
    or a reference to an argument.
    """

    value: int = 0
    arg: int = 0

    def __repr__(self) -> str:
        return self.__dict__.__str__()

    def __init__(self, value: Optional[int] = None) -> None:
        if value:
            self.value = value

    def set_arg(self, arg: int) -> None:
        """Sets the arg number to point to"""

        self.arg = arg

    def get(self, args: Optional[list[int]]) -> int:
        """Returns the current value (own or referenced arg)"""

        if self.arg <= 0:
            return self.value
        if args is not None:
            return args[self.arg]
        return 0

    def has_arg(self) -> bool:
        """Whether it is pointing to an argument or a constant value"""
        return self.arg != 0


class RuleDef:
    """Definition of a single rule whithing a codec pattern"""

    type: int = 0  # -1 conditional | 0 data | >0 timings
    negate: bool = False
    data: ValueOrArg
    action: str = ""  # M: MSB | L: LSB || > | = | <
    operation: str = ""  # >: >> | <: << | + | - | * | / | & | '|'
    op_arg: int = 0
    nbits: ValueOrArg
    consequent: Optional[list[Any]] = None
    alternate: Optional[list[Any]] = None

    def __init__(self) -> None:
        self.data = ValueOrArg()
        self.nbits = ValueOrArg()

    def __repr__(self) -> str:
        return self.__dict__.__str__()

    def eval_op(self, data: int) -> int:
        """Evaluates the operation of the rule using 'data' as left argument of operator"""

        if self.negate:
            data = ~data  # pylint: disable=invalid-unary-operand-type

        # check operation
        if self.operation == "+":
            data += self.op_arg
        elif self.operation == "-":
            data -= self.op_arg
        elif self.operation == "*":
            data *= self.op_arg
        elif self.operation == "/":
            data = int(data / self.op_arg)
        elif self.operation == ">>":
            data >>= self.op_arg
        elif self.operation == "<<":
            data <<= self.op_arg
        elif self.operation == "&":
            data &= self.op_arg
        elif self.operation == "|":
            data |= self.op_arg
        elif self.operation == "^":
            data ^= self.op_arg

        return data

    def invert_op(self, data: int, nbits: int) -> Tuple[int, int]:
        """Inverts the operation of the rule"""
        mask = (1 << nbits) - 1

        if self.negate:
            data = (data & mask) ^ mask

        # check operation
        if self.operation == "+":
            data -= self.op_arg
            mask |= (1 << data.bit_length()) - 1
        elif self.operation == "-":
            data += self.op_arg
            mask |= (1 << data.bit_length()) - 1
        elif self.operation == "*":
            data = int(data / self.op_arg)
            mask |= (1 << data.bit_length()) - 1
        elif self.operation == "/":
            data *= self.op_arg
            mask |= (1 << data.bit_length()) - 1
        elif self.operation == ">>":
            data <<= self.op_arg
            mask <<= self.op_arg
        elif self.operation == "<<":
            data >>= self.op_arg
            mask >>= self.op_arg
        elif self.operation == "&":
            mask |= self.op_arg
        elif self.operation == "|":
            mask |= ~self.op_arg
        elif self.operation == "^":
            data ^= self.op_arg

        return (data, mask)

    def eval_cond(self, args: Optional[list[int]]) -> bool:
        """Evaluates if the condition of the rule is true"""

        # Case conditional rule
        if self.type != -1:
            return False

        data = self.eval_op(self.data.get(args))
        cond = self.nbits.get(args)

        # check operation
        if self.action == ">":
            return data > cond
        if self.action == "=":
            return data == cond
        if self.action == "<":
            return data < cond

        raise Exception(f"Invalid operation in rule '{self}'")


class PatternDef:
    """Pattern definition for transformation.
    Including rules and repeat information
    """

    pre: list[RuleDef]
    data: list[RuleDef]
    mid: list[RuleDef]
    post: list[RuleDef]

    repeat: ValueOrArg
    repeat_send: ValueOrArg

    def __init__(self, value: dict[(str, Any)]) -> None:
        for key, data in value.items():
            setattr(self, key, data)

    def __repr__(self) -> str:
        return self.__dict__.__str__()


class TimingsDef:
    """Definition of a preset of signal's timings"""

    frequency: ValueOrArg

    unit: ValueOrArg
    one: list[ValueOrArg]
    zero: list[ValueOrArg]
    slots: list[list[ValueOrArg]]

    names: list[str]

    def __init__(self, value: dict[(str, Any)], slot_names: list[str]) -> None:

        self.frequency = value["frequency"]
        self.unit = value["unit"]
        self.one = value["one"]
        self.zero = value["zero"]
        self.names = slot_names
        self.slots = []

        for name in slot_names:
            self.slots.append(value[name])

    def __repr__(self) -> str:
        return self.__dict__.__str__()

    def get_slot(self, index: int, args: Optional[list[int]]) -> list[int]:
        """Return timing pulses for a named slot"""

        if index >= len(self.slots):
            return []

        return [d.get(args) * self.unit.get(args) for d in self.slots[index]]

    def get_bit(self, value: int, args: Optional[list[int]]) -> list[int]:
        """Return timing pulse information for the one/zero data bit"""

        signal = self.one if value else self.zero
        return [d.get(args) * self.unit.get(args) for d in signal]

    def get_frequency(self, args: list[int]) -> int:
        """Returns frequency of the protocol"""
        return self.frequency.get(args)


class CodecDef(ProtocolDef):
    """Encoded protocol definition"""

    timings: list[TimingsDef]
    preset: ValueOrArg
    pattern: PatternDef

    _toggle: int = 0

    def __init__(self, value: dict[(str, Any)], name: str) -> None:
        for key, data in value.items():
            setattr(self, key, data)

        self.name = name

    def parse_args(self, args: list[Any]) -> list[int]:
        """Validates argument list and fills missing args with default values"""
        parsed: list[int] = []
        args_len = len(args)
        if args_len > len(self.args):
            raise vol.Invalid(
                f"Expected a maximum of {len(self.args)} arguments but got {args_len}"
            )

        for idx, arg in enumerate(self.args):

            validator = [val.integer, vol.Range(min=arg.min, max=arg.max)]
            if arg.values:
                validator.append(vol.In(arg.values))

            if idx < args_len:
                value = args[idx]
            elif arg.default is not None:
                value = arg.default
            else:
                vol.Invalid(f"Missing required argument <{arg.name}>")

            value = vol.All(*validator)(value)
            parsed.append(value)

        return parsed

    def to_command(self, args: list[int]) -> str:

        command = self.name
        args_len = len(args)
        if args_len > len(self.args):
            raise vol.Invalid(
                f"Expected a maximum of {len(self.args)} arguments but got {args_len}"
            )

        for idx, arg in enumerate(args):
            if self.args[idx].default is None or arg != self.args[idx].default:
                command += ":"

                prefix = self.args[idx].print.lower()[-1]
                if prefix in ("b", "x"):
                    command += f"0{prefix}"
                command += format(arg, self.args[idx].print)

        return command

    def encode(self, args: list[int]) -> SignalData:
        self._toggle ^= 1
        args = [self._toggle] + args

        signal = SignalData()
        preset = self.preset.get(args)

        if preset >= len(self.timings):
            return signal

        timings = self.timings[preset]

        signal.frequency = timings.get_frequency(args)
        signal.bursts = encoder.encode_pattern(self.pattern, args, timings)
        return signal

    def decode(self, signal: SignalData, tolerance: float = 0.25) -> list[DecodeMatch]:
        """Checks a signal against the protocol and if it maches returns
        the decoded arguments as list of matches, as potentially more than one timing preset could match.
        If no match the list has zero elements
        """

        decoded: list[DecodeMatch] = []

        # See if we need to decode a preset, if so try every timing info
        if self.preset.has_arg():
            for preset, timings in enumerate(self.timings):

                state = decoder.DecodeState(self, signal, tolerance, timings)
                result = decoder.decode_pattern(state)
                if result:
                    if state.args[self.preset.arg].update(preset, None):
                        decoded.append(decoder.create_match(state))

        else:
            state = decoder.DecodeState(
                self, signal, tolerance, self.timings[self.preset.value]
            )
            result = decoder.decode_pattern(state)
            if result:
                decoded.append(decoder.create_match(state))

        return decoded
