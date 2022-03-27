"""Xiaomi Miio raw format module"""

from __future__ import annotations

import base64
from typing import Any, Set

import voluptuous as vol  # type: ignore

from remoteprotocols import validators as val
from remoteprotocols.protocol import ArgDef, DecodeMatch, ProtocolDef, SignalData

# protocol definition credit to:
# https://github.com/rytilahti/python-miio/blob/master/miio/chuangmi_ir.py

# 0: 0xA567
# 1: edge_counts
# 2: times_index
# 3...: edge_pairs

HEADER1 = 0xA5
HEADER2 = 0x67


class MiioFormat(ProtocolDef):
    """Miio b64 raw format implementation"""

    name: str = "miio"
    desc: str = "Miio base64 raw format"
    type: str = "raw"

    args: list[ArgDef] = [
        ArgDef({"name": "b64", "desc": "Base 64 encoded data"}),
        ArgDef({"name": "frequency", "desc": "Frequency", "default": 38400}),
    ]

    def parse_args(self, args: list[Any]) -> list[int]:

        vol.Length(min=1, max=2)(args)

        frequency: int = val.integer(args[1]) if len(args) == 2 else 0

        b64 = base64.b64decode(args[0])
        result: list[int] = []

        # check length
        if len(b64) < 6:
            raise vol.Invalid("No header data")

        if b64[0] != HEADER1 or b64[1] != HEADER2:
            raise vol.Invalid("Invalid data header")

        pairs = int((b64[2] * 256 + b64[3] + 1) / 2)
        data = b64[-pairs:]  # 1 par per bytes

        times = []
        for idx in range(4, len(b64) - pairs + 1, 2):
            times.append((b64[idx] << 8) + b64[idx + 1])

        for byte in data:
            result.append(times[byte & 0xF])
            result.append(times[byte >> 4])

        # Arg N frequency
        result.append(frequency)

        return result

    def to_command(self, args: list[int]) -> str:

        command = "miio:"

        edges = len(args[:-1]) - 1
        data: bytearray = bytearray([HEADER1, HEADER2, edges >> 8, edges & 0xFF])

        times: Set[int] = set()
        for burst in args[:-1]:
            times.add(burst)
        times_sorted = sorted(times)
        for time in times_sorted:
            data += bytearray([(time >> 8), (time & 0xFF)])

        if len(times_sorted) > 0xF:
            raise vol.Invalid("Too many different pulse lengths in signal")

        times_map = {t: idx for idx, t in enumerate(times_sorted)}
        for idx in range(0, len(args[:-2]), 2):
            data += bytearray([times_map[args[idx]] + (times_map[args[idx + 1]] << 4)])

        b64 = base64.b64encode(data)
        command += b64.decode("UTF-8")

        if args[-1]:
            command += f":{args[-1]}"

        return command

    def encode(self, args: list[int]) -> SignalData:

        result = SignalData()

        result.frequency = args[-1]

        result.bursts = []
        sign = 1
        for pulse in args[:-1]:
            result.bursts.append(pulse * sign)
            sign *= -1

        return result

    def decode(self, signal: SignalData, _tolerance: float = 0.25) -> list[DecodeMatch]:

        match = DecodeMatch()
        match.protocol = self
        match.args = []

        if signal.bursts and signal.bursts[0] < 0:
            # cannot encode inverted signals
            return []

        # TODO: need to round signal to generate map of max 16 entries??
        for burst in signal.bursts:
            match.args.append(round(abs(burst) / 10) * 10)

        # must be all pairs
        # if it ends High, add a minimum pause
        # TODO: find a better logic that a double time
        if len(signal.bursts) % 2:
            match.args.append(round(abs(signal.bursts[-1] / 10)) * 20)

        match.args.append(signal.frequency)

        return [match]
