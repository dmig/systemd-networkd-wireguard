from typing import Any, Callable, TypeAlias

from .caseless_dict import CaselessDict

kvType: TypeAlias = CaselessDict[str, Any]
sectionContent: TypeAlias = kvType | list[kvType]
sectionType: TypeAlias = CaselessDict[str, sectionContent]
sectionProcessor: TypeAlias = Callable[[sectionContent], sectionContent]
keyProcessor: TypeAlias = Callable[[Any], Any]
