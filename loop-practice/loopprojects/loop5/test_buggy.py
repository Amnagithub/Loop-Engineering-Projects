"""Project 5 tests - verify the buggy functions work correctly."""

from buggy import attempts_remaining, pass_rate


def test_attempts_remaining():
    assert attempts_remaining(6, 2) == 4


def test_pass_rate():
    assert pass_rate(3, 4) == 75.0


if __name__ == "__main__":
    test_attempts_remaining()
    test_pass_rate()
    print("All tests passed!")
