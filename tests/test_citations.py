from docqa.generation.citations import resolve_citations


def test_valid_citations():
    assert resolve_citations("Foo [1] bar [2].", [1, 2], 5) == ([1, 2], [])


def test_invalid_id_is_flagged():
    valid, invalid = resolve_citations("Foo [9].", [9], 5)
    assert valid == [] and invalid == [9]


def test_inline_marker_not_in_list_is_still_counted():
    assert resolve_citations("Foo [3].", [], 5) == ([3], [])


def test_listed_but_not_inline_is_counted():
    assert resolve_citations("Foo.", [2], 5) == ([2], [])


def test_zero_is_invalid():
    assert resolve_citations("x [0]", [0], 5) == ([], [0])
