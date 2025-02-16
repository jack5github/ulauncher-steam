from const import DEFAULT_ICON, DIR_SEP, EXTENSION_PATH, get_logger
from datetime import datetime, timezone
from logging import Logger
from typing import Any, Literal

log: Logger = get_logger(__name__)

ITEM_TYPES: tuple[str, ...] = ("app", "friend", "nav", "action")


class SteamExtensionItem:
    """
    A class that represents an item to be displayed by the Steam extension.
    """

    def __init__(
        self,
        preferences: dict[str, Any],
        lang: dict[str, dict[str, str]],
        type: Literal["app", "friend", "nav", "action"],
        id: int | None = None,
        non_steam: bool = False,
        name: str | None = None,
        display_name: str | None = None,
        real_name: str | None = None,
        description: str | None = None,
        created: datetime | None = None,
        location: str | None = None,
        size: int = 0,
        playtime: int = 0,
        icon: str | None = None,
        updated: datetime | None = None,
        launched: datetime | None = None,
        times: int = 0,
    ) -> None:
        """
        Initialises a new SteamExtensionItem instance.

        Args:
            preferences (dict[str, Any]): The preferences dictionary.
            lang (dict[str, dict[str, str]]): The language dictionary.
            type (Literal["app", "friend", "nav", "action"]): The type of the item.
            id (int | None, optional): The ID of the item, whether app ID or steamID64. Defaults to None.
            non_steam (bool, optional): Whether this is a non-Steam application. Defaults to False.
            name (str | None, optional): The name of the item, which may be an action ID in the case of navigations and actions. Defaults to None.
            display_name (str | None, optional): The display name of the item, not to be confused with get_name(). Defaults to None.
            real_name (str | None, optional): The real name of the friend, not to be confused with get_name(). Defaults to None.
            description (str | None, optional): The description of the item, not to be confused with get_description(). Defaults to None.
            created (datetime | None, optional): The time the item was created on the Steam servers. Defaults to None.
            location (str | None, optional): The location of the item on disk. Defaults to None.
            size (int, optional): The size of the item on disk in bytes. Defaults to 0.
            playtime (int, optional): The total playtime of the item in minutes. Defaults to 0.
            icon (str | None, optional): The path to the icon of the item, must include the extension path. If None, the default icon will be used. Defaults to None.
            updated (datetime | None, optional): The last time the item was updated. Defaults to None.
            launched (datetime | None, optional): The last time the item was launched. Defaults to None.
            times (int, optional): The number of times the item has been launched. Defaults to 0.
        """
        self.preferences: dict[str, Any] = preferences
        self.lang: dict[str, dict[str, str]] = lang
        self.type: Literal["app", "friend", "nav", "action"] = type
        self.id: int | None = id
        self.non_steam: bool = non_steam
        self.name: str | None = name
        self.display_name: str | None = display_name
        self.real_name: str | None = real_name
        self.description: str | None = description
        self.created: datetime | None = created
        self.location: str | None = location
        self.size: int = size
        self.playtime: int = playtime
        self.icon: str = DEFAULT_ICON
        if icon is not None:
            if icon.startswith(EXTENSION_PATH):
                self.icon = icon
            else:
                log.error(
                    f"Icon path '{icon}' does not start with '{EXTENSION_PATH}', ignoring"
                )
        self.updated: datetime | None = updated
        self.launched: datetime | None = launched
        self.times: int = times

    def __str__(self) -> str:
        """
        Returns a string representation of the SteamExtensionItem.

        Returns:
            str: The string representation of the SteamExtensionItem.
        """
        if (
            not "ITEM_REPR" in self.preferences.keys()
            or self.preferences["ITEM_REPR"] != "true"
        ):
            str_rep: str = self.get_name()
            description: str = self.get_description()
            if description != "":
                str_rep += f" --- {description}"
            return str_rep
        return str(
            {
                k: v
                for k, v in {
                    "ext_name": self.get_name(),
                    "ext_description": self.get_description(),
                    "ext_action": self.get_action(),
                    **self.__dict__,
                }.items()
                if not k.startswith("_") and k not in ("preferences", "lang")
            }
        )

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
                    self.lang, self.preferences["LANGUAGE"], "name_missing"
                )
            )
        )

    def get_description(self) -> str:
        """
        Returns the description of the SteamExtensionItem that can be safely displayed for and filtered through by the user.

        Returns:
            str: The description string of the SteamExtensionItem to display in uLauncher.
        """
        from pathlib import Path

        description: str = ""

        def add_divider() -> None:
            nonlocal description

            if description != "":
                description += " | "

        if self.type == "app":
            location_added: bool = False
            if self.playtime > 0:
                description += f"{self.playtime / 60:.1f} hrs"
            if self.launched is not None:
                add_divider()
                description += datetime.strftime(self.launched, "%b %d, %Y")
            if self.location is not None:
                add_divider()
                location_str: str = DIR_SEP.join(
                    self.location.split(f"{DIR_SEP}steamapps{DIR_SEP}")[0].split(
                        DIR_SEP
                    )[:-1]
                )
                if location_str.endswith(f"{DIR_SEP}.steam"):
                    location_str = DIR_SEP.join(location_str.split(DIR_SEP)[:-1])
                if Path(location_str) == Path("~").expanduser():
                    location_str = "/"
                description += location_str
                location_added = True
            if self.size > 0:
                if location_added:
                    if not description.endswith(":"):
                        description += ":"
                    description += " "
                else:
                    add_divider()
                if self.size < 1000:
                    description += f"{self.size} B"
                elif self.size < 1000**2:
                    description += f"{self.size / 1000:.2f} KB"
                elif self.size < 1000**3:
                    description += f"{self.size / 1000 ** 2:.2f} MB"
                elif self.size < 1000**4:
                    description += f"{self.size / 1000 ** 3:.2f} GB"
                else:
                    description += f"{self.size / 1000 ** 4:.2f} TB"
            add_divider()
            description += str(self.id)
        elif self.type == "friend":
            if self.real_name is not None and self.preferences["SHOW_REAL"] in (
                "all",
                "onlyNames",
            ):
                description += self.real_name
            if self.location is not None and self.preferences["SHOW_REAL"] in (
                "all",
                "onlyLocations",
            ):
                add_divider()
                description += self.location
            add_divider()
            description += str(self.id)
        elif self.description is not None:
            description = self.description
        return description

    def to_sort_list(self) -> tuple[float, int, str]:
        """
        Creates a list of the SteamExtensionItem's attributes that can be used for sorting when a search string is not specified.

        Returns:
            tuple[float, int, str]: The parameterised list of the SteamExtensionItem's attributes.
        """
        return (
            -datetime.timestamp(self.launched) if self.launched is not None else 0,
            -self.playtime,
            self.name.lower() if self.name is not None else "ÿÿ",
        )

    def get_action(self) -> str:
        """
        Returns the script action of the SteamExtensionItem. If the type is "app", the "steam://rungameid/{id}" action is returned. If the type is "friend", the item's steamID64 is returned. If the type is "nav", the action is returned as is. Otherwise, the item's name is returned. All actions that are not of the "nav" or "action" types are preceded by their type in uppercase.

        Returns:
            str: The script action of the SteamExtensionItem.
        """
        action: str = str(self.name)
        if self.type == "app":
            action = f"steam://rungameid/{self.id}"
        elif self.type == "friend":
            action = str(self.id)
        elif self.type in ("nav", "action"):
            for modifier in ("%a", "%f"):
                action = action.replace(modifier, str(self.id))
            return action
        action = f"{self.type.upper()}{action}"
        return action


