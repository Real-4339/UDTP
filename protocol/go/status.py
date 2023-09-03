from enum import Enum


class Status(Enum):
    FINISHED = 0
    RUNNING = 1
    SLEEPING = 2
    DEAD = 3
    ALIVE = 4