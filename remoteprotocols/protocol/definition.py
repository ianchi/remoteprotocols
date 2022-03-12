# Protocol Definition Classes

from typing import Any, Optional, Tuple, Union

import voluptuous as vol

TOGGLE_ARG = "_toggle"  # special arg can be referenced but not defined


class ValueOrArg:
    """Represents data in a rule, that can be either a constant value
    or a reference to an argument.
    """

    value: int = 0
    arg: int = 0

    def __repr__(self) -> str:
        return self.__dict__.__str__()

    def __init__(self, value: Union[int, None] = None) -> None:
        if value:
            self.value = value

    def set_arg(self, arg: int) -> None:
        self.arg = arg

    def get(self, args: Optional[list[int]]) -> int:
        if self.arg <= 0:
            return self.value
        if args is not None:
            return args[self.arg]
        return 0

    def has_arg(self) -> bool:
        return self.arg != 0


class RuleDef:
    """Definition of a single rule whithing a pattern"""

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
        for k, v in value.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        return self.__dict__.__str__()


class ArgDef:
    """Definition of a single argument"""

    name: str
    desc: Optional[str]
    default: Optional[int]
    example: Optional[int]
    print: str

    min: int = 0
    max: int
    values: list[int]

    def __init__(self, value: dict[(str, Any)]) -> None:
        self.values = []
        for k, v in value.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        return self.__dict__.__str__()

    def validate(self, value: Union[int, None]) -> int:
        """Validates argument against argument limits and returns replacing default"""

        if value is None:
            if hasattr(self, "default"):
                return self.default  # type: ignore
            raise vol.Invalid(f"Missing required argument <{self.name}>")

        if value > self.max:
            raise vol.Invalid(f"Argument <{self.name}> above maximum {self.max}")
        if value < self.min:
            raise vol.Invalid(f"Argument <{self.name}> below minimum {self.min}")
        if self.values and self.values.count(value) == 0:
            raise vol.Invalid(f"Argument <{self.name}> must be one of {self.values}")

        return value


TOGGLE_DEF = ArgDef({"min": 0, "max": 1, "name": "_toggle"})


class TimingsDef:
    """Definition a preset of signal's timings"""

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

        for g in slot_names:
            self.slots.append(value[g])

    def __repr__(self) -> str:
        return self.__dict__.__str__()

    def get_slot(self, index: int, args: Optional[list[int]]) -> list[int]:

        if index >= len(self.slots):
            return []

        return [d.get(args) * self.unit.get(args) for d in self.slots[index]]

    def get_bit(self, value: int, args: Optional[list[int]]) -> list[int]:

        signal = self.one if value else self.zero
        return [d.get(args) * self.unit.get(args) for d in signal]

    def get_frequency(self, args: list[int]) -> int:
        return self.frequency.get(args)


class ProtocolDef:

    name: str
    type: str
    desc: str
    note: str
    link: list[str]

    args: list[ArgDef]

    timings: list[TimingsDef]
    preset: ValueOrArg
    pattern: PatternDef

    _toggle: int = 0

    def __init__(self, value: dict[(str, Any)], name: str) -> None:
        for k, v in value.items():
            setattr(self, k, v)

        self.name = name

    def __repr__(self) -> str:
        return self.__dict__.__str__()

    def get_signature(self) -> str:
        signature = [self.name]

        for arg in self.args:
            if hasattr(arg, "default"):
                signature.append(f"<{arg.name}?={arg.default}>")
            else:
                signature.append(f"<{arg.name}>")

        return ":".join(signature)

    def validate_command(self, args: list[int]) -> None:
        """Validates argument list and fills missing args with default values"""

        args_len = len(args)
        if args_len > len(self.args):
            raise vol.Invalid(
                f"Expected a maximum of {len(self.args)} arguments but got {args_len}"
            )

        for idx, arg in enumerate(self.args):
            if idx < args_len:
                args[idx] = arg.validate(args[idx])
            else:
                args.append(arg.validate(None))

    def to_command(self, args: list[int]) -> str:

        command = self.name
        args_len = len(args)
        if args_len > len(self.args):
            raise vol.Invalid(
                f"Expected a maximum of {len(self.args)} arguments but got {args_len}"
            )

        for idx, arg in enumerate(args):
            # command += format(self.args[idx].validate(args[idx]), self.args[idx].print)
            command += ":"

            prefix = self.args[idx].print.lower()[-1]
            if prefix in ("b", "x"):
                command += f"0{prefix}"
            command += format(arg, self.args[idx].print)

        return command


class ProtocolRegistry:

    protocols: dict[(str, ProtocolDef)] = {}

    def add_protocols(self, protocols: dict[(str, ProtocolDef)]) -> None:
        if not hasattr(self, "protocols"):
            self.protocols = {}

        self.protocols.update(protocols)

    def get_protocol(self, name: str) -> Optional[ProtocolDef]:
        return self.protocols[name] if name in self.protocols else None

    def list_protocols(self) -> list[str]:
        if not hasattr(self, "protocols"):
            return []

        protocols = list(self.protocols)
        protocols.sort()
        return protocols


class SignalData:
    frequency: int
    bursts: list[int]

    def __repr__(self) -> str:
        return self.__dict__.__str__()
