from typing import Any, Callable, Mapping, TypeAlias

kvType: TypeAlias = Mapping[str, Any]
sectionContent: TypeAlias = kvType | list[kvType]
sectionsType: TypeAlias = Mapping[str, sectionContent]
sectionProcessor: TypeAlias = Callable[[sectionContent], sectionContent]
keyProcessor: TypeAlias = Callable[[Any], Any]
commentList: TypeAlias = list[str]
eofKey: TypeAlias = tuple[None, None]
lineKey: TypeAlias = tuple[str, str]
sectionKey: TypeAlias = tuple[str, None]
commentsType: TypeAlias = Mapping[sectionKey | lineKey | eofKey, commentList]
