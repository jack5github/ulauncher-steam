from const import DEFAULT_LANGUAGE, EXTENSION_PATH, STEAM_NAVIGATIONS
from datetime import datetime
from logging import getLogger, Logger
from os.path import isfile
import sys
from typing import Any

log: Logger = getLogger(__name__)


class SteamExtensionItem():
    """
    A class that represents an item to be displayed by the Steam extension.
    """
    def __init__(
        self,
        appid: str | None = None,
        name: str | None = None,
        non_steam: bool = False,
        installed: bool = True,
        description: str | None = None,
        action: str | None = None,
        ulaunched_last: datetime | None = None,
        ulaunched_times: int = 0,
        is_error: bool = False,
    ) -> None:
        """
        Initialises a new SteamExtensionItem instance.

        Args:
            appid (str | None, optional): The ID of the application, if this is a Steam application. Stored as a string due to JSON limitations. Defaults to None.
            name (str | None, optional): The name of the application or action this item represents. Defaults to None.
            non_steam (bool, optional): Whether this is a non-Steam application. Defaults to False.
            installed (bool, optional): Whether this is an installed Steam application. Defaults to True.
            description (str | None, optional): The description of the application or action this item represents. Defaults to None.
            action (str | None, optional): The action to perform when this item is launched, if necessary to specify. Defaults to None.
            ulaunched_last (datetime | None, optional): The last time this item was launched from uLauncher. Defaults to None.
            ulaunched_times (int, optional): The number of times this item has been launched from uLauncher. Defaults to 0.
            is_error (bool, optional): Whether this item represents an error. Defaults to False.
        """
        self.appid: str | None = appid
        self.name: str | None = name
        self.non_steam: bool = non_steam
        self.installed: bool = installed
        self.description: str | None = description
        self.action: str | None = action
        self.ulaunched_last: datetime | None = ulaunched_last
        self.ulaunched_times: int = ulaunched_times
        self.is_error: bool = is_error

    def __repr__(self) -> str:
        """
        Returns a verbose representation of the SteamExtensionItem instance.

        Returns:
            str: The verbose representation.
        """
        if "tiny-repr" in sys.argv:
            return f"({repr(self.appid)}, name={repr(self.name)}, non={repr(self.non_steam)}, inst={repr(self.installed)}, desc={repr(self.description)}, act={repr(self.action)}, ulast={repr(self.ulaunched_last)}, utimes={repr(self.ulaunched_times)}, err={self.is_error})"
        return f"SteamExtensionItem(appid={repr(self.appid)}, name={repr(self.name)}, non_steam={repr(self.non_steam)}, installed={repr(self.installed)}, description={repr(self.description)}, action={repr(self.action)}, ulaunched_last={repr(self.ulaunched_last)}, ulaunched_times={repr(self.ulaunched_times)}, is_error={self.is_error})"

    @classmethod
    def from_error(cls, err: Exception) -> "SteamExtensionItem":
        """
        Creates a new SteamExtensionItem instance from an error.

        Args:
            err (Exception): The error.

        Returns:
            SteamExtensionItem: A new SteamExtensionItem instance.
        """
        return SteamExtensionItem(
            name=err.__class__.__name__,
            description=str(err),
            is_error=True
        )

    def to_result_dict(self) -> dict[str, Any]:
        """
        Converts the SteamExtensionItem instance to a dictionary representation for uLauncher, which after minimal adjustments can be passed into the uLauncher API.

        Returns:
            dict[str, Any]: The dictionary representation.
        """
        icon_file: str = "images/icon.png"
        if isfile(f"{EXTENSION_PATH}images/apps/{self.appid}.jpg"):
            icon_file = f"images/apps/{self.appid}.jpg"
        result_dict: dict[str, Any] = {
            "icon": icon_file,
            "name": self.name if self.name is not None else str(self.appid),
            "on_enter": {
                "class": (
                    "ExtensionCustomAction"
                    if self.action is not None and self.action == "rebuild-cache"
                    else "RunScriptAction"
                    if self.appid is not None or self.action is not None
                    else "HideWindowAction"
                )
            }
        }
        if self.description is not None:
            result_dict["description"] = self.description
        if self.appid is not None or self.action is not None:
            result_dict["on_enter"]["argument"] = (
                self.action
                if self.action is not None
                else f"steam steam://rungameid/{self.appid}"
            )
        return result_dict

    def to_sort_string(self, sort_keys_string: str) -> str:
        """
        Converts the SteamExtensionItem instance to a string representation for sorting, used when no search is provided.

        Args:
            sort_keys_string (str): The desired sort keys as a string, separated by commas.

        Returns:
            str: The string representation for sorting.
        """
        sort_string: str = "0" if {self.is_error} else "1"
        sort_keys: list[str] = sort_keys_string.split(",")
        for index, key in enumerate(sort_keys):
            key = key.strip()
            if key == "name":
                sort_string += self.name if self.name is not None else ""
            elif key == "description":
                sort_string += self.description if self.description is not None else ""
            elif key == "appid":
                sort_string += self.appid if self.appid is not None else ""
            elif key == "non_steam":
                sort_string += str(self.non_steam)
            elif key == "ulaunched_last":
                sort_string += str(self.ulaunched_last.timestamp()).zfill(20) if self.ulaunched_last is not None else ""
            elif key == "ulaunched_times":
                sort_string += str(self.ulaunched_times)
            if index != len(sort_keys) - 1:
                sort_string += "\t"
        return sort_string.lower()

    def to_search_string(self) -> str:
        """
        Converts the SteamExtensionItem instance to a string representation for searching.

        Returns:
            str: The string representation for searching.
        """
        return f"{self.name if self.name is not None else ""}{self.description if self.description is not None else ""}".lower()


