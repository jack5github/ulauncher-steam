from json import loads as json_loads
from logging import getLogger, Logger
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

try:
    logging_fileConfig(f"{EXTENSION_PATH}logging.conf", disable_existing_loggers=False)
except FileNotFoundError:
    pass
log: Logger = getLogger(__name__)

REQUIRED_PREFERENCES: tuple[str, ...] = ()
if os.name == "nt":
    with open(f"{EXTENSION_PATH}manifest.json", "r", encoding="utf-8") as f:
        REQUIRED_PREFERENCES = tuple(
            preference["id"] for preference in json_loads(f.read())["preferences"]
        )


def check_required_preferences(preferences: dict[str, Any]) -> None:
    """
    Checks if all required preferences are present in the preferences dictionary on Windows.

    Args:
        preferences (dict[str, Any]): The preferences dictionary.

    Raises:
        ValueError: If a required preference is missing.
    """
    if os.name == "nt":
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


# Navigation
# https://developer.valvesoftware.com/wiki/Steam_browser_protocol
# TODO: Add more friends actions
# TODO: Add groups actions
STEAM_NAVIGATIONS: list[str] = [
    "AddNonSteamGame",
    "advertise/%g",
    "appnews/%g",
    "backup/%g",
    "browsemedia",
    "cdkeys/%g",
    "checksysreqs/%g",
    "controllerconfig/%g",
    "defrag/%g",
    "exit",
    "friends",
    "friends/players",
    "friends/settings/hideoffline",
    "friends/settings/showavatars",
    "friends/settings/sortbyname",
    "friends/status/away",
    "friends/status/busy",
    "friends/status/invisible",
    "friends/status/trade",
    "friends/status/play",
    "friends/status/offline",
    "friends/status/online",
    "flushconfig",
    "forceinputappid/%g",
    "gameproperties/%g",
    "guestpasses",
    "musicplayer/play",
    "musicplayer/pause",
    "musicplayer/toggleplaypause",
    "musicplayer/playprevious",
    "musicplayer/playnext",
    "musicplayer/togglemute",
    "musicplayer/increasevolume",
    "musicplayer/decreasevolume",
    "musicplayer/toggleplayingrepeatstatus",
    "musicplayer/toggleplayingshuffled",
    "open/activateproduct",
    "open/bigpicture",
    "open/console",
    "open/downloads",
    "open/friends",
    "open/games",
    "open/games/details",
    "open/games/grid",
    "open/games/list",
    "open/largegameslist",
    "open/minigameslist",
    "open/main",
    "open/music",
    "open/musicplayer",
    "open/mymedia",
    "open/news",
    "open/registerproduct",
    "open/screenshots/%g",
    "open/servers",
    "open/settings",
    "open/tools",
    "settings/account",
    "settings/friends",
    "settings/interface",
    "settings/ingame",
    "settings/downloads",
    "settings/voice",
    "stopstreaming",
    "store",
    "store/%g",
    "uninstall/%g",
    "UpdateFirmware",
    "updatenews/%g",
    "url/CommentNotifications",
    "url/CommunityFriendsThatPlay/%g",
    "url/CommunityHome",
    "url/CommunityInventory",
    "url/CommunitySearch",
    "url/DownloadsSupportInfo",
    "url/FamilySharing",
    "url/GameHub/%g",
    "url/LeaveGroupPage",
    "url/LegalInformation",
    "url/MyHelpRequests",
    "url/ParentalSetup",
    "url/PrivacyPolicy",
    "url/SSA",
    "url/SteamIDControlPage",
    "url/SteamIDEditPage",
    "url/SteamIDFriendsPage",
    "url/SteamIDMyProfile",
    "url/SteamWorkshop",
    "url/SteamWorkshopPage/%g",
    "url/SteamGreenlight",
    "url/Store",
    "url/StoreAccount",
    "url/StoreAppPage/%g",
    "url/StoreDLCPage/%g",
    "url/StoreCart",
    "url/Storefront",
    "url/StoreFrontPage",
    "url/SupportFrontPage",
    "validate/%g",
]

DEFAULT_LANGUAGE: str = "en-GB"