def get_lang_string(
    lang: dict[str, dict[str, str]], language: str, key: str, strict: bool = False
) -> str:
    """
    Gets a string from the language dictionary, which is loaded from lang.csv. The language file is organised into rows for each key, with the first column being "key" and the other columns being ISO 639-1 language code-specific translations.

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

    if key in lang.keys():
        if language in lang[key].keys():
            return str(lang[key][language])
        if DEFAULT_LANGUAGE in lang[key].keys():
            return str(lang[key][DEFAULT_LANGUAGE])
        if strict:
            raise KeyError(
                f"'{key}' is not in lang.csv for '{language}' or '{DEFAULT_LANGUAGE}'"
            )
        log.warning(
            f"'{key}' is not in lang.csv for '{language}' or '{DEFAULT_LANGUAGE}'"
        )
        return key
    if strict:
        raise KeyError(f"'{key}' is not in lang.csv for '{language}'")
    log.warning(f"'{key}' is not in lang.csv for '{language}'")
    return key


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Converts a UTC timestamp to a local datetime object.

    Args:
        timestamp (int): The timestamp to convert.

    Returns:
        datetime: The datetime object.
    """
    from datetime import timedelta
    from time import gmtime, localtime, mktime

    date = datetime.fromtimestamp(timestamp, timezone.utc)
    offset: timedelta = timedelta(seconds=mktime(localtime()) - mktime(gmtime()))
    date += offset
    return date


