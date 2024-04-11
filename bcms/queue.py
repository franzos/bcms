"""Module tracks async requests like pair and unpair"""

from dataclasses import dataclass


@dataclass
class AsyncQueueItem:
    """Class to represent an async request item"""

    command: str
    args: dict


class AsyncQueue:
    """Class to manage async requests like pair and unpair"""

    def __init__(self):
        self.queue = []

    def add(self, command, args):
        """Add an async request to the queue"""
        self.queue.append(AsyncQueueItem(command, args))

    def from_class(self, item):
        """Add an async request to the queue from a class instance"""
        self.queue.append(item)

    def get(self) -> AsyncQueueItem:
        """Get the next async request from the queue"""
        return self.queue.pop(0)

    def is_empty(self):
        """Check if the queue is empty"""
        return len(self.queue) == 0

    def __len__(self):
        """Get the length of the queue"""
        return len(self.queue)

    def __str__(self):
        """Get a string representation of the queue"""
        return str(self.queue)


def make_pair_request(address):
    """Create a pair request item"""
    return AsyncQueueItem("pair", {"address": address})


def make_unpair_request(address):
    """Create an unpair request item"""
    return AsyncQueueItem("unpair", {"address": address})
