'''
tree.py
'''

import collections
import itertools


def get(tree, key):
    subtree = tree
    for name in key:
        subtree = subtree[name]
    return subtree


def set(tree, key, value):
    subtree = tree
    *key, base = key
    for name in key:
        if not name in subtree:
            subtree[name] = {}
        subtree = subtree[name]
    subtree[base] = value


def schema(tree, _schema=None):
    if _schema is None:
        _schema = {}
    if isinstance(tree, dict):
        for k, v in tree.items():
            if isinstance(v, list):
                _schema[k] = [{}]
                schema(v, _schema[k][0])
            else:
                _schema[k] = {}
                schema(v, _schema[k])

    elif isinstance(tree, list):
        for v in tree:
            schema(v, _schema)
    else:
        return
    return _schema


def keys(tree, _parent=None):
    if isinstance(tree, dict):
        for k, v in tree.items():
            if _parent:
                p = _parent + (k,)
            else:
                p = (k,)
            yield p
            yield from keys(v, p)
    elif isinstance(tree, list):
        for n, v in enumerate(tree):
            if _parent:
                p = _parent + (n,)
            else:
                p = (n,)
            yield p
            yield from keys(v, p)


def values(tree):
    for key in keys(tree):
        yield get(tree, key)


def items(tree):
    for key in keys(tree):
        yield key, get(tree, key)


def paths(schema, _parent=None):
    if isinstance(schema, dict):
        for k, v in schema.items():
            if _parent:
                p = _parent + (k,)
            else:
                p = (k,)
            yield p
            yield from paths(v, p)
    elif isinstance(schema, list):
        for v in schema:
            if _parent:
                p = _parent + (Ellipsis,)
            else:
                p = (Ellipsis,)
            yield p
            yield from paths(v, p)


def search(tree, name):
    for path in paths(tree):
        if path[-1] == name:
            return path


def find(tree, name):
    for path in paths(tree):
        if path[-1] == name:
            yield path


def expandpath(schema, path):
    path = list(path)

    n = 0
    while n < len(path):
        if isinstance(schema, list):
            if path[n] != Ellipsis:
                path.insert(n, Ellipsis)
            schema = schema[0]
        else:
            schema = schema[path[n]]
        n += 1

    return tuple(path)


def matchkey(expanded, key):
    if not len(expanded) == len(key):
        return False

    for p, k in zip(expanded, key):
        if isinstance(k, int) and p == Ellipsis:
            continue
        if k != p:
            return False

    return True


def pathkeys(tree, expanded):

    for key in keys(tree):
        if matchkey(expanded, key):
            yield key


def walk(tree, expanded):

    for key in pathkeys(tree, expanded):
        yield get(tree, key)

def flatten(tree, key):
    result = {}

    for n, k in enumerate(key):
        if isinstance(k, int):
            continue
        result[k] = get(tree, key[:n+1])

    return result


def branches(tree, expanded):

    for key in pathkeys(tree, expanded):
        yield flatten(tree, key)


class TreeDict:

    def __init__(self, d):
        self._tree = d
        self._schema = schema(self._tree)
        self._paths = list(paths(self._schema))
        self._keys = list(keys(self._tree))

    def __str__(self):
        return str(self._tree)

    def __repr__(self):
        return 'TreeDict({!r})'.format(self._tree)

    def ispath(self, path):
        return path in self._paths

    def iskey(self, key):
        return key in self._keys

    def canonicalise(self, path):
        return expandpath(self._schema, path)

    def get(self, key):
        return get(self._tree, key)

    def keys(self):
        for key in self._keys:
            yield key

    def values(self):
        for key in self._keys:
            yield get(self._tree, key)

    def items(self):
        for key in self._keys:
            yield key, get(self._tree, key)

    def paths(self):
        for path in self._paths:
            yield path

    def schema(self):
        return self._schema


class Tree:

    def __init__(self, json_dict):
        self.__tree__ = TreeDict(json_dict)
        self.__path__ = tuple()

    def __str__(self):
        return 'Tree({})'.format(self.__tree__)

    def __repr__(self):
        if self.__path__:
            return 'Tree({}).{}'.format(
                self.__tree__, '.'.join(self.__path__))
        else:
            return 'Tree({})'.format(self.__tree__)

    def __iter__(self):
        yield from self.__tree__.get(self.__path__)

    @classmethod
    def __getter__(cls, tree, path):
        new = cls.__new__(cls)
        new.__tree__ = tree
        new.__path__ = path
        return new

    def __getattr__(self, name):
        path = self.__path__ + (name,)
        if self.__tree__.ispath(path):
            return self.__getter__(self.__tree__, path)
        else:
            raise AttributeError(
                'Tree: {} has no element {}'.format('.'.join(path[:-1]), name))
