"""Test for object identity."""

from typing import Any, Iterable


def assert_same(object_1: Any, object_2: Any,
                done: set[tuple[int, int]] | None = None) -> None:
    """
    Assert that two objects are equal.

    :param object_1: the first object
    :param object_2: the second object
    """
    if object_1 is object_2:
        return

    assert object_1.__class__ is object_2.__class__
    assert object_1 == object_2

    if done is None:
        done = set()
        id_o1 = id(object_1)
        id_o2 = id(object_2)
        done.add((id_o1, id_o2))
        done.add((id_o2, id_o1))

    if isinstance(object_1, Iterable):
        lst_1 = list(object_1)
        lst_2 = list(object_2)
        ll = list.__len__(lst_1)
        assert ll == list.__len__(lst_2)
        for i in range(ll):
            l1 = lst_1[i]
            l2 = lst_2[i]
            if (id(l1), id(l2)) in done:
                continue
            assert_same(l1, l2, done)

    attrs = set(dir(object_1))
    attrs.update(dir(object_2))
    for attr in sorted(attrs):
        if attr.startswith("_"):
            continue
        av_1 = getattr(object_1, attr)
        av_2 = getattr(object_2, attr)
        c_av_1 = callable(av_1)
        c_av_2 = callable(av_2)
        assert c_av_1 is c_av_2
        if c_av_1:
            continue
        assert av_1 == av_2
        if av_1 is av_2:
            continue
        if (av_1 is object_1) or (av_1 is object_2) or (
                av_2 is object_1) or (av_2 is object_2):
            continue
        if (id(av_1), id(av_2)) in done:
            continue
        assert_same(av_1, av_2, done)
