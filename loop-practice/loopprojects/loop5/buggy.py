"""Project 5 - buggy module.

Contains two intentional bugs. The tests in test_buggy.py currently fail;
fix the code so all tests pass, then stop.
"""


def attempts_remaining(max_attempts, used):
    return max_attempts - used


def pass_rate(passed, total):
    return passed / total * 100
