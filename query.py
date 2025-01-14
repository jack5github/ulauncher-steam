from const import DEFAULT_ICON, DIR_SEP, EXTENSION_PATH, get_logger
from datetime import datetime
from logging import Logger
from typing import Any, Literal

log: Logger = get_logger(__name__)


class SteamExtensionItem:
    """
    A class that represents an item to be displayed by the Steam extension.
    """

    def __init__(
        self,
        preferences: dict[str, Any],
        lang: dict[str, dict[str, str]],
        type: Literal["app", "nav", "action"],
        id: int | None = None,
        non_steam: bool = False,
        name: str | None = None,
        display_name: str | None = None,
        description: str | None = None,
        location: str | None = None,
        size_on_disk: int = 0,
        total_playtime: int = 0,
        icon: str | None = None,
        last_launched: datetime | None = None,
        times_launched: int = 0,
    ) -> None:
        """
        Initialises a new SteamExtensionItem instance.

        Args:
            preferences (dict[str, Any]): The preferences dictionary.
            lang (dict[str, dict[str, str]]): The language dictionary.
            type (Literal["app", "nav", "action"]): The type of the item.
            id (int | None, optional): The ID of the item, whether app ID or steamid64. Defaults to None.
            non_steam (bool, optional): Whether this is a non-Steam application. Defaults to False.
            name (str | None, optional): The name of the item, which may be an action ID in the case of navigations and actions. Defaults to None.
            display_name (str | None, optional): The display name of the item, not to be confused with get_name(). Defaults to None.
            description (str | None, optional): The description of the item, not to be confused with get_description(). Defaults to None.
            location (str | None, optional): The location of the item on disk. Defaults to None.
            size_on_disk (int, optional): The size of the item on disk in bytes. Defaults to 0.
            total_playtime (int, optional): The total playtime of the item in minutes. Defaults to 0.
            icon (str | None, optional): The path to the icon of the item, must include the extension path. If None, the default icon will be used. Defaults to None.
            last_launched (datetime | None, optional): The last time the item was launched. Defaults to None.
            times_launched (int, optional): The number of times the item has been launched. Defaults to 0.
        """
        self.preferences: dict[str, Any] = preferences
        self.lang: dict[str, dict[str, str]] = lang
        self.type: Literal["app", "nav", "action"] = type
        self.id: int | None = id
        self.non_steam: bool = non_steam
        self.name: str | None = name
        self.display_name: str | None = display_name
        self.description: str | None = description
        self.location: str | None = location
        self.size_on_disk: int = size_on_disk
        self.total_playtime: int = total_playtime
        self.icon: str = DEFAULT_ICON
        if icon is not None:
            if icon.startswith(EXTENSION_PATH):
                self.icon = icon
            else:
                log.error(
                    f"Icon path '{icon}' does not start with '{EXTENSION_PATH}', ignoring"
                )
        self.last_launched: datetime | None = last_launched
        self.times_launched: int = times_launched

    def __str__(self) -> str:
        """
        Returns a string representation of the SteamExtensionItem.

        Returns:
            str: The string representation of the SteamExtensionItem.
        """
        str_rep: str = self.get_name()
        description: str = self.get_description()
        if description != "":
            str_rep += f" --- {description}"
        return str_rep

    def get_name(self) -> str:
        """
        Returns the name of the SteamExtensionItem that can be safely displayed for and filtered through by the user.

        Returns:
            str: The name string of the SteamExtensionItem to display in uLauncher.
        """
        return (
            self.display_name
            if self.display_name is not None
            else (
                self.name
                if self.name is not None
                else get_lang_string(
                    self.lang, self.preferences["LANGUAGE_CODE"], "name_missing"
                )
            )
        )

    def get_description(self) -> str:
        """
        Returns the description of the SteamExtensionItem that can be safely displayed for and filtered through by the user.

        Returns:
            str: The description string of the SteamExtensionItem to display in uLauncher.
        """
        description: str = ""
        if self.type == "app":
            location_added: bool = False
            if self.total_playtime > 0:
                description += f"{self.total_playtime / 60:.1f} hrs"
            if self.last_launched is not None:
                if description != "":
                    description += " | "
                description += datetime.strftime(self.last_launched, "%b %d, %Y")
            if self.location is not None:
                if description != "":
                    description += " | "
                description += f"{self.location.lstrip(DIR_SEP).split(DIR_SEP)[0]}"
                location_added = True
            if self.size_on_disk > 0:
                if location_added:
                    if not description.endswith(":"):
                        description += ":"
                    description += " "
                elif description != "":
                    description += " | "
                if self.size_on_disk < 1000:
                    description += f"{self.size_on_disk} B"
                elif self.size_on_disk < 1000**2:
                    description += f"{self.size_on_disk / 1000:.2f} KB"
                elif self.size_on_disk < 1000**3:
                    description += f"{self.size_on_disk / 1000 ** 2:.2f} MB"
                elif self.size_on_disk < 1000**4:
                    description += f"{self.size_on_disk / 1000 ** 3:.2f} GB"
                else:
                    description += f"{self.size_on_disk / 1000 ** 4:.2f} TB"
        elif self.description is not None:
            description: str = self.description
        return description

    def to_sort_list(self) -> list[Any]:
        """
        Creates a list of the SteamExtensionItem's attributes that can be used for sorting. Attributes are selected using the SORT_KEYS preference.

        Returns:
            list[Any]: The list of the SteamExtensionItem's attributes.
        """
        sort_keys_str: str = self.preferences["SORT_KEYS"]
        sort_keys: list[str] = [key.strip() for key in sort_keys_str.split(",")]
        sort_list: list[Any] = []
        while len(sort_list) == 0:
            for sort_key in sort_keys:
                if sort_key == "type":
                    sort_list.append(
                        0 if self.type is "app" else 1 if self.type is "nav" else 2
                    )
                elif sort_key == "id":
                    sort_list.append(self.id if self.id is not None else float("inf"))
                elif sort_key == "non_steam":
                    sort_list.append(0 if self.non_steam else 1)
                elif sort_key == "name":
                    sort_list.append(
                        self.name.lower() if self.name is not None else "ÿÿ"
                    )
                elif sort_key == "display_name":
                    sort_list.append(
                        self.display_name.lower()
                        if self.display_name is not None
                        else "ÿÿ"
                    )
                elif sort_key == "description":
                    sort_list.append(
                        self.description.lower()
                        if self.description is not None
                        else "ÿÿ"
                    )
                elif sort_key == "location":
                    sort_list.append(
                        self.location.lower() if self.location is not None else "ÿÿ"
                    )
                elif sort_key == "size_on_disk":
                    sort_list.append(-self.size_on_disk)
                elif sort_key == "total_playtime":
                    sort_list.append(-self.total_playtime)
                elif sort_key == "icon":
                    sort_list.append(
                        self.icon.lower() if self.icon is not None else "ÿÿ"
                    )
                elif sort_key == "last_launched":
                    sort_list.append(
                        -datetime.timestamp(self.last_launched)
                        if self.last_launched is not None
                        else 0
                    )
                elif sort_key == "times_launched":
                    sort_list.append(-self.times_launched)
                else:
                    log.warning(f"Sort key '{sort_key}' not recognised")
            if len(sort_list) == 0:
                log.warning(
                    f"No valid sort key found in '{sort_keys_str}', defaulting to 'last_launched,total_playtime,name'"
                )
                sort_keys = ["last_launched", "total_playtime", "name"]
        return sort_list

    def get_action(self) -> str:
        """
        Returns the script action of the SteamExtensionItem. If the type is "app", the "steam://rungameid/{id}" action is returned, if the type is "nav", the item's name as a Steam protocol is returned. Otherwise, the item's name is returned. All actions are preceded by their type in uppercase, except for the "action" type.

        Returns:
            str: The script action of the SteamExtensionItem.
        """
        action: str = str(self.name)
        if self.type == "app":
            action = f"steam://rungameid/{self.id}"
        elif self.type == "nav":
            action = f"steam://{self.name}"
        else:
            return action
        action = f"{self.type.upper()}{action}"
        return action


