#!/usr/bin/python3


from advgame.statemsgs.gsm import GameStateMessage


__all__ = ("InvalidPartGSM", "NameSetGSM")


class InvalidPartGSM(GameStateMessage):
    """
    Returned by set_name_command() when the player tries to set a name that
    is not one or more alphabetic titelcased strings.
    """

    __slots__ = ("name_part",)

    @property
    def message(self):
        return (
            f"The name {self.name_part} is invalid; must be a capital letter "
            + "followed by lowercase letters."
        )

    def __init__(self, name_part):
        self.name_part = name_part


class NameSetGSM(GameStateMessage):
    """
    Returned by set_name_command() when the player sets a name.
    """

    __slots__ = ("name",)

    @property
    def message(self):
        return f"Your name, '{self.name}', has been set."

    def __init__(self, name):
        self.name = name
