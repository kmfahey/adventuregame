#!/usr/bin/python3

"""
The CommandProcessor class which processes a natural-language command
and executes it in the game object environment, modifying the game state
and generating a natural-language response.
"""

from dataclasses import dataclass

from advgame.commands import (
    attack_command,
    begin_game_command,
    cast_spell_command,
    close_command,
    drink_command,
    drop_command,
    equip_command,
    help_command,
    inventory_command,
    leave_command,
    lock_command,
    look_at_command,
    open_command,
    pick_lock_command,
    pick_up_command,
    put_command,
    quit_command,
    reroll_command,
    set_class_command,
    set_name_command,
    status_command,
    take_command,
    unequip_command,
    unlock_command,
)
from advgame.commands import (
    INGAME_COMMANDS,
    PREGAME_COMMANDS,
)
from advgame.elements import GameState
from advgame.errors import InternalError
from advgame.statemsgs.command import NotRecognizedGSM, NotAllowedNowGSM
from advgame.statemsgs import GameStateMessage


__all__ = ("CommandProcessor",)


@dataclass
class Context:
    game_state: GameState
    game_ending_state_msg: GameStateMessage


# This module consists solely of the CommandProcessor class and its
# supporting data structures. CommandProcessor is a monolithic class
# that has a process() method which accepts a natural language command
# and dispatches it to the appropriate command method. Every command in
# the game corresponds to a method of the CommandProcessor class, and
# each method always returns a tuple of one or more GameStateMessage
# subclass objects. Typically, the bulk of the logic in a given command
# method is devoted to detecting player error and handling each error
# discretely. The logic that completes the command task is often a brief
# coda to a sophisticated conditional handling all the cases where the
# command can't complete.


