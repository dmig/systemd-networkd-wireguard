from typing import Generic, Mapping, MutableMapping, TypeVar

KT = TypeVar("KT")
VT = TypeVar("VT")


class CaselessDict(MutableMapping, Generic[KT, VT]):
    """A caseless ``dict``-like object.
    Based on [implementation](https://github.com/kennethreitz/requests/blob/master/src/requests/structures.py#L13)
    in the Requests library.

    Implements all methods and operations of ``MutableMapping`` as well as dict's ``copy``.

    All keys are expected to be strings. The structure remembers the case of the last key to be set,
    and ``iter(instance)``, ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()`` will
    contain case-sensitive keys.
    However, querying and contains testing is case insensitive::

        cid = CaselessDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the value of a ``'Content-Encoding'``
    response header, regardless of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison operations are given keys that have
    equal ``.lower()``s, the behavior is undefined.
    """

    def __init__(self, data: Mapping | None = None, **kwargs):
        self._store = dict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the casefolded key for lookups, but store the actual
        # key alongside the value.
        self._store[key.casefold()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.casefold()][1]

    def __delitem__(self, key):
        del self._store[key.casefold()]

    def __iter__(self):
        return (casedkey for casedkey, _ in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())

    def __eq__(self, other):
        if isinstance(other, Mapping):
            other = self.__class__(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return self.__class__(self._store.values())  # type: ignore

    def __repr__(self):
        return str(dict(self.items()))