def get_lang_string(
    lang: dict[str, dict[str, str]], language: str, key: str, strict: bool = False
) -> str:
    """
    Gets a string from the language dictionary, which is loaded from lang.json.

    Args:
        lang (dict[str, dict[str, str]]): The language dictionary.
        language (str): The desired language code.
        key (str): The string to retrieve from the language dictionary.
        strict (bool, optional): Whether to raise an exception if the key is not found. Defaults to False.

    Raises:
        KeyError: If the default language is not in the language dictionary.
        KeyError: If the desired key is not in the language dictionary, both for the desired and the default language.

    Returns:
        str: The string from the language dictionary, either from the desired or the default language.
    """
    from const import DEFAULT_LANGUAGE

    log.debug(f"Getting '{key}' for language '{language}' from lang.json")
    if language in lang.keys():
        if key in lang[language].keys():
            return str(lang[language][key])
    if DEFAULT_LANGUAGE not in lang.keys():
        log.error(f"Default language '{DEFAULT_LANGUAGE}' is not in lang.json")
        if strict:
            raise KeyError(f"Default language '{DEFAULT_LANGUAGE}' is not in lang.json")
        return key
    if key not in lang[DEFAULT_LANGUAGE].keys():
        log.warning(
            f"'{key}' is not in lang.json for '{language}' or '{DEFAULT_LANGUAGE}'"
        )
        if strict:
            raise KeyError(
                f"'{key}' is not in lang.json for '{language}' or '{DEFAULT_LANGUAGE}'"
            )
        return key
    log.warning(f"'{key}' is not in lang.json for '{language}'")
    return str(lang[DEFAULT_LANGUAGE][key])


