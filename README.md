# remoteprotocols

`remoteprotocols` is a command line utility and a Python's library to convert between more than 20 encoded IR and 5 RF remote protocols (nec, jvc, RC switch, see [full protocol list](https://github.com/ianchi/remoteprotocols/tree/master/PROTOCOLS.md)) and 4 raw formats (pronto, Broadlink, Xiaomi miio, raw durations) and between those. The goal is to be able to use any existing code listing with any transmitter, and to be able to decode raw signal received by any device into the proper encoded format.

## Remote command strings

To interact with _remoteprotocols_ you'll be using remote commands to encode/decode/convert using the following syntax:

```bash
protocol:<arg 1>:<arg 2>: ... :<arg n>

# Example signatures
sony:<data>:<nbits?=12>
toshiba_ac:<rc_code_1>:<rc_code_2?=0>

# Example usage
nec16:0x7A:0x57
```

You can get a list of all supported protocols and their command signatures [here](https://github.com/ianchi/remoteprotocols/tree/master/PROTOCOLS.md), and from the command line.

Optional arguments can be omitted, with empty `::` in the middle or completely omitting the colon at the end.

## Command line

You can use _remoteprotocols_ from the command line:

```
usage: remoteprotocols [-h] [-v] command ...

remoteprotocols v0.0.1

positional arguments:
  command            Command to run:
    validate-protocol
                     Validate a protocol definition file.
    validate-command
                     Validate a send command string(s).
    encode           Encodes command string(s) into raw signal (durations).
    convert          Converts command string(s) to other protocols.
    list             List supported protocols.

optional arguments:
  -h, --help         show this help message and exit
  -v, --version      Show version information.
```

## API usage

To interact with _remoteprotocols_ from your own program you import it and interact with it thru the registry, which has all built-in protocol definitions

```python
from remoteprotocols import ProtocolRegistry


protocols = ProtocolRegistry()

matches = protocols.convert("nec:0x7A:0x57", 0.2, ["durations", "broadlink"])

```

Main _ProtocolRegistry_ methods:

- **convert**(_command_:str, _tolerance_: float, _codec_filter_:list[str]) -> list[DecodeMatch]
  Converts a given command into other protocols (all or filtered).
  Returns a list of _DecodeMatch_ objects with the successful conversions, or an empty list if it couldn't convert.
  The match has the following attributes:

  - _protocol_: the matched protocol as a _ProtocolDef_ object
  - _args_: an array of parsed arguments (including default ones)
  - _tolerance_: the tolerance needed to match this protocol (lower better match)
  - _uniquematch_: boolean indicating if the match is unique for this protocol. It should always be true for well defined protocols. When _false_, it means that the returned match is one out of multiple results that would encode in the same signal
  - _missing_bits_: array of bitmasks of bits for each argument, that could not be decoded, and thus any value in those bits would be a valid result. If any mask is non zero, then the match is not unique for the protocol
  - _toggle_bit_: state of the toggle bit (internal argument). Only relevant for protocols that use it (like RC5)

- **decode**(signal: SignalData, tolerance: float, protocol: Optional[list[str]])-> list[DecodeMatch]

  Decodes a signal (optional frequency & array of durations) and returns a list of all matching protocols and corresponding decoded arguments. It decodes into all known protocols or a filtered subset.

- **parse_command**(command: str)-> RemoteCommand

  Parses and validates a command string into a _RemoteCommand_ object.
  It raises `voluptuous.Invalid` exception if there is any parsing problem.

## Example Protocol Definition

Encoded protocols are easily defined using an intuitive declarative syntax in the definitions yaml file, which is then used to both encode and decode.

```yaml
nec:
  desc: NEC IR code (in LSB form)
  type: IR
  args:
    - name: address
      max: 16bits
      desc: Address to send
      print: 04X
    - name: command
      max: 16bits
      desc: NEC command to send
      print: 04X
  timings:
    frequency: 38000
    unit: 1
    one: [560, -1690]
    zero: [560, -560]
    header: [9000, -4500]
    footer: [560]

  pattern: header {address LSB 16} {command LSB 16} footer
```

# Acknowledgments

Thanks to all of the following sites and projects from where I obtained information about different codec definitions:

- [ESPHome](https://github.com/esphome/esphome/tree/2022.3.0/esphome/components/remote_base)
- [IRremoteESP8266](https://crankyoldgit.github.io/IRremoteESP8266/)
- [IRMP](https://github.com/ukw100/IRMP)
- [MakeHex](https://github.com/probonopd/MakeHex)
- [IrScrutinizer](https://github.com/bengtmartensson/IrScrutinizer)
- [python-miio](https://github.com/rytilahti/python-miio/blob/master/miio/chuangmi_ir.py) for Xiaomi miio raw format
- [python-broadlink](https://github.com/mjg59/python-broadlink/blob/master/protocol.md) for Broadlink raw format
- [harctoolbox](http://www.harctoolbox.org/Glossary.html#ProntoSemantics) for Pronto