class CommandProcessor:
    """
    A processor that can parse a natural language command, modify the
    game state appropriately, and return a GameStateMessage object that
    stringifies to a natural language reply.
    """

    __slots__ = "context", "commands_set", "game_state", "game_ending_state_msg"

    # All return values from [a-z_]+_command methods in this class are
    # tuples. Every [a-z_]+_command method returns a tuple of one or
    # more GameStateMessage subclass objects reflecting a change or set
    # of changes in game State.
    #
    # For example, an ATTACK action that doesn't kill the foe will
    # prompt the foe to attack. The foe's attack might lead to the
    # character's death. So the return value might be a `AttackHitGSM`
    # object, a `AttackedAndHitGSM` object, and a `CharacterDeathGSM`
    # object, each bearing a message in its `message` property. The
    # frontend code will iterate through the tuple printing each message
    # in turn.

    def __init__(self, game_state):
        """
        Initialize the CommandProcessor before the beginning of the game.

        :gamestate: A GameState object, which is composited of the game's
        RoomsState, CreaturesState, ContainersState, DoorsState, and ItemsState
        objects. Once the character_name and character_class attributes are set
        on this object, a Character object will be added and the game can begin.
        """
        self.context = dict(game_state=None, game_ending_state_msg=None)

        # This GameState object contains & makes available ItemsState,
        # DoorsState, ContainersState, CreaturesState, and RoomsState
        # objects. It will later furnish a Character object when one
        # can be initialized. These comprise the game data that the
        # player interacts with during the game, and have already been
        # initialized by the frontend script before a CommandProcessor
        # object is instantiated.
        self.game_state = game_state

        # This attribute isn't used until the end of the game. Once
        # the game is over, self.game_state.game_has_ended is set to
        # True, and any further commands just get the GameStateMessage
        # subclass object that indicated end of game. It's saved in this
        # attribute.
        self.game_ending_state_msg = None

        # This introspection associates each method whose name ends with
        # _command with a command whose text (with spaces replaced by
        # underscores) is the beginning of that name.
        self.commands_set = PREGAME_COMMANDS | INGAME_COMMANDS

    @staticmethod
    def pre_process(natural_language_str):
        tokens = natural_language_str.strip().split()
        command = tokens.pop(0).lower()

        # This block of conditionals is a set of preprocessing steps
        # that handle multi-token commands and commands which can be
        # said different ways.

        match command:

            case "begin":
                if (
                    len(tokens) >= 1
                    and tokens[0].lower() == "game"
                    or len(tokens) >= 2
                    and tokens[0].lower() == "the"
                    and tokens[1].lower() == "game"
                ):
                    if tokens[0].lower() == "the":
                        # 'begin the game' becomes 'begin game'.
                        tokens.pop(0)
                    command += "_" + tokens.pop(0).lower()
                elif not len(tokens):
                    command = "begin_game"

            case "cast" if len(tokens) and tokens[0].lower() == "spell":
                # A two-word command.
                command += "_" + tokens.pop(0).lower()

            case "leave" if len(tokens) and tokens[0].lower() in ("using", "via"):
                # 'via' or 'using' is dropped.
                tokens.pop(0)

            case "look" if len(tokens) and tokens[0].lower() == "at":
                # A two-word command.
                command += "_" + tokens.pop(0).lower()

            case "pick" if len(tokens) and (
                tokens[0].lower() == "up" or tokens[0].lower() == "lock"
            ):
                # Either 'pick lock' or 'pick up', a two-word command.
                command += "_" + tokens.pop(0).lower()

            case "quit":
                if (
                    len(tokens) >= 1
                    and tokens[0] == "game"
                    or len(tokens) >= 2
                    and tokens[0:2] == ["the", "game"]
                ):
                    if tokens[0] == "the":
                        # 'quit the game' or 'quit game' becomes 'quit'.
                        tokens.pop(0)
                    tokens.pop(0)

            case "set" if len(tokens) and (
                tokens[0].lower() == "name" or tokens[0].lower() == "class"
            ):
                command += "_" + tokens.pop(0).lower()
                # 'set name to' becomes 'set name'.
                if len(tokens) and tokens[0].lower() == "to":
                    # 'set class to' becomes 'set class'.
                    tokens.pop(0)

            case "show" if len(tokens) and tokens[0].lower() == "inventory":
                # 'show inventory' becomes 'inventory'.
                command = tokens.pop(0).lower()

            case _:
                pass

        return command, tokens

    def process(self, natural_language_str):
        """
        Process and dispatch a natural language command string. The return
        value is always a tuple even when it's length 1. If the command is not
        recognized, returns a NotRecognizedGSM object.

        If a ingame command is used during the pregame (before name and class
        have been set and ability scores have been rolled and accepted)
        or a pregame command is used during the game proper, returns a
        NotAllowedNowGSM object.

        If this method is called after the game has ended, the same object that
        was returned when the game ended is returned again. Otherwise, the
        command is processed and a state message object is returned.

        :natural_language_str: The player's command input as a natural language
        string.
        """
        if self.game_state.game_has_ended:
            return (self.game_ending_state_msg,)

        command, tokens = self.pre_process(natural_language_str)

        if command not in ("set_name", "set_class"):
            # 'set name' and 'set class' are case-sensitive; the rest of
            # the commands are not.
            tokens = tuple(map(str.lower, tokens))

        # With the command normalized, I check for it in the commands
        # set. If it's not present, a NotRecognizedGSM error is
        # returned. The commands allowed in the current game mode are
        # included.
        if command not in self.commands_set:
            return (
                NotRecognizedGSM(
                    command,
                    INGAME_COMMANDS
                    if self.game_state.game_has_begun
                    else PREGAME_COMMANDS,
                    self.game_state.game_has_begun,
                ),
            )

        # If the player used an ingame command during the pregame, or a
        # pregame command during the ingame, a NotAllowedNowGSM error
        # is returned with a list of the currently allowed commands
        # included.
        elif self.game_state.game_has_begun and command not in INGAME_COMMANDS:
            return (
                NotAllowedNowGSM(
                    command, INGAME_COMMANDS, self.game_state.game_has_begun
                ),
            )
        elif not self.game_state.game_has_begun and command not in PREGAME_COMMANDS:
            return (
                NotAllowedNowGSM(
                    command, PREGAME_COMMANDS, self.game_state.game_has_begun
                ),
            )

        return self.dispatch(command, tokens)

    def dispatch(self, command, tokens):
        # Having completed all the checks, I have a valid command and
        # there is a matching command method. The command method is tail
        # called with the remainder of the tokens as an argument.
        context = Context(self.game_state, self.game_ending_state_msg)
        match command:
            case "attack":
                retval = attack_command(context, tokens)
                self.game_ending_state_msg = context.game_ending_state_msg
                return retval
            case "begin_game":
                return begin_game_command(self.game_state, tokens)
            case "cast_spell":
                retval = cast_spell_command(context, tokens)
                self.game_ending_state_msg = context.game_ending_state_msg
                return retval
            case "close":
                return close_command(self.game_state, tokens)
            case "drink":
                return drink_command(self.game_state, tokens)
            case "drop":
                return drop_command(self.game_state, tokens)
            case "equip":
                return equip_command(self.game_state, tokens)
            case "help":
                return help_command(self.game_state, tokens)
            case "inventory":
                return inventory_command(self.game_state, tokens)
            case "leave":
                retval = leave_command(context, tokens)
                self.game_ending_state_msg = context.game_ending_state_msg
                return retval
            case "lock":
                return lock_command(self.game_state, tokens)
            case "look_at":
                return look_at_command(self.game_state, tokens)
            case "open":
                return open_command(self.game_state, tokens)
            case "pick_lock":
                return pick_lock_command(self.game_state, tokens)
            case "pick_up":
                return pick_up_command(self.game_state, tokens)
            case "put":
                return put_command(self.game_state, tokens)
            case "quit":
                retval = quit_command(context, tokens)
                self.game_ending_state_msg = context.game_ending_state_msg
                return retval
            case "reroll":
                return reroll_command(self.game_state, tokens)
            case "set_class":
                return set_class_command(self.game_state, tokens)
            case "set_name":
                return set_name_command(self.game_state, tokens)
            case "status":
                return status_command(self.game_state, tokens)
            case "take":
                return take_command(self.game_state, tokens)
            case "unequip":
                return unequip_command(self.game_state, tokens)
            case "unlock":
                return unlock_command(self.game_state, tokens)
            case _:
                raise InternalError(f"unrecognized command: {_}")
