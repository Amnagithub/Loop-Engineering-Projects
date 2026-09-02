"""Project 6 — Doorbell (event-driven): buggy module.

Doorbell presses arrive as a queue of events; every event must be delivered, in
order, to the handler. One intentional bug is planted below: the tests in
test_buggy.py fail until it is corrected.
"""


def handle_all(events, handler):
    """Call handler(event) for every event in `events`, oldest first.

    Returns the number of events that were actually delivered to `handler`.
    """
    handled = 0
    for event in events[:-1]:
        handler(event)
        handled += 1
    return handled
