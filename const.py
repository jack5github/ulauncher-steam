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
    # "s:AddNonSteamGame",  Does nothing
    # "s:advertise/%a",  Duplicate of "s:store/%a"
    # "s:appnews/%a",  Duplicate of "s:updatenews/%a"
    "s:backup/%a",
    # "s:browsemedia",  Does nothing
    "s:cdkeys/%a",
    # "s:checksysreqs/%a",  Does nothing
    "s:controllerconfig/%a",  # TODO: Test while using Steam Input
    # "s:defrag/%a",  Does nothing
    "s:exit",
    # "s:flushconfig",  Does nothing
    "s:forceinputappid/%a",  # TODO: Test while using Steam Input
    # "s:friends",  Does nothing
    # "s:friends/joinchat/%f",  Duplicate of "s:friends/message/%f"
    "s:friends/message/%f",
    "s:friends/players",
    # "s:friends/settings/hideoffline",  Does nothing
    # "s:friends/settings/showavatars",  Does nothing
    # "s:friends/settings/sortbyname",  Does nothing
    "s:friends/status/away",
    # "s:friends/status/busy",  Does nothing
    "s:friends/status/invisible",
    "s:friends/status/offline",
    "s:friends/status/online",
    # "s:friends/status/play",  Does nothing
    # "s:friends/status/trade",  Does nothing
    "s:gameproperties/%a",
    # "s:guestpasses",  Is meant to display pending gifts, but currently is a duplicate of "s:url/CommunityInventory"
    "s:musicplayer/decreasevolume",
    "s:musicplayer/increasevolume",
    "s:musicplayer/pause",
    "s:musicplayer/play",
    "s:musicplayer/playnext",
    "s:musicplayer/playprevious",
    "s:musicplayer/togglemute",
    "s:musicplayer/toggleplayingrepeatstatus",
    "s:musicplayer/toggleplayingshuffled",
    "s:musicplayer/toggleplaypause",
    "s:open/activateproduct",
    "s:open/bigpicture",
    "s:open/console",
    "s:open/downloads",
    "s:open/friends",
    "s:open/games",
    # "s:open/games/details",  Duplicate of "s:open/games"
    # "s:open/games/grid",  Duplicate of "s:open/games"
    # "s:open/games/list",  Duplicate of "s:open/games"
    "s:open/largegameslist",
    # "s:open/main",  Does nothing
    "s:open/minigameslist",
    # "s:open/music",  Does nothing
    # "s:open/musicplayer",  Does nothing
    # "s:open/mymedia",  Does nothing
    # "s:open/news",  Does nothing
    # "s:open/registerproduct",  Does nothing
    "s:open/screenshots/%a",
    "s:open/servers",
    # "s:open/settings",  Duplicate of "s:settings/account"
    "s:open/tools",
    "s:settings/account",
    "s:settings/downloads",
    "s:settings/friends",
    "s:settings/ingame",
    "s:settings/interface",
    "s:settings/voice",
    # "s:stopstreaming",  Disabled as there is no way to start streaming from the extension
    "s:store",
    "s:store/%a",
    "s:uninstall/%a",
    "s:UpdateFirmware",  # TODO: Test while using a Steam controller
    "s:updatenews/%a",
    # "s:url/CommentNotifications",  Encounters an error when processing the request
    "s:url/CommunityFriendsThatPlay/%a",
    "s:url/CommunityHome",
    "s:url/CommunityInventory",
    # "s:url/CommunitySearch",  Does nothing
    # "s:url/DownloadsSupportInfo",  Does nothing
    "s:url/FamilySharing",
    "s:url/GameHub/%a",
    # "s:url/LeaveGroupPage",  Does nothing
    "s:url/LegalInformation",
    "s:url/MyHelpRequests",
    "s:url/ParentalSetup",
    "s:url/PrivacyPolicy",
    "s:url/SSA",
    # "s:url/SteamGreenlight",  Does nothing
    # "s:url/SteamIDControlPage",  Does nothing
    "s:url/SteamIDEditPage",
    "s:url/SteamIDFriendsPage",
    "s:url/SteamIDMyProfile",
    "s:url/SteamIDPage/%f",
    "s:url/SteamWorkshop",
    "s:url/SteamWorkshopPage/%a",
    # "s:url/Store",  Duplicate of "s:store", does nothing if Steam is closed
    "s:url/StoreAccount",
    # "s:url/StoreAppPage/%a",  Duplicate of "s:store/%a"
    "s:url/StoreCart",
    # "s:url/StoreDLCPage/%a",  Does nothing
    # "s:url/Storefront",  Does nothing
    # "s:url/StoreFrontPage",  Duplicate of "s:store"
    # "s:url/SupportFrontPage",  Does nothing
    "s:validate/%a",
    "s:viewfriendsgame/%f",
    # TODO: Add nav images for the following URLs
    # TODO: Add support for inserting the user's Steam username into the URL
    "w:help.steampowered.com",
    "w:steamcommunity.com/discussions",
    "w:steamcommunity.com/market",
    "w:store.steampowered.com/account/cookiepreferences",
    "w:store.steampowered.com/account/preferences",
    "w:store.steampowered.com/charts",
    "w:store.steampowered.com/explore",
    "w:store.steampowered.com/news",
    "w:store.steampowered.com/replay",
    "w:store.steampowered.com/steamaccount/addfunds",
    "w:store.steampowered.com/wishlist",
]
