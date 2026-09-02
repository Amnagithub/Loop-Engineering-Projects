"""Project 2 tests - verify the calculator functions work correctly."""

from calculator import add, subtract, multiply


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(10, 4) == 6


def test_multiply():
    assert multiply(3, 4) == 12


if __name__ == "__main__":
    test_add()
    test_subtract()
    test_multiply()
    print("All tests passed!")
