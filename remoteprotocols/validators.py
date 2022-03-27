"""General validator utilities"""

from __future__ import annotations

import re
from typing import Any, Callable, List, Union, cast

import voluptuous as vol  # type: ignore

# Validation Helpers

BITS_VALUES = {
    "8bits": 0xFF,
    "16bits": 0xFFFF,
    "24bits": 0xFFFFFF,
    "32bits": 0xFFFFFFFF,
    "40bits": 0xFFFFFFFFFF,
    "48bits": 0xFFFFFFFFFFFF,
    "56bits": 0xFFFFFFFFFFFFFF,
    "64bits": 0xFFFFFFFFFFFFFFFF,
}


def remove_quotes(value: Any) -> Any:
    """If the value is a string with leading quotes, extracts and returns the inner value.
    In any other case returns the value unchanged"""
    if isinstance(value, str):
        # remove quotes
        re_quote = re.compile(r"^\s*([\"\'])((?:(?!\1).|\\\1)*)(?<!\\)\1\s*$")
        # remove border quotes
        match = re.search(re_quote, value)
        if match:
            value = match[2]
    return value


def coerce_string(value: Any) -> str:
    """Coerce primitive value to string.
    If it is a string with leading quotes, remove them"""
    if isinstance(value, (dict, list)):
        raise vol.Invalid("string value cannot be dictionary or list.")
    if isinstance(value, bool):
        raise vol.Invalid(
            "Auto-converted this value to boolean, please wrap the value in quotes."
        )
    if isinstance(value, str):
        return cast(str, remove_quotes(value))
    if value is not None:
        return str(value)
    raise vol.Invalid("string value is None")


def string_strict(value: str) -> str:
    """Check that value es."""
    if isinstance(value, str):
        return cast(str, remove_quotes(value))
    raise vol.Invalid(
        f"Must be string, got {value}. did you forget putting quotes around the value?"
    )


def integer(value: Any) -> int:
    """Validate that the config option is an integer.

    Automatically also converts strings to ints, it understands bits mnemonics.
    """
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if int(value) == value:
            return int(value)
        raise vol.Invalid(
            f"This option only accepts integers with no fractional part. Please remove the fractional part from {value}"
        )
    if isinstance(value, bool):
        return int(value)

    if value in BITS_VALUES:
        return BITS_VALUES[value]

    value = string_strict(value).lower()
    base = 10
    if value.startswith("0x"):
        base = 16
    elif value.startswith("0b"):
        base = 2

    try:
        return int(value, base)
    except ValueError:
        # pylint: disable=raise-missing-from
        raise vol.Invalid(f"Expected integer, but cannot parse {value} as an integer")


def valid(value: Any) -> Any:
    """A validator that is always valid and returns the value as-is."""
    return value


def unique_field_value(field: str) -> Callable[[Any], Any]:
    """Generates a validator to check that objects in a list have a unique value in the
    provided field"""

    def validator(value: Any) -> Any:
        if not isinstance(value, list):
            raise vol.Invalid("Expected a list")
        vol.Schema(vol.Unique())([a[field] for a in value])

        return value

    return validator


def coerce_list(separator: Union[str, None] = None) -> Callable[[Any], list[Any]]:
    """Converts value to list. Primitives are returned as a one element list.
    None is converted to an empty list.
    Unquoted strings will be split by separator (respecting quoting semantics)
    and the values returned as list elements
    """

    def validator(value: Any) -> list[Any]:
        if isinstance(value, list):
            return value

        if value is None:
            return []

        if isinstance(value, str):
            if separator is not None:
                return quoted_split(value, separator)

        return [value]

    return validator


def valid_name(value: str) -> str:
    """Check it is a strict string with valid characters for a name.
    It cannot start with a number.
    """
    return cast(
        str,
        vol.All(
            string_strict,
            vol.Match(
                r"^[a-z][a-z0-9_]*$",
                msg="Invalid characters for an identifier name",
            ),
        )(value),
    )


def kebab_to_pascal(value: str) -> str:
    """Converts a string from kebab_case to PascalCase"""

    value = string_strict(value)

    value = "".join([w.title() for w in value.split("_")])
    return value


def alternating_signs(value: list[Union[str, int]]) -> list[Union[str, int]]:
    """Validates that a list has all alternating positive and negatives elements, skiping argument references"""
    assert isinstance(value, list)
    for i in range(1, len(value)):

        if isinstance(value[i], str) or isinstance(value[i - 1], str):
            continue
        if value[i] * value[i - 1] > 0:  # type: ignore
            raise vol.Invalid(
                f"Values must alternate between being positive and negative, please see index {i-1} and {i}",
                [i],
            )
    return value


def binary_string(value: Any) -> str:
    """Validates that value is a valid binary digit"""

    val = coerce_string(value)

    for char in val:
        if char not in ("0", "1"):
            raise vol.Invalid(f"String must be all binary digits, but got '{char}'")

    return val


def hex_string(value: Any) -> int:
    """Validates that value is a valid hexadecimal digit and converts it to number"""

    val = coerce_string(value)

    re_hex = re.compile(r"^[0-9a-fA-F]+$")
    if not re_hex.match(val):
        raise vol.Invalid("String must be all hexadecimal digits")

    return int(val, 16)


def quoted_split(text: str, delimiter: str) -> List[str]:
    """Splits a string by 'delimiter', ignoring it if it is inside quotations
    Returns a list of strings with results.
    Consecutive delimiters are returned as empty string
    """

    args = []
    # gets first part
    re_first = re.compile(
        r"^(?:\s*([\"\'])(?:(?!\1).|\\\1)*(?<!\\)\1\s*|[^" + delimiter + r"]?)+"
    )

    while len(text):
        match = re.search(re_first, text)

        if not match:
            break
        text = text[match.end(0) + 1 :]

        # remove spaces
        arg = match[0].strip()

        args.append(arg)

    return args


value_or_arg = vol.Any(integer, valid_name)