def timestamp_to_datetime_from_dict(info: dict[str, Any], key: str) -> datetime | None:
    """
    Converts a UTC timestamp in a dictionary to a datetime object to a local datetime object.

    Args:
        info (dict[str, Any]): The dictionary theoretically containing the timestamp.
        key (str): The key of the timestamp in the dictionary.

    Returns:
        datetime | None: The datetime object, or None if the timestamp is not found.
    """

    timestamp: int | None = info.get(key)
    return timestamp_to_datetime(timestamp) if timestamp is not None else None


def get_launches(info: dict[str, Any]) -> tuple[datetime | None, int]:
    """
    Returns the last time an item was launched and the number of times it has been launched from an item dictionary's value for the key "launched", which is in either one of the formats "TIMESTAMP" or "TIMESTAMPxTIMES".

    Args:
        info (dict[str, Any]): The item dictionary.

    Returns:
        tuple[datetime | None, int]: The last time the item was launched and the number of times it has been launched.
    """
    launched_str: str | int | None = info.get("launched")
    if launched_str is None:
        return None, 0
    if not isinstance(launched_str, str):  # int
        launched_str = str(launched_str)
    launched_split: list[str] = launched_str.split("x")
    if len(launched_split) >= 3:
        log.error(f"Invalid launched value '{launched_str}'")
        return None, 0
    launched_ints: list[int]
    try:
        launched_ints = [int(num) for num in launched_split]
    except ValueError:
        log.error(f"Invalid launched value '{launched_str}'")
        return None, 0
    launched: datetime | None = timestamp_to_datetime(launched_ints[0])
    times: int = launched_ints[1] if len(launched_ints) == 2 else 0
    return launched, times


"""
A dictionary of metrics used when sorting items based on a search query and their multipliers.
"""
# TODO: Add metric for how early each word appears in the individual words of the name
ITEM_METRIC_MULTS: dict[str, float] = {
    "type": 0.924256,  # The ease-of-use of the item type
    "name-fuzzy-index": 0.196592,  # How early fuzzy word matches appear in the name
    "name-fuzzy-order": 0.177762,  # Whether fuzzy word matches are in order in the name
    "name-exact-index": 0.051574,  # How early exact word matches appear in the name
    "name-exact-order": 0.047850,  # Whether exact word matches are in order in the name
    "name-length": 0.282486,  # The shortness of the name length
    "name-chars": 0.297724,  # The alphabetical ordering of the name
    "desc-fuzzy": 1.0,  # Whether fuzzy word matches are in the description
    "desc-length": 0.379305,  # The shortness of the description length
    "installed": 0.241787,  # Whether the item is installed
    "launched": 0.604697,  # The last time the item was launched
    "times": 0.073986,  # The number of times the item has been launched
}


