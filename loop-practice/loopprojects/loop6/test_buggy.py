"""Project 6 tests — the doorbell dispatcher must deliver every event.

Run with the canonical interpreter:  C:/Python314/python.exe test_buggy.py
"""

from buggy import handle_all


def test_handle_all_delivers_every_event():
    delivered = []
    count = handle_all(["front_door", "back_door", "gate"], delivered.append)
    assert delivered == ["front_door", "back_door", "gate"]
    assert count == 3


def test_handle_all_with_no_events():
    delivered = []
    count = handle_all([], delivered.append)
    assert delivered == []
    assert count == 0


if __name__ == "__main__":
    test_handle_all_delivers_every_event()
    test_handle_all_with_no_events()
    print("All tests passed!")
