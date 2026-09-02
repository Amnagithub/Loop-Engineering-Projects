"""Project 6 — Doorbell (event-driven): dispatcher module.

Doorbell presses arrive as a queue of events; every event must be delivered, in
order, to the handler.

NOTE: this copy on `main` is CORRECT and its tests pass. The planted-bug version
of this module lives on the demo branch `doorbell/planted-bug` (a loop over
`events[:-1]` that drops the last event). Opening that branch as a PR rings the
Doorbell, whose automatic review should flag the bug.
"""


def handle_all(events, handler):
    """Call handler(event) for every event in `events`, oldest first.

    Returns the number of events that were actually delivered to `handler`.
    """
    handled = 0
    for event in events:
        handler(event)
        handled += 1
    return handled
