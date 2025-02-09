from json import loads as json_loads
from logging import Logger
from logging.config import fileConfig as logging_fileConfig
import os
from os.path import abspath
from typing import Any

DIR_SEP: str = "/"
if os.name == "nt":
    DIR_SEP = "\\"

EXTENSION_PATH: str = f"{DIR_SEP.join(__file__.split(DIR_SEP)[:-1])}{DIR_SEP}"
if len(EXTENSION_PATH) <= 1:
    EXTENSION_PATH = "."
EXTENSION_PATH = abspath(EXTENSION_PATH)
if EXTENSION_PATH[-1] != DIR_SEP:
    EXTENSION_PATH += DIR_SEP


def get_logger(module_name: str) -> Logger:
    """
    Gets the logger for the given module name. The logging configuration file logging.conf is loaded if it exists.

    Args:
        module_name (str): The name of the module.

    Returns:
        Logger: The logger.
    """
    from logging import getLogger
    from os.path import isfile

    if isfile(f"{EXTENSION_PATH}logging.conf"):
        logging_fileConfig(
            f"{EXTENSION_PATH}logging.conf", disable_existing_loggers=False
        )
    return getLogger(module_name)


log: Logger = get_logger(__name__)


def get_preferences_from_env() -> dict[str, Any]:
    """
    Gets the preferences from the .env file and returns them as a dictionary. Used for testing of individual modules.

    Returns:
        dict[str, Any]: The preferences dictionary.
    """
    from configparser import ConfigParser

    preferences_file = ConfigParser()
    preferences_file.read(".env")
    return {k.upper(): v for k, v in preferences_file.items("PREFERENCES")}


REQUIRED_PREFERENCES: tuple[str, ...] = ()
with open(f"{EXTENSION_PATH}manifest.json", "r", encoding="utf-8") as f:
    REQUIRED_PREFERENCES = tuple(
        preference["id"] for preference in json_loads(f.read())["preferences"]
    )


def check_required_preferences(preferences: dict[str, Any]) -> None:
    """
    Checks if all required preferences are present in the preferences dictionary.

    Args:
        preferences (dict[str, Any]): The preferences dictionary.

    Raises:
        ValueError: If a required preference is missing.
    """
    log.debug("Checking all required preferences are present")
    try:
        missing_preference: str = next(
            key for key in REQUIRED_PREFERENCES if key not in preferences.keys()
        )
        raise ValueError(
            f"Missing preference key '{missing_preference}', add to .env file"
        )
    except StopIteration:
        pass


DEFAULT_ICON: str = f"{EXTENSION_PATH}images{DIR_SEP}icon.png"
DEFAULT_LANGUAGE: str = "en-GB"
# Navigation
# https://developer.valvesoftware.com/wiki/Steam_browser_protocol
# TODO: Add groups actions
STEAM_NAVIGATIONS: list[str] = [
    # "AddNonSteamGame",  Does nothing
    # "advertise/%a",  Duplicate of "store/%a"
    # "appnews/%a",  Duplicate of "updatenews/%a"
    "backup/%a",
    # "browsemedia",  Does nothing
    "cdkeys/%a",
    # "checksysreqs/%a",  Does nothing
    "controllerconfig/%a",  # TODO: Test while using Steam Input
    # "defrag/%a",  Does nothing
    "exit",
    # "flushconfig",  Does nothing
    "forceinputappid/%a",  # TODO: Test while using Steam Input
    # "friends",  Does nothing
    # "friends/joinchat/%f",  Duplicate of "friends/message/%f"
    "friends/message/%f",
    "friends/players",
    # "friends/settings/hideoffline",  Does nothing
    # "friends/settings/showavatars",  Does nothing
    # "friends/settings/sortbyname",  Does nothing
    "friends/status/away",
    # "friends/status/busy",  Does nothing
    "friends/status/invisible",
    "friends/status/offline",
    "friends/status/online",
    # "friends/status/play",  Does nothing
    # "friends/status/trade",  Does nothing
    "gameproperties/%a",
    # "guestpasses",  Is meant to display pending gifts, but currently is a duplicate of "url/CommunityInventory"
    # TODO: Test music player navigations with a soundtrack installed on the system
    "musicplayer/decreasevolume",
    "musicplayer/increasevolume",
    "musicplayer/pause",
    "musicplayer/play",
    "musicplayer/playnext",
    "musicplayer/playprevious",
    "musicplayer/togglemute",
    "musicplayer/toggleplayingrepeatstatus",
    "musicplayer/toggleplayingshuffled",
    "musicplayer/toggleplaypause",
    "open/activateproduct",
    "open/bigpicture",
    "open/console",
    "open/downloads",
    "open/friends",
    "open/games",
    # "open/games/details",  Duplicate of "open/games"
    # "open/games/grid",  Duplicate of "open/games"
    # "open/games/list",  Duplicate of "open/games"
    "open/largegameslist",
    # "open/main",  Does nothing
    "open/minigameslist",
    # TODO: Test music player navigations with a soundtrack installed on the system
    "open/music",
    "open/musicplayer",
    # "open/mymedia",  Does nothing
    # "open/news",  Does nothing
    # "open/registerproduct",  Does nothing
    "open/screenshots/%a",
    "open/servers",
    # "open/settings",  Duplicate of "settings/account"
    "open/tools",
    "settings/account",
    "settings/downloads",
    "settings/friends",
    "settings/ingame",
    "settings/interface",
    "settings/voice",
    # "stopstreaming",  Disabled as there is no way to start streaming from the extension
    "store",
    "store/%a",
    "uninstall/%a",
    "UpdateFirmware",  # TODO: Test while using a Steam controller
    "updatenews/%a",
    # "url/CommentNotifications",  Encounters an error when processing the request
    "url/CommunityFriendsThatPlay/%a",
    "url/CommunityHome",
    "url/CommunityInventory",
    # "url/CommunitySearch",  Does nothing
    # "url/DownloadsSupportInfo",  Does nothing
    "url/FamilySharing",
    "url/GameHub/%a",
    # "url/LeaveGroupPage",  Does nothing
    "url/LegalInformation",
    "url/MyHelpRequests",
    "url/ParentalSetup",
    "url/PrivacyPolicy",
    "url/SSA",
    # "url/SteamGreenlight",  Does nothing
    # "url/SteamIDControlPage",  Does nothing
    "url/SteamIDEditPage",
    "url/SteamIDFriendsPage",
    "url/SteamIDMyProfile",
    "url/SteamIDPage/%f",
    "url/SteamWorkshop",
    "url/SteamWorkshopPage/%a",
    # "url/Store",  Duplicate of "store", does nothing if Steam is closed
    "url/StoreAccount",
    # "url/StoreAppPage/%a",  Duplicate of "store/%a"
    "url/StoreCart",
    # "url/StoreDLCPage/%a",  Does nothing
    # "url/Storefront",  Does nothing
    # "url/StoreFrontPage",  Duplicate of "store"
    # "url/SupportFrontPage",  Does nothing
    "validate/%a",
    "viewfriendsgame/%f",
]
