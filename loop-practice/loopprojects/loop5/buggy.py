"""Project 5 - buggy module.

Contains two intentional bugs. The tests in test_buggy.py currently fail;
fix the code so all tests pass, then stop.
"""


def attempts_remaining(max_attempts, used):
    # BUG: off-by-one — returns one more than the attempts actually left
    return max_attempts - used + 1


def pass_rate(passed, total):
    # BUG: returns a bare ratio instead of a percentage
    return passed / total
