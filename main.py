from logging import getLogger, Logger
from typing import Any
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction

log: Logger = getLogger(__name__)

class SteamExtension(Extension):
    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, SteamExtensionKeywordEventListener())

# http://docs.ulauncher.io/en/stable/extensions/libs.html

def fuzzy_match_filter(items: list[tuple[str, Any, ...]], match: str | None) -> list[tuple[str, Any, ...]]:
    """
    Filters a list of items based on a fuzzy match. If no match is provided, the items are sorted alphabetically.

    Args:
        items (list[tuple[str, Any, ...]]): The list of items to filter.
        match (str | None): The fuzzy match to filter the items by.

    Returns:
        list[tuple[str, Any, ...]]: The filtered list of items.
    """
    from difflib import SequenceMatcher

    if match is None:
        items.sort(key=lambda x: x[0].lower())
        return items
    matches: list[str] = match.strip().lower().split()
    # items = sorted([item for item in items if all(word in item[0].lower() for word in matches)], key=lambda x: x[0].lower())
    items = [item for item in items if all(word in item[0].lower() for word in matches)]
    items.sort(
        key=lambda x: SequenceMatcher(
            None, x[0].lower(), match.strip().lower()
        ).ratio(),
        reverse=True
    )
    log.debug(items)
    return items

def get_extension_path() -> str:
    return "/".join(__file__.split("/")[:-1])

# https://developer.valvesoftware.com/wiki/Steam_browser_protocol

class SteamExtensionKeywordEventListener(EventListener):
    def on_event(self, event, extension):
        from .get import get_all_owned_steam_apps, get_installed_steam_apps, get_non_steam_apps
        from os import mkdir
        from os.path import isdir, isfile
        from urllib.error import HTTPError
        from urllib.request import urlretrieve

        items: list[ExtensionResultItem] = []
        if event.get_keyword() == extension.preferences["game_keyword"]:
            steam_apps: tuple[str, int, bool] = get_installed_steam_apps(
                extension.preferences["steamapps_folder"]
            )  # + get_non_steam_apps(extension.preferences["userdata_folder"])
            log.debug(event.get_argument())
            steam_apps = fuzzy_match_filter(
                steam_apps, event.get_argument()
            )
            for app in steam_apps:
                items.append(
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name=app[0],
                        on_enter=RunScriptAction(f"steam steam://run/{app[1]}" if app[2] else f"steam steam://rungameid/{app[1]}")
                    )
                )
        elif event.get_keyword() == extension.preferences["api_keyword"]:
            owned_steam_apps: tuple[str, int, str] = get_all_owned_steam_apps(
                extension.preferences["api_key"], extension.preferences["steam_id"]
            )
            owned_steam_apps = fuzzy_match_filter(
                owned_steam_apps, event.get_argument()
            )
            ext_path: str = get_extension_path()
            if not isdir(f"{ext_path}/images/apps"):
                mkdir(f"{ext_path}/images/apps")
            for app in owned_steam_apps:
                if not isfile(f"{ext_path}/images/apps/{app[1]}.jpg"):
                    # Download the icon
                    try:
                        urlretrieve(app[2], f"{ext_path}/images/apps/{app[1]}.jpg")
                    except HTTPError:
                        pass
                items.append(
                    ExtensionResultItem(
                        icon=f"images/apps/{app[1]}.jpg",
                        name=app[0],
                        on_enter=RunScriptAction(f"steam steam://rungameid/{app[1]}")
                    )
                )
        else:  # event.get_keyword() == extension.preferences["nav_keyword"]
            navigations: list[tuple[str, str]] = [
                ("Quit Steam", "steam steam://exit"),
                ("Friends", "steam steam://friends"),
                ("Activate Product", "steam steam://open/activateproduct"),
                ("Big Picture", "steam steam://open/bigpicture"),
                ("Console", "steam steam://open/console"),
                ("Downloads", "steam steam://open/downloads"),
                ("Friends (Open)", "steam steam://open/friends"),
                ("Games Library", "steam steam://open/games"),
                ("Preferred Window", "steam steam://open/main"),
                ("Music", "steam steam://open/music"),
                ("Music Player", "steam steam://open/musicplayer"),
                ("Media", "steam steam://open/media"),
                ("News", "steam steam://open/news"),
                ("Screenshots", "steam steam://open/screenshots"),
                ("Servers", "steam steam://open/servers"),
                ("Settings", "steam steam://open/settings"),
                ("Tools", "steam steam://open/tools"),
                ("Account Settings", "steam steam://settings/account"),
                ("Friends Settings", "steam steam://settings/friends"),
                ("Interface Settings", "steam steam://settings/interface"),
                ("In-game Settings", "steam steam://settings/ingame"),
                ("Download Settings", "steam steam://settings/downloads"),
                ("Voice Settings", "steam steam://settings/voice"),
                ("Notifications", "steam steam://url/CommentNotifications"),
                ("Community", "steam steam://url/CommunityHome"),
                ("Inventory", "steam steam://url/CommunityInventory"),
                ("Community Search", "steam steam://url/CommunitySearch"),
                ("Family Sharing", "steam steam://url/FamilySharing"),
                ("Family View", "steam steam://url/ParentalSetup"),
                ("Profile Control", "steam steam://url/SteamIDControlPage"),
                ("Edit Profile", "steam steam://url/SteamIDEditPage"),
                ("Profile Friends", "steam steam://url/SteamIDFriendsPage"),
                ("Profile", "steam steam://url/SteamIDMyProfile"),
                ("Workshop", "steam steam://url/SteamWorkshop"),
                ("Store", "steam steam://url/Store"),
                ("Store Settings", "steam steam://url/StoreAccount"),
                ("Store Cart", "steam steam://url/StoreCart"),
                ("Support", "steam steam://url/SupportFrontPage"),
            ]
            navigations = fuzzy_match_filter(navigations, event.get_argument())
            for navigation in navigations:
                items.append(
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name=navigation[0],
                        on_enter=RunScriptAction(navigation[1])
                    )
                )
        return RenderResultListAction(items)

if __name__ == '__main__':
    SteamExtension().run()
