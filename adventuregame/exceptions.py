#!/usr/bin/python3


__name__ = "adventuregame.exceptions"

class Internal_Exception(Exception):
    pass


class Bad_Command_Exception(Exception):
    __slots__ = 'command', 'message'

    def __init__(self, command_str, message_str):
        self.command = command_str
        self.message = message_str
