import re
from typing import IO, Any, Callable, MutableMapping

from .caseless_dict import CaselessDict
from .exceptions import IncompleteMultilineError, SectionlessKeyError, SyntaxError
from .typedefs import commentsType, keyProcessor, sectionProcessor, sectionsType

_MATCH_SECTION = re.compile(r"^\[(.+)\]$")
_MATCH_COMMENT = re.compile(r"^[#;]")
_MATCH_KEY_VALUE = re.compile(r"^(?P<key>[\w\-]+)\s*=\s*(?P<value>.*)")


def _assign_existing(dict_: MutableMapping[str, Any], k: str, v: Any, concat=False):
    if not v:
        # empty value resets
        dict_[k] = ""
        return

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
    dict_: MutableMapping[str, Any],
    k: str,
    v: Any,
    processor: Callable | None = None,
    concat: bool = False,
):
    if processor:
        v = processor(v)

    if k in dict_:
        _assign_existing(dict_, k, v, concat)
    else:
        dict_[k] = v


def parse(
    fp: IO,
    section_processors: dict[str, sectionProcessor] = {},
    key_processors: dict[str, keyProcessor] = {},
    preserve_comments: bool = False,
) -> tuple[sectionsType, commentsType]:
    """Systemd file parser.

    Parses Systemd unit files into python `dict`.

    :param fp IO: any file type object
    :param section_processors dict: dictionary of `section_name -> lambda content: ...`, useful for
        force-converting certain sections into `list`s, `section_name` matching is caseless.
    :param key_processors dict: dictionary of `key_name -> lambda value: ...`. useful for enforcing
      value types or validation;
      `key_name` may be a `section_name.key_name` for specific key targeting, or a `key_name` for
      global key targeting, `section_name.key_name` has higher priority; matching is caseless.
    :param preserve_comments bool: whether to collect comments and return them as the second
      member of return value.
    :return: tuple[sectionsType, commentsType]
    :raises SyntaxError: if line doesn't match expected syntax
    :raises SectionlessKeyError: if a key definition appears before any section
    :raises IncompleteMultilineError: if a multiline value wasn't finished
    """
    structure: sectionsType = CaselessDict()
    comments: commentsType = {}

    current_section = ""
    section_content = CaselessDict()
    is_reading_multiline = False
    current_key = ""
    current_comments: list[str] = []
    kp = CaselessDict(key_processors)
    sp = CaselessDict(section_processors)

    for ln, line in enumerate(fp):
        line = line.strip()

        if _MATCH_COMMENT.match(line):
            if preserve_comments:
                current_comments.append(line)
            continue

        if section := _MATCH_SECTION.match(line):
            if is_reading_multiline:
                raise IncompleteMultilineError(ln)

            section = section.group(1)

            if current_comments:
                comments[(section.casefold(), None)] = current_comments
                current_comments = []

            if current_section and section_content:
                _set_value(
                    structure,
                    current_section,
                    section_content,
                    sp.get(current_section),
                )

            section_content = CaselessDict()
            current_section = section
            continue

        if kv_pair := _MATCH_KEY_VALUE.match(line):
            if is_reading_multiline:
                raise IncompleteMultilineError(ln)
            if not current_section:
                raise SectionlessKeyError(ln)

            key = kv_pair.group("key").strip()

            if current_comments:
                comments[(current_section.casefold(), key.casefold())] = (
                    current_comments
                )
                current_comments = []

            # TODO unquote
            value = kv_pair.group("value").strip()

            is_reading_multiline = value.endswith("\\")
            if is_reading_multiline:
                value = value[:-1]
                current_key = key

            _set_value(
                section_content,
                key,
                value,
                # multiline values must be processed at the end
                None
                if is_reading_multiline
                else (kp.get(f"{current_section}.{key}") or kp.get(key)),
                is_reading_multiline,
            )

            continue

        if is_reading_multiline:
            value = line
            is_reading_multiline = value.endswith("\\")
            if is_reading_multiline:
                value = value[:-1]
            elif current_comments:
                # finished reading multiline value and collected some comments in process:
                # keep them with current key comments
                comments.setdefault(
                    (current_section.casefold(), current_key.casefold()), []
                ).extend(current_comments)
                current_comments = []

            _set_value(
                section_content,
                current_key,
                value,
                # multiline values must be processed at the end
                None
                if is_reading_multiline
                else (
                    kp.get(f"{current_section}.{current_key}") or kp.get(current_key)
                ),
                is_reading_multiline,
            )
            continue

        if line:
            raise SyntaxError(line, ln)

    if is_reading_multiline and (
        processor := (kp.get(f"{current_section}.{current_key}") or kp.get(current_key))
    ):
        # apply processor if multiline value was unfinished
        section_content[current_key] = processor(section_content[current_key])

    if current_section and section_content:
        _set_value(
            structure,
            current_section,
            section_content,
            sp.get(current_section),
        )

    if current_comments:
        comments[(None, None)] = current_comments

    return structure, comments
