from typing import IO

from .typedefs import sectionType



def dump(fp: IO, structure: sectionType) -> int:
    """Simple Systemd file writer.

    Writes provided `structure` as Systemd config file.

    :param fp IO: any file type object
    :param structure sectionType: 2-level `dict` with `list`s of values when multiple sections or
        keys needed
    :returns int: number of characters written
    """
    chars_written = 0
    for section, sections_content in structure.items():
        sections_content = (
            sections_content
            if isinstance(sections_content, list)
            else [sections_content]
        )
        for content in sections_content:
            chars_written += fp.write(f"[{section}]\n")
            for key, value in content.items():
                value = value if isinstance(value, list) else [value]
                for v in value:
                    # TODO split long lines
                    # TODO escape if needed
                    chars_written += fp.write(f'{key} = {v}\n')
            chars_written += fp.write("\n")

    return chars_written
