from dataclasses import dataclass


@dataclass
class AsyncQueueItem:
    command: str
    args: dict


class AsyncQueue:
    def __init__(self):
        self.queue = []

    def add(self, command, args):
        self.queue.append(AsyncQueueItem(command, args))

    def from_class(self, item):
        self.queue.append(item)

    def get(self) -> AsyncQueueItem:
        return self.queue.pop(0)

    def is_empty(self):
        return len(self.queue) == 0

    def __len__(self):
        return len(self.queue)

    def __str__(self):
        return str(self.queue)


def make_pair_request(address):
    return AsyncQueueItem("pair", {"address": address})


def make_unpair_request(address):
    return AsyncQueueItem("unpair", {"address": address})
