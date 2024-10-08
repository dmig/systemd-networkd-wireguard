from typing import Any, Callable, Mapping, TypeAlias

kvType: TypeAlias = Mapping[str, Any]
sectionContent: TypeAlias = kvType | list[kvType]
sectionType: TypeAlias = Mapping[str, sectionContent]
sectionProcessor: TypeAlias = Callable[[sectionContent], sectionContent]
keyProcessor: TypeAlias = Callable[[Any], Any]