def get_lang_string(lang: dict[str, Any], language: str, key: str) -> str:
    """
    Gets a string from the language dictionary, which is loaded from lang.json.

    Args:
        lang (dict[str, Any]): The language dictionary.
        language (str): The desired language.
        key (str): The string to retrieve from the language dictionary.

    Raises:
        KeyError: If the default language is not in the language dictionary.
        KeyError: If the desired key is not in the language dictionary, both for the desired and the default language.

    Returns:
        str: The string from the language dictionary, either from the desired or the default language.
    """
    log.debug(f"Getting '{key}' for language '{language}' from lang.json")
    if language in lang.keys():
        if key in lang[language].keys():
            return str(lang[language][key])
    if DEFAULT_LANGUAGE not in lang.keys():
        raise KeyError(f"Default language '{DEFAULT_LANGUAGE}' is not in lang.json")
    if key not in lang[DEFAULT_LANGUAGE].keys():
        raise KeyError(
            f"'{key}' is not in lang.json for '{language}' or '{DEFAULT_LANGUAGE}'"
        )
    return str(lang[DEFAULT_LANGUAGE][key])


def steam_extension_event(
    manifest: dict[str, Any], search: str
) -> list[SteamExtensionItem]:
    """
    The main code that is run when the Steam extension keyword is entered into uLauncher. This function looks for Steam and non-Steam apps and menus using cache.json and returns a list of SteamExtensionItem instances. It is designed to be run on its own without needing to import the uLauncher API.

    Args:
        manifest (dict[str, Any]): The manifest dictionary, a set of variables that are passed into the extension from uLauncher's extension settings.
        search (str): The search string entered after the Steam extension keyword.

    Returns:
        list[SteamExtensionItem]: A list of SteamExtensionItem instances.
    """
    from difflib import SequenceMatcher
    from json import loads as json_loads

    log.info(f"Triggering Steam extension event with search '{search}'")
    items: list[SteamExtensionItem] = []
    log.debug("Checking manifest keys")
    try:
        missing_manifest_key: str = next(
            key for key in (
                "keyword", "language", "sort-keys"
            ) if key not in manifest.keys()
        )
        items = [
            SteamExtensionItem.from_error(
                KeyError(f"'{missing_manifest_key}' missing from manifest keys")
            )
        ]
        return items
    except StopIteration:
        pass
    try:
        log.debug("Loading lang.json")
        language: str = DEFAULT_LANGUAGE
        if "language" in manifest.keys():
            language = manifest["language"]
        lang: dict[str, Any] = {}
        try:
            with open(f"{EXTENSION_PATH}lang.json", "r", encoding="utf-8") as f:
                lang = json_loads(f.read())
        except Exception as err:
            items.insert(0, SteamExtensionItem.from_error(err))
            return items
        if language not in lang.keys():
            items.insert(0, SteamExtensionItem.from_error(
                KeyError(f"Language '{language}' not found in lang.json")
            ))
            language = DEFAULT_LANGUAGE
        log.debug("Loading cache.json")
        cache: dict[str, Any] = {}
        if isfile(f"{EXTENSION_PATH}cache.json"):
            try:
                with open(f"{EXTENSION_PATH}cache.json", "r", encoding="utf-8") as f:
                    cache = json_loads(f.read())
            except Exception as err:
                items.insert(0, SteamExtensionItem.from_error(err))
        steam_apps: list[SteamExtensionItem] = []
        if "steam-apps" in cache.keys():
            log.debug("Iterating through Steam apps")
            if not isinstance(cache["steam-apps"], dict):
                items.insert(0, SteamExtensionItem.from_error(
                    TypeError("'steam-apps' in cache.json is not a dictionary")
                ))
                cache["steam-apps"] = {}
            for appid, appinfo in cache["steam-apps"].items():
                if not isinstance(appinfo, dict):
                    items.insert(0, SteamExtensionItem.from_error(
                        TypeError(
                            f"'steam-apps' app ID {appid} in cache.json is not a dictionary"
                        )
                    ))
                    continue
                name: str = appid
                installed: bool = False
                ulaunched_last: datetime | None = None
                ulaunched_times: int = 0
                if "name" in appinfo.keys():
                    name = str(appinfo["name"])
                if "installed" in appinfo.keys() and appinfo["installed"]:
                    installed = True
                if "ulaunched-last" in appinfo.keys():
                    ulaunched_last = datetime.strptime(
                        str(appinfo["ulaunched-last"]), "%Y-%m-%d %H:%M:%S"
                    )
                if "ulaunched-times" in appinfo.keys():
                    ulaunched_times = int(appinfo["ulaunched-times"])
                steam_apps.append(
                    SteamExtensionItem(
                        appid=appid,
                        name=name,
                        installed=installed,
                        ulaunched_last=ulaunched_last,
                        ulaunched_times=ulaunched_times
                    )
                )
            items.extend(steam_apps)
        if "non-steam-apps" in cache.keys():
            log.debug("Iterating through non-Steam apps")
            if not isinstance(cache["non-steam-apps"], dict):
                items.insert(0, SteamExtensionItem.from_error(
                    TypeError("'non-steam-apps' in cache.json is not a dictionary")
                ))
                cache["non-steam-apps"] = {}
            for appid, appinfo in cache["non-steam-apps"].items():
                if not isinstance(appinfo, dict):
                    items.insert(0, SteamExtensionItem.from_error(
                        TypeError(
                            f"'non-steam-apps' app ID {appid} in cache.json is not a dictionary"
                        )
                    ))
                    continue
                name: str = appid
                ulaunched_last: datetime | None = None
                ulaunched_times: int = 0
                if "name" in appinfo.keys():
                    name = str(appinfo["name"])
                if "ulaunched-last" in appinfo.keys():
                    ulaunched_last = datetime.strptime(
                        str(appinfo["ulaunched-last"]), "%Y-%m-%d %H:%M:%S"
                    )
                if "ulaunched-times" in appinfo.keys():
                    ulaunched_times = int(appinfo["ulaunched-times"])
                items.append(
                    SteamExtensionItem(
                        appid=appid,
                        name=name,
                        non_steam=True,
                        ulaunched_last=ulaunched_last,
                        ulaunched_times=ulaunched_times
                    )
                )
        # Navigation
        # https://developer.valvesoftware.com/wiki/Steam_browser_protocol
        log.debug("Iterating through Steam navigations")
        if "steam-navs" not in cache.keys():
            cache["steam-navs"] = {}
        if not isinstance(cache["steam-navs"], dict):
            items.insert(0, SteamExtensionItem.from_error(
                TypeError("'steam-navs' in cache.json is not a dictionary")
            ))
            cache["steam-navs"] = {}
        navigations: list[str] = STEAM_NAVIGATIONS.copy()
        for nav_name in navigations:
            nav_action: str = f"steam steam://{nav_name}"
            try:
                nav_name = get_lang_string(lang, language, nav_name)
            except KeyError as err:
                items.insert(0, SteamExtensionItem.from_error(err))
            nav_description: str | None = None
            try:
                nav_description = get_lang_string(lang, language, f"{nav_name}%d")
            except KeyError as err:
                pass
            if "%g" not in nav_name:
                ulaunched_last: datetime | None = None
                ulaunched_times: int = 0
                if (
                    "steam-navs" in cache.keys()
                    and isinstance(cache["steam-navs"], dict)
                    and nav_name in cache["steam-navs"].keys()
                    and isinstance(cache["steam-navs"][nav_name], dict)
                ):
                    if "ulaunched-last" in appinfo.keys():
                        ulaunched_last = datetime.strptime(
                            str(appinfo["ulaunched-last"]), "%Y-%m-%d %H:%M:%S"
                        )
                    if "ulaunched-times" in appinfo.keys():
                        ulaunched_times = int(appinfo["ulaunched-times"])
                items.append(
                    SteamExtensionItem(
                        name=nav_name,
                        description=nav_description,
                        action=nav_action,
                        ulaunched_last=ulaunched_last,
                        ulaunched_times=ulaunched_times
                    )
                )
                continue
            log.debug(f"Iterating through Steam apps for navigation '{nav_name}'")
            for steam_app in steam_apps:
                app_id: str = steam_app.appid  # type: ignore
                app_name: str = steam_app.name  # type: ignore
                if app_id is None or app_name is None:
                    items.insert(0, SteamExtensionItem.from_error(
                        RuntimeError(
                            f"An in-memory Steam app has a missing app ID or name: ({app_id}, {repr(app_name)})"
                        )
                    ))
                    break
                specific_name: str = nav_name.replace("%g", app_name)
                specific_description: str | None = (
                    nav_description.replace("%g", app_name)
                    if nav_description is not None
                    else None
                )
                specific_action: str = nav_action.replace("%g", str(app_id))
                ulaunched_last: datetime | None = None
                ulaunched_times: int = 0
                items.append(
                    SteamExtensionItem(
                        appid=app_id,
                        name=specific_name,
                        description=specific_description,
                        action=specific_action,
                        ulaunched_last=ulaunched_last,
                        ulaunched_times=ulaunched_times
                    )
                )
        if "actions" not in cache.keys():
            cache["actions"] = {}
        if "rebuild-cache" not in cache["actions"].keys():
            cache["actions"]["rebuild-cache"] = {}
        ulaunched_last: datetime | None = None
        ulaunched_times: int = 0
        if "ulaunched-last" in cache["actions"]["rebuild-cache"].keys():
            ulaunched_last = datetime.strptime(
                str(cache["actions"]["rebuild-cache"]["ulaunched-last"]),
                "%Y-%m-%d %H:%M:%S"
            )
        if "ulaunched-times" in cache["actions"]["rebuild-cache"].keys():
            ulaunched_times = int(cache["actions"]["rebuild-cache"]["ulaunched-times"])
        items.append(SteamExtensionItem(
            name=get_lang_string(lang, language, "rebuild-cache"),
            non_steam=True,
            description=get_lang_string(lang, language, "rebuild-cache%d"),
            action="rebuild-cache",
            ulaunched_last=ulaunched_last,
            ulaunched_times=ulaunched_times
        ))
        search = search.strip().lower()
        if search == "":
            log.debug("Sorting items")
            items = sorted(items, key=lambda x: x.to_sort_string(manifest["sort-keys"]))
        else:
            log.debug(f"Searching items for fuzzy match of '{search}'")
            items = [item for item in items if all(word in item.to_search_string() for word in search.split())]
            items = sorted(items, key=lambda x: SequenceMatcher(
                None, x.to_search_string(), search
            ).ratio(), reverse=True)
        items = items[:max(10, len(items))]
    except Exception as err:
        items.insert(0, SteamExtensionItem.from_error(err))
    return items
