"""Project 4 - buggy module.

Contains two intentional bugs. The tests in test_buggy.py currently fail;
fix the code so all tests pass, then stop.
"""


def calculate_total(price, quantity):
    # BUG: adds price + quantity instead of multiplying
    return price + quantity


def countdown(n):
    # BUG: off-by-one — range stops at 1, so 0 is missing
    return list(range(n, 0, -1))