def get_item_metrics(
    item: SteamExtensionItem,
    split_search: list[str],
    oldest_launched: datetime | None,
    most_times: int,
    now: datetime,
) -> dict[str, float]:
    """
    Gets the metrics of an item based on various attributes scaled between 0 and 1, used when sorting items based on a search query. The lower the metric, the more impactful it is when sorting.

    Args:
        item (SteamExtensionItem): The item to get the metrics of.
        split_search (list[str]): The list of words in the search query.
        oldest_launched (datetime | None): The oldest launch time of an item.
        most_times (int): The most times an item has been launched.
        now (datetime): The current datetime.

    Returns:
        dict[str, float]: The list of metrics.
    """
    from re import Match as ReMatch, search as re_search, sub as re_sub

    metrics: dict[str, float] = {k: 0.0 for k in ITEM_METRIC_MULTS.keys()}
    metrics["type"] = ITEM_TYPES.index(item.type) / (len(ITEM_TYPES) - 1)
    if item.type == "app" and item.size == 0 and item.location is None:
        metrics["installed"] = 1.0
    if oldest_launched is not None and item.launched is not None:
        metrics["launched"] = max(
            (now - item.launched).days / (now - oldest_launched).days, 0
        )
    else:
        metrics["launched"] = 1.0
    if most_times >= 1:
        metrics["times"] = item.times / most_times
    else:
        metrics["times"] = 1.0
    name: str = re_sub(r"[^a-z0-9 ]", " ", item.get_name().lower())
    metrics["name-length"] = min(len(name) - 1, 100) / 100
    metrics["name-chars"] = sum(ord(char) - 32 for char in name[:100]) / sum(
        ord("z") - 32 for _ in range(100)
    )
    description: str = re_sub(r"[^a-z0-9 ]", " ", item.get_description().lower())
    metrics["desc-length"] = max(min(len(description) - 1, 100), 0) / 100
    biggest_word_len: int = max(len(word) for word in split_search)
    previous_fuzzy_index: int | None = None
    previous_exact_index: int | None = None
    for word in split_search:
        fuzzy_index: int = name.find(word)
        if fuzzy_index != -1:
            word_len_factor: float = (
                (len(word) - 1) / (biggest_word_len - 1) if biggest_word_len >= 2 else 0
            )
            metrics["name-fuzzy-index"] += (
                (fuzzy_index / (len(name) - 1))  # Position of the word
                + word_len_factor  # Length of the word
            ) / 2
            if previous_fuzzy_index is not None and fuzzy_index < previous_fuzzy_index:
                metrics["name-fuzzy-order"] += 1.0
            previous_fuzzy_index = fuzzy_index
            exact_match: ReMatch | None = re_search(f"\\b{word}\\b", name)
            if exact_match is not None:
                metrics["name-exact-index"] += (
                    (exact_match.start() / (len(name) - 1))  # Position of the word
                    + word_len_factor  # Length of the word
                ) / 2
                if (
                    previous_exact_index is not None
                    and exact_match.start() < previous_exact_index
                ):
                    metrics["name-exact-order"] += 1.0
                previous_exact_index = exact_match.start()
            else:
                metrics["name-exact-index"] += 1.0
                metrics["name-exact-order"] += 1.0
        else:
            metrics["name-fuzzy-index"] += 1.0
            metrics["name-fuzzy-order"] += 1.0
            metrics["name-exact-index"] += 1.0
            metrics["name-exact-order"] += 1.0
            previous_fuzzy_index = -1
            previous_exact_index = -1
        fuzzy_index = description.find(word)
        if fuzzy_index == -1:
            metrics["desc-fuzzy"] += 1.0
    metrics["name-fuzzy-index"] /= len(split_search)
    metrics["name-fuzzy-order"] /= len(split_search)
    metrics["name-exact-index"] /= len(split_search)
    metrics["name-exact-order"] /= len(split_search)
    metrics["desc-fuzzy"] /= len(split_search)
    return metrics


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
    from csv import DictReader
    from os.path import isfile

    check_required_preferences(preferences)
    if keyword not in (
        preferences["KEYWORD"],
        preferences["KEYWORD_APPS"],
        preferences["KEYWORD_FRIENDS"],
        preferences["KEYWORD_NAVIGATIONS"],
        preferences["KEYWORD_EXTENSION"],
    ):
        log.error(
            f"Invalid keyword '{keyword}', start query with one of ('{preferences['KEYWORD']}', '{preferences['KEYWORD_APPS']}', '{preferences['KEYWORD_FRIENDS']}', '{preferences['KEYWORD_NAVIGATIONS']}', '{preferences['KEYWORD_EXTENSION']}')"
        )
        keyword = ""
        search = None
    if search is None:
        log.info("Querying Steam extension cache")
    else:
        log.info(f"Querying Steam extension cache with search '{search}'")
    cache: dict[str, Any] = load_cache()
    lang: dict[str, dict[str, str]] = {}
    try:
        with open(f"{EXTENSION_PATH}lang.csv", "r", encoding="utf-8") as f:
            reader: DictReader = DictReader(f)
            for row in reader:
                lang[row["key"]] = {
                    k: v for k, v in row.items() if k != "key" and v != ""
                }
    except Exception:
        log.error("Failed to read lang.csv", exc_info=True)
    log.debug("Getting blacklists from preferences")
    app_blacklist: list[int] = get_blacklist("app", preferences)
    friend_blacklist: list[int] = get_blacklist("friend", preferences)
    items: list[SteamExtensionItem] = []
    icon: str | None
    icon_path: str
    launched: datetime | None
    times: int
    oldest_launched: datetime | None = None
    most_times: int = 0

    def compare_launches(info: dict[str, Any]) -> tuple[datetime | None, int]:
        """
        Compares the launch times and times of an item to the current oldest launch time and most times of an item, and updates them if the item has a newer launch time or more times. This function also returns the last time the item was launched and the number of times it has been launched.

        Args:
            info (dict[str, Any]): The item dictionary.

        Returns:
            tuple[datetime | None, int]: The last time the item was launched and the number of times it has been launched.
        """
        nonlocal oldest_launched
        nonlocal most_times

        launched: datetime | None
        times: int
        launched, times = get_launches(info)
        if launched is not None and (
            oldest_launched is None or launched > oldest_launched
        ):
            oldest_launched = launched
        if times > most_times:
            most_times = times
        return launched, times

    if keyword in (preferences["KEYWORD"], preferences["KEYWORD_APPS"]):
        app_id_int: int
        name: str
        location: str | None
        size: int
        if "apps" in cache.keys() and isinstance(cache["apps"], dict):
            for app_id, app_info in cache["apps"].items():
                app_id_int = int(app_id)
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
                location = app_info.get("dir")
                size = app_info.get("size", 0)
                if preferences["SHOW_UNINSTALLED"] == "false" and (
                    location is None and size == 0
                ):
                    continue
                name = app_info["name"]
                display_name: str | None = None
                if location is not None or size > 0:
                    display_name = get_lang_string(
                        lang, preferences["LANGUAGE"], f"launch_%a"
                    ).replace("%a", name)
                else:
                    display_name = get_lang_string(
                        lang, preferences["LANGUAGE"], f"install_%a"
                    ).replace("%a", name)
                playtime: int = app_info.get("playtime", 0)
                icon = None
                icon_path = (
                    f"{EXTENSION_PATH}images{DIR_SEP}apps{DIR_SEP}{app_id_int}.jpg"
                )
                if isfile(icon_path):
                    icon = icon_path
                launched, times = compare_launches(app_info)
                items.append(
                    SteamExtensionItem(
                        preferences,
                        lang,
                        type="app",
                        id=app_id_int,
                        name=name,
                        display_name=display_name,
                        location=location,
                        size=size,
                        playtime=playtime,
                        icon=icon,
                        launched=launched,
                        times=times,
                    )
                )
        if "nonSteam" in cache.keys() and isinstance(cache["nonSteam"], dict):
            for app_id, app_info in cache["nonSteam"].items():
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
                name = app_info["name"]
                non_steam_display_name: str = get_lang_string(
                    lang, preferences["LANGUAGE"], f"launch_%a"
                ).replace("%a", name)
                location = app_info.get("exe")
                size = app_info.get("size", 0)
                icon = None
                icon_path = f"{EXTENSION_PATH}images{DIR_SEP}apps{DIR_SEP}{app_id_int}"
                if isfile(f"{icon_path}.png"):
                    icon = f"{icon_path}.png"
                elif isfile(f"{icon_path}.jpg"):
                    icon = f"{icon_path}.jpg"
                launched, times = compare_launches(app_info)
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
                        icon=icon,
                        size=size,
                        launched=launched,
                        times=times,
                    )
                )
    if (
        keyword in (preferences["KEYWORD"], preferences["KEYWORD_FRIENDS"])
        and "friends" in cache.keys()
        and isinstance(cache["friends"], dict)
    ):
        for friend_id, friend_info in cache["friends"].items():
            friend_id_int: int
            try:
                friend_id_int = int(friend_id)
            except Exception:
                log.error(f"Invalid friend ID '{friend_id}'", exc_info=True)
                continue
            if friend_id_int in friend_blacklist:
                log.debug(f"Skipping blacklisted friend ID {friend_id_int}")
                continue
            if not isinstance(friend_info, dict):
                log.error(
                    f"Invalid dictionary for Steam friend ID {friend_id_int}: {friend_info}",
                    exc_info=True,
                )
                continue
            name = friend_info["name"] if "name" in friend_info.keys() else friend_id
            real_name: str | None = friend_info.get("realName")
            created: datetime | None = friend_info.get("created")
            location = None
            if "country" in friend_info.keys():
                location = friend_info["country"]
                if "state" in friend_info.keys():
                    if (
                        friend_info["country"] in cache["countries"].keys()
                        and friend_info["state"]
                        in cache["countries"][friend_info["country"]].keys()
                    ):
                        location = f"{cache['countries'][friend_info['country']][friend_info['state']]['name']}, {location}"
                    else:
                        location = f"{friend_info['state']}, {location}"
                    if (
                        "city" in friend_info.keys()
                        and friend_info["country"] in cache["countries"].keys()
                        and friend_info["state"]
                        in cache["countries"][friend_info["country"]].keys()
                        and str(friend_info["city"])
                        in cache["countries"][friend_info["country"]][
                            friend_info["state"]
                        ].keys()
                    ):
                        location = f"{cache['countries'][friend_info['country']][friend_info['state']][str(friend_info['city'])]}, {location}"
            icon = f"{EXTENSION_PATH}images{DIR_SEP}friend-default.jpg"
            icon_path = (
                f"{EXTENSION_PATH}images{DIR_SEP}friends{DIR_SEP}{friend_id_int}.jpg"
            )
            if isfile(icon_path):
                icon = icon_path
            updated: datetime | None = timestamp_to_datetime_from_dict(
                friend_info, "updated"
            )
            created = timestamp_to_datetime_from_dict(friend_info, "created")
            launched, times = compare_launches(friend_info)
            items.append(
                SteamExtensionItem(
                    preferences,
                    lang,
                    type="friend",
                    id=friend_id_int,
                    name=name,
                    real_name=real_name,
                    created=created,
                    location=location,
                    icon=icon,
                    updated=updated,
                    launched=launched,
                    times=times,
                )
            )
    if keyword in (
        preferences["KEYWORD"],
        preferences["KEYWORD_APPS"],
        preferences["KEYWORD_FRIENDS"],
        preferences["KEYWORD_NAVIGATIONS"],
    ):
        if "navs" not in cache.keys() or not isinstance(cache["navs"], dict):
            log.warning(msg="cache.json does not contain valid 'navs' key")
            cache["navs"] = {}

        def sanitise_filename(filename: str) -> str:
            """
            Sanitises a filename by replacing unsupported characters with dashes, according to Windows file naming conventions. Do not include directories in the filename when using this function.

            Args:
                filename (str): The filename to sanitise.

            Returns:
                str: The sanitised filename.
            """
            from re import sub as re_sub

            return re_sub(r"[<>:\"/\\|?*]", "-", filename)

        for name in STEAM_NAVIGATIONS:
            nav_display_name: str = get_lang_string(lang, preferences["LANGUAGE"], name)
            description: str | None = None
            try:
                description = get_lang_string(
                    lang, preferences["LANGUAGE"], f"{name}%d", strict=True
                )
            except KeyError:
                pass
            ids: list[int | None] = [None]
            if "%a" in name and keyword in (
                preferences["KEYWORD"],
                preferences["KEYWORD_APPS"],
            ):
                if preferences["SHOW_DEPENDENT"] not in ("all", "onlyApps"):
                    continue
                if "apps" in cache.keys() and isinstance(cache["apps"], dict):
                    ids = [int(app_id) for app_id in cache["apps"].keys()]
                else:
                    log.warning(
                        "cache.json does not contain any valid Steam apps",
                        exc_info=True,
                    )
                    continue
            elif "%f" in name and keyword in (
                preferences["KEYWORD"],
                preferences["KEYWORD_FRIENDS"],
            ):
                if preferences["SHOW_DEPENDENT"] not in ("all", "onlyFriends"):
                    continue
                if "friends" in cache.keys() and isinstance(cache["friends"], dict):
                    ids = [int(friend_id) for friend_id in cache["friends"].keys()]
                else:
                    log.warning(
                        "cache.json does not contain any valid Steam friends",
                        exc_info=True,
                    )
                    continue
            elif keyword in (
                preferences["KEYWORD_APPS"],
                preferences["KEYWORD_FRIENDS"],
            ):
                continue
            for id in ids:
                if (
                    ("%a" in name and id in app_blacklist)
                    or ("%f" in name and id in friend_blacklist)
                    or ("%u" in name and preferences["STEAM_USERNAME"] == "")
                ):
                    continue
                id_name: str = name
                skip_dependent_nav: bool = False
                for modifier in ("%a", "%f"):
                    if modifier in name:
                        if keyword == preferences["KEYWORD_NAVIGATIONS"]:
                            skip_dependent_nav = True
                            continue
                        id_name = name.replace(modifier, str(id))
                if skip_dependent_nav:
                    continue
                id_display_name: str = nav_display_name
                id_description: str | None = description
                icon = None
                icon_path = f"{EXTENSION_PATH}images{DIR_SEP}navs{DIR_SEP}{sanitise_filename(f'{name}.png')}"
                if "%a" in name:  # App ID
                    if preferences["SHOW_UNINSTALLED"] == "false" and (
                        "location" not in cache["apps"][str(id)].keys()
                        and "size" not in cache["apps"][str(id)].keys()
                    ):
                        continue
                    app_name: str = str(id)
                    if "name" in cache["apps"][str(id)].keys():
                        app_name = str(cache["apps"][str(id)]["name"])
                    id_display_name = nav_display_name.replace("%a", app_name)
                    if id_description is not None:
                        id_description = id_description.replace("%a", app_name)
                    if icon is None:
                        icon_path = (
                            f"{EXTENSION_PATH}images{DIR_SEP}apps{DIR_SEP}{id}.jpg"
                        )
                elif "%f" in name:  # Friend steamID64
                    skip_repeated_action: bool = False
                    for act, key in (
                        ("friends/message/", "chat"),
                        ("url/SteamIDPage/", "profile"),
                    ):
                        skip_repeated_action = (
                            name.startswith(act) and preferences["FRIEND_ACTION"] == key
                        )
                    if skip_repeated_action:
                        continue
                    friend_name: str = str(id)
                    if "name" in cache["friends"][str(id)].keys():
                        friend_name = str(cache["friends"][str(id)]["name"])
                    id_display_name = nav_display_name.replace("%f", friend_name)
                    if id_description is not None:
                        id_description = id_description.replace("%f", friend_name)
                    if icon is None:
                        icon_path = (
                            f"{EXTENSION_PATH}images{DIR_SEP}friends{DIR_SEP}{id}.jpg"
                        )
                elif "%u" in name:  # Username
                    id_display_name = nav_display_name.replace(
                        "%u", preferences["STEAM_USERNAME"]
                    )
                    if id_description is not None:
                        id_description = id_description.replace(
                            "%u", preferences["STEAM_USERNAME"]
                        )
                if isfile(icon_path):
                    icon = icon_path
                else:
                    log.debug(
                        f"Failed to find icon for navigation '{name}' at '{icon_path}'"
                    )
                launched = None
                times = 0
                if id_name in cache["navs"].keys() and isinstance(
                    cache["navs"][id_name], dict
                ):
                    launched, times = compare_launches(cache["navs"][id_name])
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
                        launched=launched,
                        times=times,
                    )
                )
    if keyword in (preferences["KEYWORD"], preferences["KEYWORD_EXTENSION"]):
        for name in ("update_cache", "clear_cache", "clear_images", "rebuild_cache"):
            items.append(
                SteamExtensionItem(
                    preferences,
                    lang,
                    type="action",
                    name=name,
                    display_name=get_lang_string(lang, preferences["LANGUAGE"], name),
                    description=get_lang_string(
                        lang, preferences["LANGUAGE"], f"{name}%d"
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
        split_search: list[str] = search.split()
        now: datetime = datetime.now(timezone.utc)

        def get_placement(item: SteamExtensionItem) -> float:
            """
            Gets the placement of an item based on various attributes. The lower the placement, the higher the item will appear in the list.

            Args:
                item (SteamExtensionItem): The item to get the placement of.

            Returns:
                float: The placement of the item.
            """
            metrics: dict[str, float] = get_item_metrics(
                item, split_search, oldest_launched, most_times, now
            )
            placement: float = 0.0
            for key, mult in ITEM_METRIC_MULTS.items():
                placement += metrics[key] * mult
            return placement

        items = sorted(items, key=lambda item: get_placement(item))
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
                    lang, preferences["LANGUAGE"], "no_results"
                ),
                description=get_lang_string(
                    lang, preferences["LANGUAGE"], f"no_results%d"
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
                    sys.argv[1],
                    preferences,
                    search=" ".join(sys.argv[2:] if len(sys.argv) >= 3 else ""),
                )
            )
        )
    )
