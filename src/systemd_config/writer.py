from typing import IO

from .typedefs import commentsType, sectionsType


def dump(fp: IO, structure: sectionsType, comments: commentsType | None = None) -> int:
    """Simple Systemd file writer.

    Writes provided `structure` as Systemd config file.

    :param fp IO: any file type object
    :param structure sectionType: 2-level `dict` with `list`s of values when multiple sections or
        keys needed
    :param comments commentsType: optional comments to be written before each section and line
    :returns int: number of characters written
    """
    if not comments:
        comments = {}
    chars_written = 0
    for section, sections_content in structure.items():
        sections_content = (
            sections_content
            if isinstance(sections_content, list)
            else [sections_content]
        )
        for content in sections_content:
            # write section comments
            for comment in comments.get((section.casefold(), None), []):
                chars_written += fp.write(comment + "\n")

            chars_written += fp.write(f"[{section}]\n")
            for key, value in content.items():
                # write key comments
                for comment in comments.get((section.casefold(), key.casefold()), []):
                    chars_written += fp.write(comment + "\n")

                value = value if isinstance(value, list) else [value]
                for v in value:
                    # TODO split long lines
                    # TODO escape if needed
                    chars_written += fp.write(f"{key} = {v}\n")
            chars_written += fp.write("\n")
    # write EOF comments
    for comment in comments.get((None, None), []):
        chars_written += fp.write(comment + "\n")

    return chars_written
