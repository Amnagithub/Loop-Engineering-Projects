"""Project 4 tests - verify the buggy functions work correctly."""

from buggy import calculate_total, countdown


def test_calculate_total():
    assert calculate_total(5, 3) == 15


def test_countdown():
    assert countdown(3) == [3, 2, 1, 0]


if __name__ == "__main__":
    test_calculate_total()
    test_countdown()
    print("All tests passed!")
