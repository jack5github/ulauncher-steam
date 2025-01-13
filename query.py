from const import DEFAULT_LANGUAGE, EXTENSION_PATH, get_logger, STEAM_NAVIGATIONS
from datetime import datetime
from logging import Logger
from os.path import isfile
from typing import Any

log: Logger = get_logger(__name__)


class SteamExtensionItem:
    """
    A class that represents an item to be displayed by the Steam extension.
    """

    def __init__(
        self,
        preferences: dict[str, Any],
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
            preferences (dict[str, Any]): The preferences dictionary.
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
        self.preferences: dict[str, Any] = preferences
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
        if "RESULT_TINY_REPR" in self.preferences.keys() and bool(
            self.preferences["RESULT_TINY_REPR"]
        ):
            return f"({repr(self.appid)}, name={repr(self.name)}, non={repr(self.non_steam)}, inst={repr(self.installed)}, desc={repr(self.description)}, act={repr(self.action)}, ulast={repr(self.ulaunched_last)}, utimes={repr(self.ulaunched_times)}, err={self.is_error})"
        return f"SteamExtensionItem(appid={repr(self.appid)}, name={repr(self.name)}, non_steam={repr(self.non_steam)}, installed={repr(self.installed)}, description={repr(self.description)}, action={repr(self.action)}, ulaunched_last={repr(self.ulaunched_last)}, ulaunched_times={repr(self.ulaunched_times)}, is_error={self.is_error})"

    @classmethod
    def from_error(
        cls, err: Exception, preferences: dict[str, Any]
    ) -> "SteamExtensionItem":
        """
        Creates a new SteamExtensionItem instance from an error.

        Args:
            err (Exception): The error.
            preferences (dict[str, Any]): The preferences dictionary.

        Returns:
            SteamExtensionItem: A new SteamExtensionItem instance.
        """
        log.error(f"{err.__class__.__name__}: {err}", exc_info=True)
        return SteamExtensionItem(
            preferences,
            name=err.__class__.__name__,
            description=str(err),
            is_error=True,
        )

    def to_result_dict(self) -> dict[str, Any]:
        """
        Converts the SteamExtensionItem instance to a dictionary representation for uLauncher, which after minimal adjustments can be passed into the uLauncher API.

        Returns:
            dict[str, Any]: The dictionary representation.
        """
        from const import DIR_SEP

        icon_file: str = "images/icon.png"
        if isfile(f"{EXTENSION_PATH}images{DIR_SEP}apps{DIR_SEP}{self.appid}.jpg"):
            icon_file = f"images/apps/{self.appid}.jpg"
        result_dict: dict[str, Any] = {
            "icon": icon_file,
            "name": self.name if self.name is not None else str(self.appid),
            "description": self.description if self.description is not None else "",
            "on_enter": {
                "class": (
                    "ExtensionCustomAction"
                    if self.action is not None and self.action == "rebuild_cache"
                    else (
                        "RunScriptAction"
                        if self.appid is not None or self.action is not None
                        else "HideWindowAction"
                    )
                )
            },
        }
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
            if key == "appid":
                sort_string += self.appid if self.appid is not None else ""
            elif key == "name":
                sort_string += self.name if self.name is not None else ""
            elif key == "description":
                sort_string += self.description if self.description is not None else ""
            elif key == "non_steam":
                sort_string += str(self.non_steam)
            elif key == "ulaunched_last":
                sort_string += (
                    str(self.ulaunched_last.timestamp()).zfill(20)
                    if self.ulaunched_last is not None
                    else ""
                )
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
        return f"{self.name if self.name is not None else ''}{self.description if self.description is not None else ''}".lower()


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
    preferences: dict[str, Any], search: str | None = None
) -> list[SteamExtensionItem]:
    """
    The main code that is run when the Steam extension keyword is entered into uLauncher. This function looks for Steam and non-Steam apps and menus using cache.json and returns a list of SteamExtensionItem instances. It is designed to be run on its own without needing to import the uLauncher API.

    Args:
        preferences (dict[str, Any]): The preferences dictionary, a set of variables that are passed into the extension from uLauncher's extension settings.
        search (str | None, optional): The search string entered after the Steam extension keyword, or None if no search is provided. Defaults to None.

    Returns:
        list[SteamExtensionItem]: A list of SteamExtensionItem instances.
    """
    from cache import load_cache
    from const import check_required_preferences
    from difflib import SequenceMatcher
    from json import loads as json_loads

    log.info(f"Triggering Steam extension event with search '{search}'")
    items: list[SteamExtensionItem] = []
    populate_items: bool = True
    try:
        check_required_preferences(preferences)
        if populate_items:
            log.debug("Loading lang.json")
            language: str = DEFAULT_LANGUAGE
            if "LANGUAGE_CODE" in preferences.keys():
                language = preferences["LANGUAGE_CODE"]
            lang: dict[str, Any] = {}
            try:
                with open(f"{EXTENSION_PATH}lang.json", "r", encoding="utf-8") as f:
                    lang = json_loads(f.read())
            except Exception as err:
                items.insert(0, SteamExtensionItem.from_error(err, preferences))
                populate_items = False
            if language not in lang.keys():
                items.insert(
                    0,
                    SteamExtensionItem.from_error(
                        KeyError(f"Language '{language}' not found in lang.json"),
                        preferences,
                    ),
                )
                language = DEFAULT_LANGUAGE
        if populate_items:
            cache: dict[str, Any] = load_cache()
            steam_apps: list[SteamExtensionItem] = []
            if "steam_apps" in cache.keys():
                log.debug("Iterating through Steam apps")
                if not isinstance(cache["steam_apps"], dict):
                    items.insert(
                        0,
                        SteamExtensionItem.from_error(
                            TypeError("'steam_apps' in cache.json is not a dictionary"),
                            preferences,
                        ),
                    )
                    cache["steam_apps"] = {}
                for appid, appinfo in cache["steam_apps"].items():
                    if not isinstance(appinfo, dict):
                        items.insert(
                            0,
                            SteamExtensionItem.from_error(
                                TypeError(
                                    f"'steam_apps' app ID {appid} in cache.json is not a dictionary"
                                ),
                                preferences,
                            ),
                        )
                        continue
                    name: str = appid
                    installed: bool = False
                    ulaunched_last: datetime | None = None
                    ulaunched_times: int = 0
                    if "name" in appinfo.keys():
                        name = str(appinfo["name"])
                    if "installed" in appinfo.keys() and appinfo["installed"]:
                        installed = True
                    if "last_launched" in appinfo.keys():
                        ulaunched_last = datetime.strptime(
                            str(appinfo["last_launched"]), "%Y-%m-%d %H:%M:%S"
                        )
                    if "times_launched" in appinfo.keys():
                        ulaunched_times = int(appinfo["times_launched"])
                    steam_apps.append(
                        SteamExtensionItem(
                            preferences,
                            appid=appid,
                            name=name,
                            installed=installed,
                            ulaunched_last=ulaunched_last,
                            ulaunched_times=ulaunched_times,
                        )
                    )
                items.extend(steam_apps)
            if "non_steam_apps" in cache.keys():
                log.debug("Iterating through non-Steam apps")
                if not isinstance(cache["non_steam_apps"], dict):
                    items.insert(
                        0,
                        SteamExtensionItem.from_error(
                            TypeError(
                                "'non_steam_apps' in cache.json is not a dictionary"
                            ),
                            preferences,
                        ),
                    )
                    cache["non_steam_apps"] = {}
                for appid, appinfo in cache["non_steam_apps"].items():
                    if not isinstance(appinfo, dict):
                        items.insert(
                            0,
                            SteamExtensionItem.from_error(
                                TypeError(
                                    f"'non_steam_apps' app ID {appid} in cache.json is not a dictionary"
                                ),
                                preferences,
                            ),
                        )
                        continue
                    name: str = appid
                    ulaunched_last: datetime | None = None
                    ulaunched_times: int = 0
                    if "name" in appinfo.keys():
                        name = str(appinfo["name"])
                    if "last_launched" in appinfo.keys():
                        ulaunched_last = datetime.strptime(
                            str(appinfo["last_launched"]), "%Y-%m-%d %H:%M:%S"
                        )
                    if "times_launched" in appinfo.keys():
                        ulaunched_times = int(appinfo["times_launched"])
                    items.append(
                        SteamExtensionItem(
                            preferences,
                            appid=appid,
                            name=name,
                            non_steam=True,
                            ulaunched_last=ulaunched_last,
                            ulaunched_times=ulaunched_times,
                        )
                    )
            # Navigation
            # https://developer.valvesoftware.com/wiki/Steam_browser_protocol
            log.debug("Iterating through Steam navigations")
            if "steam_navs" not in cache.keys():
                cache["steam_navs"] = {}
            if not isinstance(cache["steam_navs"], dict):
                items.insert(
                    0,
                    SteamExtensionItem.from_error(
                        TypeError("'steam_navs' in cache.json is not a dictionary"),
                        preferences,
                    ),
                )
                cache["steam_navs"] = {}
            navigations: list[str] = STEAM_NAVIGATIONS.copy()
            for navigation in navigations:
                log.debug(f"Adding navigation '{navigation}'")
                nav_name: str = navigation
                nav_action: str = f"steam steam://{navigation}"
                try:
                    nav_name = get_lang_string(lang, language, navigation)
                except KeyError as err:
                    items.insert(0, SteamExtensionItem.from_error(err, preferences))
                nav_description: str | None = None
                try:
                    nav_description = get_lang_string(lang, language, f"{navigation}%d")
                except KeyError as err:
                    pass
                if "%g" not in navigation:
                    ulaunched_last: datetime | None = None
                    ulaunched_times: int = 0
                    if (
                        "steam_navs" in cache.keys()
                        and isinstance(cache["steam_navs"], dict)
                        and navigation in cache["steam_navs"].keys()
                        and isinstance(cache["steam_navs"][navigation], dict)
                    ):
                        if "last_launched" in appinfo.keys():
                            ulaunched_last = datetime.strptime(
                                str(appinfo["last_launched"]), "%Y-%m-%d %H:%M:%S"
                            )
                        if "times_launched" in appinfo.keys():
                            ulaunched_times = int(appinfo["times_launched"])
                    items.append(
                        SteamExtensionItem(
                            preferences,
                            name=nav_name,
                            description=nav_description,
                            action=nav_action,
                            ulaunched_last=ulaunched_last,
                            ulaunched_times=ulaunched_times,
                        )
                    )
                    continue
                log.debug(f"Iterating through Steam apps for navigation '{navigation}'")
                for steam_app in steam_apps:
                    app_id: str = steam_app.appid  # type: ignore
                    app_name: str = steam_app.name  # type: ignore
                    if app_id is None or app_name is None:
                        items.insert(
                            0,
                            SteamExtensionItem.from_error(
                                RuntimeError(
                                    f"An in-memory Steam app has a missing app ID or name: ({app_id}, {repr(app_name)})"
                                ),
                                preferences,
                            ),
                        )
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
                            preferences,
                            appid=app_id,
                            name=specific_name,
                            description=specific_description,
                            action=specific_action,
                            ulaunched_last=ulaunched_last,
                            ulaunched_times=ulaunched_times,
                        )
                    )
            if "actions" not in cache.keys():
                cache["actions"] = {}
            if "rebuild_cache" not in cache["actions"].keys():
                cache["actions"]["rebuild_cache"] = {}
            ulaunched_last: datetime | None = None
            ulaunched_times: int = 0
            if "last_launched" in cache["actions"]["rebuild_cache"].keys():
                ulaunched_last = datetime.strptime(
                    str(cache["actions"]["rebuild_cache"]["last_launched"]),
                    "%Y-%m-%d %H:%M:%S",
                )
            if "times_launched" in cache["actions"]["rebuild_cache"].keys():
                ulaunched_times = int(
                    cache["actions"]["rebuild_cache"]["times_launched"]
                )
            items.append(
                SteamExtensionItem(
                    preferences,
                    name=get_lang_string(lang, language, "rebuild_cache"),
                    non_steam=True,
                    description=get_lang_string(lang, language, "rebuild_cache%d"),
                    action="rebuild_cache",
                    ulaunched_last=ulaunched_last,
                    ulaunched_times=ulaunched_times,
                )
            )
            if search is None:
                search = ""
            else:
                search = search.strip().lower()
            if search == "":
                log.debug("Sorting items")
                items = sorted(
                    items, key=lambda x: x.to_sort_string(preferences["SORT_KEYS"])
                )
            else:
                log.debug(f"Searching items for fuzzy match of '{search}'")
                items = [
                    item
                    for item in items
                    if all(word in item.to_search_string() for word in search.split())
                ]
                items = sorted(
                    items,
                    key=lambda x: SequenceMatcher(
                        None, x.to_search_string(), search
                    ).ratio(),
                    reverse=True,
                )
    except Exception as err:
        items.insert(0, SteamExtensionItem.from_error(err, preferences))
    max_items: int = 10
    try:
        max_items = int(preferences["MAX_ITEMS"])
        if max_items <= 0:
            raise ValueError()
    except ValueError:
        items.insert(
            0,
            SteamExtensionItem.from_error(
                ValueError("Maximum items is not a valid positive integer"), preferences
            ),
        )
    if len(items) >= 1:
        items = items[: min(max_items, len(items))]
    else:
        try:
            items.append(
                SteamExtensionItem(
                    preferences,
                    name=get_lang_string(lang, language, "no_results"),
                    description=get_lang_string(lang, language, "no_results%d"),
                    is_error=True,
                )
            )
        except KeyError as err:
            items.append(SteamExtensionItem.from_error(err, preferences))
    return items


if __name__ == "__main__":
    from configparser import ConfigParser
    import sys

    preferences_file = ConfigParser()
    preferences_file.read(".env")
    print(
        "\n".join(
            f"{index + 1}. {item}"
            for index, item in enumerate(
                steam_extension_event(
                    preferences={
                        k.upper(): v for k, v in preferences_file.items("PREFERENCES")
                    },
                    search=" ".join(sys.argv[1:]),
                )
            )
        )
    )
