"""Project 4 - buggy module.

Contains two intentional bugs. The tests in test_buggy.py currently fail;
fix the code so all tests pass, then stop.
"""


def calculate_total(price, quantity):
    # FIXED: returns price * quantity
    return price * quantity


def countdown(n):
    # FIXED: includes 0 — range(n, -1, -1)
    return list(range(n, -1, -1))
