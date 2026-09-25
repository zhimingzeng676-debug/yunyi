import pytest

from window import is_ready


@pytest.mark.parametrize(
    ("samples", "expected"),
    [
        ([], False),
        ([True], False),
        ([True, True], False),
        ([True, True, True], True),
        ([True, True, True, True], True),
        ([False, False, False], False),
    ],
)
def test_default_threshold_boundary(samples, expected):
    assert is_ready(samples) is expected


@pytest.mark.parametrize(
    ("samples", "expected"),
    [
        ([True, True, True, False], False),
        ([True, True, False, True], False),
        ([True, True, True, False, True, True], False),
        ([True, True, True, False, True, True, True], True),
        ([False, True, True, True], True),
    ],
)
def test_failure_resets_trailing_success_count(samples, expected):
    assert is_ready(samples) is expected


@pytest.mark.parametrize(
    ("samples", "threshold", "expected"),
    [
        ([], 1, False),
        ([True], 1, True),
        ([True, False], 1, False),
        ([False, True], 1, True),
        ([True], 2, False),
        ([False, True, True], 2, True),
        ([True, False, True], 2, False),
        ([True, True, True], 4, False),
        ([True, True, True, True], 4, True),
        ([False, True, True, True, True, True], 4, True),
    ],
)
def test_custom_threshold(samples, threshold, expected):
    assert is_ready(samples, threshold) is expected


@pytest.mark.parametrize("threshold", [0, -1, -10])
@pytest.mark.parametrize("samples", [[], [False], [True, True, True]])
def test_nonpositive_threshold_is_rejected(samples, threshold):
    with pytest.raises(ValueError):
        is_ready(samples, threshold)