def query_cache(
    keyword: str, preferences: dict[str, Any], search: str | None = None
) -> list[SteamExtensionItem]:
    """
    Queries the Steam extension cache for items that match the search, or if there is no search, sorts them based on the user's preferences.

    Args:
        keyword (str): The keyword that indicates what type of items are allowed to appear.
        preferences (dict[str, Any]): The preferences dictionary.
        search (str | None, optional): The search query. Defaults to None.

    Returns:
        list[SteamExtensionItem]: The list of SteamExtensionItems that match the criteria.
    """
    from cache import get_blacklist, load_cache
    from const import check_required_preferences, STEAM_NAVIGATIONS
    from difflib import SequenceMatcher
    from json import loads as json_loads
    from os.path import isfile

    check_required_preferences(preferences)
    if search is None:
        log.info("Querying Steam extension cache")
    else:
        log.info(f"Querying Steam extension cache with search '{search}'")
    cache: dict[str, Any] = load_cache()
    lang: dict[str, dict[str, str]] = {}
    try:
        with open(f"{EXTENSION_PATH}lang.json", "r", encoding="utf-8") as f:
            lang = json_loads(f.read())
    except Exception:
        log.error("Failed to read lang.json", exc_info=True)
    log.debug("Getting blacklists from preferences")
    app_blacklist: list[int] = get_blacklist("app", preferences)
    """
    friend_blacklist: list[int] = get_blacklist("friend", preferences)
    """
    items: list[SteamExtensionItem] = []

    def get_launches(info: dict[str, Any]) -> tuple[datetime | None, int]:
        """
        Returns the last time the app was launched and the number of times it has been launched from an item dictionary's values.

        Args:
            info (dict[str, Any]): The item dictionary.

        Returns:
            tuple[datetime | None, int]: The last time the app was launched and the number of times it has been launched.
        """
        from datetime import timezone

        last_launched: datetime | None = None
        last_launched_int: int | None = info.get("last_launched")
        if last_launched_int is not None:
            last_launched = datetime.fromtimestamp(last_launched_int, timezone.utc)
            # TODO: Implement basic timezone support?
            # last_launched = last_launched.astimezone()
        times_launched: int = info.get("times_launched", 0)
        return last_launched, times_launched

    if keyword in (preferences["KEYWORD"], preferences["KEYWORD_APPS"]):
        if "steam_apps" in cache.keys() and isinstance(cache["steam_apps"], dict):
            if not preferences["STEAM_FOLDER"].endswith(DIR_SEP):
                preferences["STEAM_FOLDER"] = f"{preferences['STEAM_FOLDER']}{DIR_SEP}"
            for app_id, app_info in cache["steam_apps"].items():
                app_id_int: int = int(app_id)
                try:
                    app_id_int = int(app_id)
                except Exception:
                    log.error(f"Invalid app ID '{app_id}'", exc_info=True)
                    continue
                if app_id_int in app_blacklist:
                    log.debug(f"Skipping blacklisted app ID {app_id_int}")
                    continue
                if not isinstance(app_info, dict):
                    log.error(
                        f"Invalid dictionary for Steam app ID {app_id_int}: {app_info}",
                        exc_info=True,
                    )
                    continue
                name: str = app_info["name"]
                location: str | None = app_info.get("install_dir")
                if location is not None:
                    location = f"{preferences['STEAM_FOLDER']}steamapps{DIR_SEP}common{DIR_SEP}{location}"
                size_on_disk: int = app_info.get("size_on_disk", 0)
                display_name: str | None = None
                if location is not None or size_on_disk > 0:
                    display_name = get_lang_string(
                        lang, preferences["LANGUAGE_CODE"], f"launch_%a"
                    ).replace("%a", name)
                else:
                    display_name = get_lang_string(
                        lang, preferences["LANGUAGE_CODE"], f"install_%a"
                    ).replace("%a", name)
                total_playtime: int = app_info.get("total_playtime", 0)
                icon: str | None = None
                icon_path: str = f"{EXTENSION_PATH}images{DIR_SEP}apps{DIR_SEP}{app_id_int}.jpg"
                if isfile(icon_path):
                    icon = icon_path
                last_launched: datetime | None
                times_launched: int
                last_launched, times_launched = get_launches(app_info)
                items.append(
                    SteamExtensionItem(
                        preferences,
                        lang,
                        type="app",
                        id=app_id_int,
                        name=name,
                        display_name=display_name,
                        location=location,
                        size_on_disk=size_on_disk,
                        total_playtime=total_playtime,
                        icon=icon,
                        last_launched=last_launched,
                        times_launched=times_launched,
                    )
                )
        if "non_steam_apps" in cache.keys() and isinstance(cache["non_steam_apps"], dict):
            for app_id, app_info in cache["non_steam_apps"].items():
                app_id_int: int
                try:
                    app_id_int = int(app_id)
                except Exception:
                    log.error(f"Invalid app ID '{app_id}'", exc_info=True)
                    continue
                if app_id_int in app_blacklist:
                    log.debug(f"Skipping blacklisted app ID {app_id_int}")
                    continue
                if not isinstance(app_info, dict):
                    log.error(
                        f"Invalid dictionary for non-Steam app ID {app_id_int}: {app_info}",
                        exc_info=True,
                    )
                name: str = app_info["name"]
                non_steam_display_name: str = get_lang_string(
                    lang, preferences["LANGUAGE_CODE"], f"launch_%a"
                ).replace("%a", name)
                location: str | None = app_info.get("exe")
                size_on_disk: int = app_info.get("size_on_disk", 0)
                last_launched: datetime | None
                times_launched: int
                last_launched, times_launched = get_launches(app_info)
                items.append(
                    SteamExtensionItem(
                        preferences,
                        lang,
                        type="app",
                        id=app_id_int,
                        non_steam=True,
                        name=name,
                        display_name=non_steam_display_name,
                        location=location,
                        size_on_disk=size_on_disk,
                        last_launched=last_launched,
                        times_launched=times_launched,
                    )
                )
    if keyword in (preferences["KEYWORD"], preferences["KEYWORD_APPS"]):
        if "steam_navs" not in cache.keys() or not isinstance(cache["steam_navs"], dict):
            log.warning("cache.json does not contain valid 'steam_navs' key")
            cache["steam_navs"] = {}
        for name in STEAM_NAVIGATIONS:
            nav_display_name: str = get_lang_string(
                lang, preferences["LANGUAGE_CODE"], name
            )
            description: str | None = None
            try:
                description = get_lang_string(
                    lang, preferences["LANGUAGE_CODE"], f"{name}%d", strict=True
                )
            except KeyError:
                pass
            ids: list[int | None] = [None]
            if "%a" in name:
                if "steam_apps" in cache.keys() and isinstance(
                    cache["steam_apps"], dict
                ):
                    ids = [int(app_id) for app_id in cache["steam_apps"].keys()]
                else:
                    log.warning(
                        "cache.json does not contain any valid Steam apps", exc_info=True)
                    ids = []
            elif keyword == preferences["KEYWORD_APPS"]:
                continue
            for id in ids:
                if id in app_blacklist:
                    log.debug(f"Skipping blacklisted app ID {id}")
                    continue
                id_name: str = name.replace("%a", str(id))
                id_display_name: str = nav_display_name
                id_description: str | None = description
                icon: str | None = None
                if "%a" in name:
                    app_name: str = str(id)
                    if "name" in cache["steam_apps"][str(id)].keys():
                        app_name = str(cache["steam_apps"][str(id)]["name"])
                    id_display_name = nav_display_name.replace("%a", app_name)
                    if id_description is not None:
                        id_description = id_description.replace("%a", app_name)
                    icon_path: str = f"{EXTENSION_PATH}images{DIR_SEP}apps{DIR_SEP}{id}.jpg"
                    if isfile(icon_path):
                        icon = icon_path
                last_launched: datetime | None = None
                times_launched: int = 0
                if id_name in cache["steam_navs"].keys() and isinstance(
                    cache["steam_navs"][id_name], dict
                ):
                    last_launched, times_launched = get_launches(
                        cache["steam_navs"][id_name]
                    )
                items.append(
                    SteamExtensionItem(
                        preferences,
                        lang,
                        type="nav",
                        id=id,
                        name=id_name,
                        display_name=id_display_name,
                        description=id_description,
                        icon=icon,
                        last_launched=last_launched,
                        times_launched=times_launched,
                    )
                )
    if keyword in (preferences["KEYWORD"], preferences["KEYWORD_ACTIONS"]):
        for name in ("update_cache", "clear_cache", "rebuild_cache"):
            items.append(
                SteamExtensionItem(
                    preferences,
                    lang,
                    type="action",
                    name=name,
                    display_name=get_lang_string(lang, preferences["LANGUAGE_CODE"], name),
                    description=get_lang_string(
                        lang, preferences["LANGUAGE_CODE"], f"{name}%d"
                    ),
                )
            )
    if search is None:
        search = ""
    else:
        search = search.strip().lower()
    if search == "":
        items = sorted(items, key=lambda x: x.to_sort_list())
    else:
        log.debug(f"Searching items for fuzzy match of '{search}'")
        items = [
            item
            for item in items
            if all(
                word in f"{item.get_name().lower()} {item.get_description().lower()}"
                for word in search.split()
            )
        ]
        items = sorted(
            items,
            key=lambda x: [
                x.type == "app",
                SequenceMatcher(None, x.get_name().lower(), search).ratio(),
                SequenceMatcher(None, x.get_description().lower(), search).ratio(),
            ],
            reverse=True,
        )
    max_items_str: str = preferences["MAX_ITEMS"]
    max_items: int = 10
    try:
        max_items = int(max_items_str)
        if max_items <= 0:
            max_items = 10
            raise ValueError()
    except Exception:
        log.warning(f"Maximum items from preferences '{max_items_str}' is invalid")
    items = items[: min(max_items, len(items))]
    if len(items) == 0:
        items.append(
            SteamExtensionItem(
                preferences,
                lang,
                type="action",
                name="no_results",
                display_name=get_lang_string(
                    lang, preferences["LANGUAGE_CODE"], "no_results"
                ),
                description=get_lang_string(
                    lang, preferences["LANGUAGE_CODE"], f"no_results%d"
                ),
            )
        )
    return items


if __name__ == "__main__":
    from const import get_preferences_from_env
    import sys

    preferences: dict[str, Any] = get_preferences_from_env()
    print(
        "\n".join(
            f"{index + 1}. {item}"
            for index, item in enumerate(
                query_cache(
                    preferences["KEYWORD"],
                    preferences,
                    search=" ".join(sys.argv[1:]),
                )
            )
        )
    )
