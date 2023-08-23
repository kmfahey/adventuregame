#!/usr/bin/python3

from ._common import *


__all__ = "various", "unlock", "unequip", "take", "status", "setname"

__all__ += ("GameStateMessage", "Stmsg_CommandBadSyntax", "Stmsg_CommandClassRestricted", "Stmsg_CommandNotAllowedNow",
            "Stmsg_CommandNotRecognized", "Stmsg_Attack_AttackHit", "Stmsg_Attack_AttackMissed",
            "Stmsg_Attack_OpponentNotFound", "Stmsg_Attack_YouHaveNoWeaponOrWandEquipped",
            "Stmsg_Batkby_AttackedAndHit", "Stmsg_Batkby_AttackedAndNotHit",
            "Stmsg_Batkby_CharacterDeath", "Stmsg_Begin_GameBegins",
            "Stmsg_Begin_NameOrClassNotSet", "Stmsg_Cstspl_CastDamagingSpell",
            "Stmsg_Cstspl_CastHealingSpell", "Stmsg_Cstspl_InsufficientMana",
            "Stmsg_Cstspl_NoCreatureToTarget", "Stmsg_Close_ElementNotCloseable",
            "Stmsg_Close_ElementHasBeenClosed", "Stmsg_Close_ElementIsAlreadyClosed",
            "Stmsg_Close_ElementToCloseNotHere", "Stmsg_Drink_DrankManaPotion",
            "Stmsg_Drink_DrankManaPotion_when_Not_A_Spellcaster", "Stmsg_Drink_ItemNotDrinkable",
            "Stmsg_Drink_ItemNotInInventory", "Stmsg_Drink_TriedToDrinkMoreThanPossessed",
            "Stmsg_Drink_QuantityUnclear", "Stmsg_Drop_DroppedItem", "Stmsg_Drop_QuantityUnclear",
            "Stmsg_Drop_TryingToDropItemYouDontHave", "Stmsg_Drop_TryingToDropMoreThanYouHave",
            "Stmsg_Equip_ClassCantUseItem", "Stmsg_Equip_NoSuchItemInInventory",
            "Stmsg_Help_CommandNotRecognized", "Stmsg_Help_DisplayCommands",
            "Stmsg_Help_DisplayHelpForCommand", "Stmsg_Inven_DisplayInventory",
            "Stmsg_Leave_DoorIsLocked", "Stmsg_Leave_LeftRoom", "Stmsg_Leave_WonTheGame",
            "Stmsg_Lock_DontPossessCorrectKey", "Stmsg_Lock_ElementNotUnlockable",
            "Stmsg_Lock_ElementHasBeenUnlocked", "Stmsg_Lock_ElementIsAlreadyUnlocked",
            "Stmsg_Lock_ElementToUnlockNotHere", "Stmsg_LookAt_FoundContainerHere",
            "Stmsg_LookAt_FoundCreatureHere", "Stmsg_LookAt_FoundDoorOrDoorway",
            "Stmsg_LookAt_FoundItemOrItemsHere", "Stmsg_LookAt_FoundNothing",
            "Stmsg_Open_ElementNotOpenable", "Stmsg_Open_ElementHasBeenOpened",
            "Stmsg_Open_ElementIsAlreadyOpen", "Stmsg_Open_ElementIsLocked",
            "Stmsg_Open_ElementToOpenNotHere", "Stmsg_PkLock_ElementNotUnlockable",
            "Stmsg_PkLock_TargetHasBeenUnlocked", "Stmsg_PkLock_TargetNotFound",
            "Stmsg_PkLock_TargetNotLocked", "Stmsg_PickUp_CantPickUpChestCorpseCreatureOrDoor",
            "Stmsg_PickUp_ItemNotFound", "Stmsg_PickUp_ItemPickedUp", "Stmsg_PickUp_QuantityUnclear",
            "Stmsg_PickUp_TryingToPickUpMoreThanIsPresent", "Stmsg_Put_PutAmountOfItem",
            "Stmsg_Put_ItemNotInInventory", "Stmsg_Put_QuantityUnclear",
            "Stmsg_Put_TryingToPutMoreThanYouHave", "Stmsg_Quit_HaveQuitTheGame",
            "Stmsg_Reroll_NameOrClassNotSet", "Stmsg_SetCls_ClassSet", "Stmsg_SetCls_InvalidClass")
