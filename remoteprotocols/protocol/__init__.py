""" Handle protocol definitions and validations
"""
# flake8: noqa
from typing import Any

from . import schema1
from .definition import ArgDef, PatternDef, ProtocolDef, TimingsDef, ValueOrArg


def validate_protocols(definition: dict[(str, Any)]) -> dict[(str, ProtocolDef)]:
    """Validates a dict of protocols definitions and converts them into ProtocolDef objects"""
    return schema1.PROTOCOLS_DEF_SCHEMA(definition)  # type: ignore
