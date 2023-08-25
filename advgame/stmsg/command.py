#!/usr/bin/python3

from advgame.stmsg.gsm import GameStateMessage
from advgame.utils import join_strs_w_comma_conj


__all__ = ("BadSyntax", "ClassRestricted", "NotAllowedNow", "NotRecognized")


class BadSyntax(GameStateMessage):
    """
Returned by command methods of advgame.process.CommandProcessor when
incorrect syntax for a command has been used.
    """

    __slots__ = 'command', 'proper_syntax_options'

    @property
    def message(self):
        # The proper_syntax_options tuple is drawn from
        # advgame.process.COMMANDS_SYNTAX; it is comprised of
        # strings which spell out valid command arguments. \u00A0 (a
        # nonbreaking space) is used in place of normal spaces to
        # ensure that a syntax line is never broken across a newline
        # by advgame.utilsities.textwrapper(). (They become kindof
        # unreadable if they're word-wrapped.)
        #
        # This message property joins the command with each line of
        # the proper_syntax_options tuple, and presents a corrective
        # outlining valid syntax for this command.
        command = self.command.upper().replace(' ', '\u00A0')
        syntax_options = [f"'{command}\u00A0{syntax_option}'" if syntax_option else f"'{command}'"
                          for syntax_option in self.proper_syntax_options]
        proper_syntax_options_str = join_strs_w_comma_conj(
                syntax_options, 'or')
        return (f'{self.command.upper()} command: bad syntax. Should be {proper_syntax_options_str}.')

    def __init__(self, command, proper_syntax_options):
        self.command = command
        self.proper_syntax_options = proper_syntax_options


class ClassRestricted(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.process() when the player
has used a command that is restricted to a class other than their own.
(For example, only thieves can use PICK LOCK.)
    """

    __slots__ = 'command', 'classes',

    @property
    def message(self):
        # This message property assembles a list of classes (in
        # self.classes) which are authorized to use the given command
        # (in self.command).
        classes_plural = ([class_str + 's' if class_str != 'thief' else 'thieves' for class_str in self.classes])
        class_str = join_strs_w_comma_conj(classes_plural, 'and')
        return f'Only {class_str} can use the {self.command.upper()} command.'

    def __init__(self, command, *classes):
        self.command = command
        self.classes = classes


class NotAllowedNow(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.process() when the
player has used a command that is not allowed in the current
game mode. The game has two modes: pregame, when name and class
are chosen and ability scores are rolled, and in-game, when the
player plays the game. Different command sets are allowed in each
mode. See advgame.process.CommandProcessor.pregame_commands and
advgame.process.CommandProcessor.ingame_commands for the lists.
    """

    __slots__ = 'command', 'allowed_commands', 'game_has_begun'

    @property
    def message(self):
        # This message property responds to a user using a pregame
        # command during ingame or an ingame command during pregame;
        # it assembles a list of allowed commands from self.allowed
        # commands and returns a remonstrative message informing the
        # player that the command they tried (in self.command) can't be
        # used in the current game mode (game_state_str), but commands
        # in this list (commands_str) can.
        game_state_str = ('before game start' if not self.game_has_begun else 'during the game')
        message_str = (f"Command '{self.command}' not allowed {game_state_str}. ")
        commands_str = join_strs_w_comma_conj([command.upper().replace('_', ' ')
                                               for command in sorted(self.allowed_commands)],
                                              'and')
        message_str += f'Commands allowed {game_state_str} are {commands_str}.'
        return message_str

    def __init__(self, command, allowed_commands, game_has_begun):
        self.command = command
        self.allowed_commands = allowed_commands
        self.game_has_begun = game_has_begun


class NotRecognized(GameStateMessage):
    """
Returned by advgame.process.CommandProcessor.process() when a command
was entered that is not known to the command processor.
    """

    __slots__ = 'command', 'allowed_commands', 'game_has_begun'

    @property
    def message(self):
        # This message property responds to a user entering a command
        # that's not recognized; it assembles a list of allowed commands
        # from self.allowed commands and returns a message informing
        # the player that the command they used (in self.command) isn't
        # recognized but in the current game mode (game_state_str)
        # commands in this list (commands_str) can.
        message_str = f"Command '{self.command}' not recognized. "
        game_state_str = ('before game start' if not self.game_has_begun else 'during the game')
        commands_str = join_strs_w_comma_conj([command.upper().replace('_', ' ')
                                               for command in sorted(self.allowed_commands)],
                                              'and')
        message_str += f'Commands allowed {game_state_str} are {commands_str}.'
        return message_str

    def __init__(self, command, allowed_commands, game_has_begun):
        self.command = command
        self.allowed_commands = allowed_commands
        self.game_has_begun = game_has_begun
