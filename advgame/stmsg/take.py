#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage


__all__ = (
    "ItemNotFoundInContainer",
    "ItemOrItemsTaken",
    "AmountToTakeUnclear",
    "TryingToTakeMoreThanIsPresent",
)


class ItemNotFoundInContainer(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.take_command() if the
    player specifies an item to take from a chest that is not in that chest
    or from a corpse that is not on the corpse.
    """

    __slots__ = "container_title", "amount_attempted", "container_type", "item_title"

    @property
    def message(self):
        # This message property assembles a single sentence which
        # conveys that the container mentioned doesn't contain the item
        # sought.
        base_str = f"The {self.container_title} doesn't have"
        indirect_article_or_determiner = (
            "any"
            if self.amount_attempted > 1
            else "an"
            if self.item_title[0] in "aeiou"
            else "a"
        )
        container_clause = "in it" if self.container_type == "chest" else "on them"
        pluralizer = "s" if self.amount_attempted > 1 else ""
        return (
            f"{base_str} {indirect_article_or_determiner} "
            + f"{self.item_title}{pluralizer} {container_clause}."
        )

    def __init__(self, container_title, amount_attempted, container_type, item_title):
        self.container_title = container_title
        self.amount_attempted = amount_attempted
        self.container_type = container_type
        self.item_title = item_title


class ItemOrItemsTaken(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.take_command() when the
    player successfully acquires an item from a chest or corpse.
    """

    __slots__ = "container_title", "item_title", "amount_taken"

    @property
    def message(self):
        # This message property assembles a sentence which conveys that
        # the player character took an amount of an item from a chest or
        # corpse.
        indirect_article_or_quantity = (
            str(self.amount_taken)
            if self.amount_taken > 1
            else "an"
            if self.item_title[0] in "aeiou"
            else "a"
        )
        pluralizer = "s" if self.amount_taken > 1 else ""
        return (
            f"You took {indirect_article_or_quantity} "
            + f"{self.item_title}{pluralizer} from the {self.container_title}."
        )

    def __init__(self, container_title, item_title, amount_taken):
        self.container_title = container_title
        self.item_title = item_title
        self.amount_taken = amount_taken


class AmountToTakeUnclear(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.take_command() when the
    player writes an ungrammatical sentence that is ambiguous as to how many
    of the item the player means to take.
    """

    @property
    def message(self):
        return "Amount to take unclear. How many do you want?"

    def __init__(self):
        pass


class TryingToTakeMoreThanIsPresent(GameStateMessage):
    """
    Returned by advgame.process.CommandProcessor.take_command() when the
    player specifies a quantity of an item to take from a chest that is more
    than is present in that chest, or from a corpse that is more than is
    present on that corpse.
    """

    __slots__ = (
        "container_title",
        "container_type",
        "item_title",
        "amount_attempted",
        "amount_present",
    )

    @property
    def message(self):
        # This message property assembles a sentence conveying that the
        # quantity of the item sought can't be taken from the container
        # because only a smaller quantity is there. The lowest value
        # self.amount_present can be is 1, and self.amount_attempted
        # must be greater than that if this error is being returned, so
        # we know that self.amount_attempted > 1.
        item_specifier = (
            f"suits of {self.item_title}"
            if self.item_type == "armor"
            else f"{self.item_title}s"
        )
        return (
            f"You can't take {self.amount_attempted} {item_specifier} from "
            + f"the {self.container_title}. Only {self.amount_present} is "
            + "there."
        )

    def __init__(
        self,
        container_title,
        container_type,
        item_title,
        item_type,
        amount_attempted,
        amount_present,
    ):
        self.container_title = container_title
        self.container_type = container_type
        self.item_title = item_title
        self.item_type = item_type
        self.amount_attempted = amount_attempted
        self.amount_present = amount_present
