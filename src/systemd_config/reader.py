import re
from typing import IO, Any, Callable

from .caseless_dict import CaselessDict
from .exceptions import IncompleteMultilineError, SectionlessKeyError
from .typedefs import keyProcessor, sectionProcessor, sectionType

_MATCH_SECTION = re.compile(r"^\[(.+)\]$")
_MATCH_COMMENT = re.compile(r"^[#;]")
_MATCH_KEY_VALUE = re.compile(r"^(?P<key>[\w\-]+)\s*=\s*(?P<value>.*)")


def _assign_existing(dict_: CaselessDict[str, Any], k: str, v: Any, concat=False):
    if concat and isinstance(v, str) and isinstance(dict_[k], str):
        dict_[k] += v
        return

    if not isinstance(dict_[k], list):
        dict_[k] = [dict_[k]]
    if isinstance(v, list):
        dict_[k].extend(v)
    else:
        dict_[k].append(v)


def _set_value(
    dict_: CaselessDict[str, Any],
    k: str,
    v: Any,
    processor: Callable | None = None,
    concat: bool = False,
):
    if processor:
        v = processor(v)

    # TODO empty value resets
    if k in dict_:
        _assign_existing(dict_, k, v, concat)
    else:
        dict_[k] = v


def parse(
    fp: IO,
    section_processors: dict[str, sectionProcessor] = {},
    key_processors: dict[str, keyProcessor] = {},
) -> sectionType:
    """Systemd file parser.

    Parses Systemd unit files into python `dict`.

    :param fp IO: any file type object
    :param section_processors dict: dictionary of `section_name -> lambda content: ...`, useful for
        force-converting certain sections into `list`s, `section_name` matching is caseless.
    :param key_processors dict: dictionary of `key_name -> lambda value: ...`. useful for enforcing
      value types or validation;
      `key_name` may be a `section_name.key_name` for specific key targeting, or a `key_name` for
      global key targeting, `section_name.key_name` has higher priority; matching is caseless.
    :return: sectionType
    :raises SyntaxError: if line doesn't match expected syntax
    :raises SectionlessKeyError: if a key definition appears before any section
    :raises IncompleteMultilineError: if a multiline value wasn't finished

    More information on Systemd file syntax here:
    https://www.freedesktop.org/software/systemd/man/256/systemd.syntax.html.

    Features:
    - beginning and trailing whitespace is ignored
    - inline comments are not supported (as systemd syntax defines)
    - comments inside multiline values are supported (as systemd syntax defines)
    - multiline values are concatenated into a single string (excluding comments)
    - duplicate sections become a `list` of sections contents under a single key
    - duplicate keys become a `list` of values under a single key
    - section and key comparison is
      [caseless](https://docs.python.org/3/library/stdtypes.html#str.casefold), but preserving case;
      first occurence met in file will be used as a key

    Example:
    ```
        with open("wireguard.netdev") as fp:
            config = parse(
                fp,
                # force-convert WireguardPeer section to list
                {"Wireguardpeer": lambda v: v if isinstance(v, list) else [v]},
                # split AllowedIPs by ','
                {"allowedips": lambda v: v if isinstance(v, list) else list(filter(None, v.split(','))),
                # convert ListenPort to `int`
                'listenport': int},
            )
    ```
    """
    structure: sectionType = CaselessDict()

    current_section = ""
    section_content = CaselessDict()
    is_multiline = False
    current_key = ""
    kp = CaselessDict(key_processors)
    sp = CaselessDict(section_processors)

    for ln, line in enumerate(fp):
        line = line.strip()

        if _MATCH_COMMENT.match(line):
            continue

        if section := _MATCH_SECTION.match(line):
            if is_multiline:
                raise IncompleteMultilineError(ln)

            if current_section and section_content:
                _set_value(
                    structure,
                    current_section,
                    section_content,
                    sp.get(current_section),
                )

            section_content = CaselessDict()
            current_section = section.group(1)
            continue

        if kv_pair := _MATCH_KEY_VALUE.match(line):
            if is_multiline:
                raise IncompleteMultilineError(ln)
            if not current_section:
                raise SectionlessKeyError(ln)

            key = kv_pair.group("key").strip()
            # TODO unquote
            value = kv_pair.group("value").strip()

            is_multiline = value.endswith("\\")
            if is_multiline:
                value = value[:-1]
                current_key = key

            _set_value(
                section_content,
                key,
                value,
                # multiline values must be processed at the end
                None
                if is_multiline
                else (kp.get(f"{current_section}.{key}") or kp.get(key)),
                is_multiline,
            )

            continue

        if is_multiline:
            value = line
            is_multiline = value.endswith("\\")
            if is_multiline:
                value = value[:-1]

            _set_value(
                section_content,
                current_key,
                value,
                # multiline values must be processed at the end
                None
                if is_multiline
                else (
                    kp.get(f"{current_section}.{current_key}") or kp.get(current_key)
                ),
                is_multiline,
            )
            continue

        if line:
            raise SyntaxError(line, ln)

    if is_multiline and (
        processor := (kp.get(f"{current_section}.{current_key}") or kp.get(current_key))
    ):
        # apply processor if multiline value is unfinished
        section_content[current_key] = processor(section_content[current_key])

    if current_section and section_content:
        _set_value(
            structure,
            current_section,
            section_content,
            sp.get(current_section),
        )
    return structure
