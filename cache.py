"""
This module contains functions for building and saving the Steam extension cache. The cache dictionary is saved to a JSON file named "cache.json" in the extension directory.
"""

from const import DIR_SEP, EXTENSION_PATH, get_logger
from datetime import datetime, timedelta
from logging import Logger
from os import makedirs, remove
from os.path import isdir, isfile
from typing import Any, Literal
from urllib.error import HTTPError
from urllib.request import urlretrieve

log: Logger = get_logger(__name__)


def download_steam_app_icon(app_id: int, icon_hash: str) -> None:
    """
    Downloads the Steam icon for the given app ID and hash and saves it to the images/apps folder.

    Args:
        appid (int): The ID of the Steam app.
        icon_hash (str): The hash of the icon of the Steam app.
    """
    app_images_path: str = f"{EXTENSION_PATH}images{DIR_SEP}apps{DIR_SEP}"
    if not isdir(app_images_path):
        makedirs(app_images_path)
    if isfile(f"{app_images_path}{app_id}.jpg"):
        remove(f"{app_images_path}{app_id}.jpg")
    icon_url: str = (
        f"http://media.steampowered.com/steamcommunity/public/images/apps/{app_id}/{icon_hash}.jpg"
    )
    try:
        urlretrieve(icon_url, f"{app_images_path}{app_id}.jpg")
    except HTTPError:
        log.warning(
            f"Failed to download Steam icon for app ID {app_id} at '{icon_url}'",
            exc_info=True,
        )


def download_steam_friend_icon(steamid64: int, icon_hash: str) -> None:
    """
    Downloads the Steam icon for the given Steam ID and hash and saves it to the images/friends folder.

    Args:
        steamid64 (int): The Steam ID of the Steam friend.
        icon_hash (str): The hash of the icon of the Steam friend.
    """
    friend_images_path: str = f"{EXTENSION_PATH}images{DIR_SEP}friends{DIR_SEP}"
    if not isdir(friend_images_path):
        makedirs(friend_images_path)
    if isfile(f"{friend_images_path}{steamid64}.jpg"):
        remove(f"{friend_images_path}{steamid64}.jpg")
    icon_url: str = f"http://avatars.steamstatic.com/{icon_hash}_full.jpg"
    try:
        urlretrieve(icon_url, f"{friend_images_path}{steamid64}.jpg")
    except HTTPError:
        log.warning(
            f"Failed to download Steam icon for steamid64 {steamid64} at '{icon_url}'",
            exc_info=True,
        )


def load_cache() -> dict[str, Any]:
    """
    Loads the cache dictionary from its JSON file. If the file does not exist or an error occurs, an empty dictionary is returned.

    Returns:
        dict[str, Any]: The cache dictionary.
    """
    from json import loads as json_loads

    cache: dict[str, Any] = {}
    if isfile(f"{EXTENSION_PATH}cache.json"):
        log.debug("Loading cache.json")
        try:
            with open(f"{EXTENSION_PATH}cache.json", "r", encoding="utf-8") as f:
                cache = json_loads(f.read())
            log.debug("cache.json loaded")
        except Exception:
            log.error("Failed to read cache.json", exc_info=True)
    else:
        log.warning("cache.json does not exist")
    return cache


def get_blacklist(
    type: Literal["app", "friend"], preferences: dict[str, Any]
) -> list[int]:
    """
    Returns a list of IDs from the specified blacklist property in the preferences dictionary, provided they are integers separated by commas.

    Args:
        type (Literal["app", "friend"]): The type of blacklist to retrieve.
        preferences (dict[str, Any]): The preferences dictionary.

    Returns:
        list[int]: The blacklisted IDs.
    """
    blacklist_str: str = preferences[f"{type.upper()}_BLACKLIST"].strip()
    if blacklist_str != "":
        blacklist_str_list: list[str] = blacklist_str.split(",")
        try:
            return [int(id.strip()) for id in blacklist_str_list]
        except Exception:
            log.error(
                f"Failed to parse {type} blacklist value '{blacklist_str}'",
                exc_info=True,
            )
    return []


def str_to_timedelta(string: str) -> timedelta:
    """
    Converts a string to a timedelta object, using regex to parse time units. The string can contain the following units: y, mo, w, d, h, m, s, ms, us. If the string has no units, the timedelta will be 0.

    Args:
        string (str): The string to convert.

    Returns:
        timedelta: The timedelta object.
    """
    from re import findall as re_findall

    if string == "":
        return timedelta(0)
    time_strings: list[str] = re_findall(
        r"-?[0-9]+(?:\.[0-9]+)?(?:y|mo|w|d|h|m|s|ms|us)(?![a-z])", string
    )
    years: float = 0
    months: float = 0
    weeks: float = 0
    days: float = 0
    hours: float = 0
    minutes: float = 0
    seconds: float = 0
    milliseconds: float = 0
    microseconds: float = 0
    for time_string in time_strings:
        if time_string.endswith("y"):
            years += float(time_string[:-1])
        elif time_string.endswith("mo"):
            months += float(time_string[:-2])
        elif time_string.endswith("w"):
            weeks += float(time_string[:-1])
        elif time_string.endswith("d"):
            days += float(time_string[:-1])
        elif time_string.endswith("h"):
            hours += float(time_string[:-1])
        elif time_string.endswith("m"):
            minutes += float(time_string[:-1])
        elif time_string.endswith("ms"):
            milliseconds += float(time_string[:-2])
        elif time_string.endswith("us"):
            microseconds += float(time_string[:-2])
        elif time_string.endswith("s"):  # After "ms" and "us" to avoid errors
            seconds += float(time_string[:-1])
        else:
            log.warning(
                f"Invalid time unit '{time_string}' in '{string}', accepted units: y, mo, w, d, h, m, s, ms, us"
            )
    return timedelta(
        weeks=weeks,
        days=(years * 365) + (months * 30) + days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        milliseconds=milliseconds,
        microseconds=microseconds,
    )


def ensure_dict_key_is_dict(dictionary: dict, key: Any) -> tuple[dict, bool]:
    """
    Ensures that the given key exists in the dictionary and is a dictionary. If the key does not exist or is not a dictionary, it is created and initialised as an empty dictionary.

    Args:
        dictionary (dict): The dictionary to check.
        key (Any): The key to check.

    Returns:
        tuple[dict, bool]: The dictionary at the given key, and a boolean that is True if the key existed and was a dictionary, or False if otherwise.
    """
    if key in dictionary.keys() and isinstance(dictionary[key], dict):
        return dictionary[key], True
    dictionary[key] = {}
    return dictionary[key], False


def get_steam_folders(preferences: dict[str, Any]) -> list[str]:
    """
    Returns a list of Steam folders from the preferences dictionary, removing any that do not contain a "steamapps" folder. The first of these folders is assumed to include a "userdata" folder.

    Args:
        preferences (dict[str, Any]): The preferences dictionary.

    Returns:
        list[str]: The list of Steam folders.
    """
    folders_str: str = preferences["STEAM_FOLDERS"].strip()
    folders: list[str] = folders_str.split(",")
    for i in reversed(range(len(folders))):
        if not folders[i].endswith(DIR_SEP):
            folders[i] += DIR_SEP
        if not isdir(folders[i]):
            log.warning(f"Steam folder '{folders[i]}' is not a folder")
            folders.pop(i)
            continue
        if not isdir(f"{folders[i]}{DIR_SEP}steamapps{DIR_SEP}"):
            log.warning(
                f"Steam folder '{folders[i]}' does not contain a 'steamapps' folder"
            )
            folders.pop(i)
    return folders


def datetime_to_timestamp(dt: datetime | None = None) -> int:
    """
    Converts a datetime object to an integer timestamp.

    Args:
        dt (datetime | None, optional): The datetime object to convert. If this is None, the current datetime is used. Defaults to None.

    Returns:
        int: The timestamp of the datetime object.
    """
    from math import floor

    if dt is None:
        dt = datetime.now()
    return floor(dt.timestamp())


def save_cache(cache: dict[str, Any], preferences: dict[str, Any]) -> None:
    """
    Saves the updated cache dictionary to its JSON file.

    Args:
        cache (dict[str, Any]): The updated cache dictionary.
        preferences (dict[str, Any]): The preferences dictionary.
    """
    from json import dumps as json_dumps

    log.debug("Saving cache.json")
    try:
        with open(f"{EXTENSION_PATH}cache.json", "w", encoding="utf-8") as f:
            f.write(
                json_dumps(
                    cache,
                    indent=(
                        int(preferences["CACHE_INDENT"])
                        if "CACHE_INDENT" in preferences.keys()
                        and preferences["CACHE_INDENT"] != ""
                        else None
                    ),
                )
            )
        log.debug("Saved cache.json")
    except Exception:
        log.error(f"Failed to save cache.json: {cache}", exc_info=True)


def clear_cache() -> None:
    """
    Clears the cache of the Steam extension.
    """
    log.debug("Deleting cache.json")
    remove(f"{EXTENSION_PATH}cache.json")


# TODO: Convert this function to be asynchronous so that searches are not blocked
def build_cache(preferences: dict[str, Any], force: bool = False) -> None:
    """
    Builds the Steam extension cache, saving it to cache.json. This includes non-Steam apps, installed Steam apps and owned Steam apps.

    Args:
        preferences (dict[str, Any]): The preferences dictionary.
        force (bool, optional): Whether to force a rebuild of all parts of the cache, regardless of whether enough time has passed for each. Defaults to False.
    """
    from const import check_required_preferences
    from get import (
        get_installed_steam_apps,
        get_non_steam_apps,
        get_owned_steam_apps,
        get_state_or_city_codes,
        get_steam_friends_info,
        get_steam_friends_list,
        InstalledSteamApp,
        NonSteamApp,
        OwnedSteamApp,
        SteamFriendFromList,
        SteamFriendInfo,
    )

    check_required_preferences(preferences)
    log.info("Building Steam extension cache")
    cache: dict[str, Any] = load_cache()
    log.debug("Getting blacklists from preferences")
    app_blacklist: list[int] = get_blacklist("app", preferences)
    friend_blacklist: list[int] = get_blacklist("friend", preferences)
    log.debug("Getting delays from preferences")
    update_from_files: bool = True
    update_from_steam_api: bool = True
    if "updated" not in cache.keys():
        log.warning("'updated' not found in cache.json")
    elif not isinstance(cache["updated"], dict):
        log.warning("'updated' in cache.json is not a dictionary")
    elif not force:

        def compare_last_updated(key: str) -> bool:
            if key not in cache["updated"].keys():
                log.warning(
                    f"'updated' in cache.json does not contain '{key}' key"
                )
                return True
            updated_last: datetime = datetime.min
            try:
                updated_last = datetime.fromtimestamp(cache["updated"][key])
            except Exception:
                log.warning(
                    f"Failed to parse 'updated' key '{key}' timestamp '{cache['updated'][key]}'",
                    exc_info=True,
                )
            wait_time: timedelta = str_to_timedelta(
                preferences[f"UPDATE_FROM_{key.replace("Api", "_Api").upper()}_DELAY"]
            )
            if updated_last + wait_time < datetime.now():
                log.debug(
                    f"{key.replace('_', ' ').capitalize()} cache is outdated, updating"
                )
                return True
            log.debug(f"{key.replace('_', ' ').capitalize()} cache is up to date")
            return False

        update_from_files = compare_last_updated("files")
        update_from_steam_api = compare_last_updated("steamApi")
    ensure_dict_key_is_dict(cache, "updated")
    if update_from_files or force:
        steam_folders: list[str] = get_steam_folders(preferences)
        from_files_updated: bool = False

        def compare_last_launched(
            app: InstalledSteamApp | NonSteamApp | OwnedSteamApp, cache_app: dict
        ) -> bool:
            if app["last_launched"] is None:
                return True
            if "last_launched" in cache_app.keys():
                try:
                    cache_last_launched: datetime = datetime.fromtimestamp(
                        cache_app["last_launched"]
                    )
                    if app["last_launched"] < cache_last_launched:
                        return False
                except Exception:
                    log.warning(
                        f"Failed to parse app {app['app_id']} 'last_launched' timestamp '{cache_app['last_launched']}'",
                        exc_info=True,
                    )
            return True

        for steam_folder_index, steam_folder in enumerate(steam_folders):
            if steam_folder_index == 0:
                log.info("Getting non-Steam apps from shortcuts.vdf")
                userdata_folder: str = (
                    f"{steam_folder}userdata{DIR_SEP}{preferences['STEAM_USERDATA_ID']}{DIR_SEP}"
                )
                shortcuts_file: str = (
                    f"{steam_folder}userdata{DIR_SEP}{preferences['STEAM_USERDATA_ID']}{DIR_SEP}config{DIR_SEP}shortcuts.vdf"
                )
                cache_app: dict[str, Any]
                if not isdir(userdata_folder):
                    log.error(
                        f"Steam userdata ID '{preferences['STEAM_USERDATA_ID']}' is invalid as folder path '{userdata_folder}' is invalid"
                    )
                elif not isfile(shortcuts_file):
                    log.error(
                        f"Steam shortcuts file '{shortcuts_file}' unexpectedly not found"
                    )
                else:
                    non_steam_apps: dict[int, NonSteamApp] = {}
                    try:
                        non_steam_apps = get_non_steam_apps(
                            shortcuts_file, app_blacklist
                        )
                    except Exception:
                        log.error("Failed to get non-Steam apps", exc_info=True)
                    if not ensure_dict_key_is_dict(cache, "nonSteam")[1]:
                        log.debug("Removing non-existant non-Steam apps")
                        for app_id in cache["nonSteam"].keys():
                            if int(app_id) not in non_steam_apps.keys():
                                del cache["nonSteam"][app_id]
                    for app_id, app_info in non_steam_apps.items():
                        cache_app = ensure_dict_key_is_dict(
                            cache["nonSteam"], str(app_id)
                        )[0]
                        cache_app["name"] = app_info["name"]
                        if app_info["exe"] is not None:
                            cache_app["exe"] = app_info["exe"]
                        elif "exe" in cache_app.keys():
                            del cache_app["exe"]
                        if app_info["size_on_disk"] is not None:
                            cache_app["size_on_disk"] = app_info["size_on_disk"]
                        elif "size_on_disk" in cache_app.keys():
                            del cache_app["size_on_disk"]
                        if app_info["last_launched"] is not None:
                            if compare_last_launched(app_info, cache_app):
                                cache_app["last_launched"] = datetime_to_timestamp(
                                    app_info["last_launched"]
                                )
                    from_files_updated = True
            log.info("Getting installed Steam apps from appmanifest_#.acf files")
            steamapps_folder: str = f"{steam_folder}steamapps{DIR_SEP}"
            if not isdir(steamapps_folder):
                log.error(
                    f"Steam steamapps folder path '{steamapps_folder}' unexpectedly is invalid"
                )
            else:
                installed_steam_apps: dict[int, InstalledSteamApp] = {}
                try:
                    installed_steam_apps = get_installed_steam_apps(
                        steamapps_folder, app_blacklist
                    )
                except Exception:
                    log.error("Failed to get installed Steam apps", exc_info=True)
                if not ensure_dict_key_is_dict(cache, "apps")[1]:
                    log.debug("Removing 'size_on_disk' key from uninstalled Steam apps")
                    for app_id in cache["apps"].keys():
                        try:
                            if (
                                int(app_id) not in installed_steam_apps.keys()
                                and isinstance(cache["apps"][app_id], dict)
                                and "size_on_disk" in cache["apps"][app_id].keys()
                            ):
                                del cache["apps"][app_id]["size_on_disk"]
                        except Exception:
                            log.warning(
                                f"Failed to check Steam app with ID '{app_id}', not a number"
                            )
                for app_id, app_info in installed_steam_apps.items():
                    cache_app = ensure_dict_key_is_dict(cache["apps"], str(app_id))[0]
                    cache_app["name"] = app_info["name"]
                    cache_app["install_dir"] = app_info["install_dir"]
                    cache_app["size_on_disk"] = app_info["size_on_disk"]
                    if app_info["last_updated"] is not None:
                        cache_app["last_updated"] = datetime_to_timestamp(
                            app_info["last_updated"]
                        )
                    if app_info["last_launched"] is not None:
                        if compare_last_launched(app_info, cache_app):
                            cache_app["last_launched"] = datetime_to_timestamp(
                                app_info["last_launched"]
                            )
                if len(installed_steam_apps) >= 1:
                    if "CACHE_SORT" in preferences.keys() and bool(
                        preferences["CACHE_SORT"]
                    ):
                        cache["apps"] = {
                            k: v
                            for k, v in sorted(
                                cache["apps"].items(), key=lambda i: int(i[0])
                            )
                        }
                    from_files_updated = True
            if from_files_updated:
                cache["updated"]["files"] = datetime_to_timestamp()
                save_cache(cache, preferences)
    if update_from_steam_api or force:
        log.info("Getting owned Steam apps from Steam API")
        from_steam_api_updated: bool = False
        owned_steam_apps: dict[int, OwnedSteamApp] = {}
        try:
            owned_steam_apps = get_owned_steam_apps(
                preferences["STEAM_API_KEY"], int(preferences["STEAMID64"])
            )
        except Exception:
            log.error("Failed to get owned Steam apps", exc_info=True)
        ensure_dict_key_is_dict(cache, "apps")
        app_icons_to_download: list[tuple[int, str]] = []
        for app_id, app_info in owned_steam_apps.items():
            cache_app = ensure_dict_key_is_dict(cache["apps"], str(app_id))[0]
            cache_app["name"] = app_info["name"]
            cache_app["total_playtime"] = app_info["total_playtime"]
            if app_info["icon_hash"] is not None:
                cache_app["icon_hash"] = app_info["icon_hash"]
                app_icons_to_download.append((app_id, cache_app["icon_hash"]))
        if len(owned_steam_apps) >= 1:
            if "CACHE_SORT" in preferences.keys() and bool(preferences["CACHE_SORT"]):
                cache["apps"] = {
                    k: v
                    for k, v in sorted(cache["apps"].items(), key=lambda i: int(i[0]))
                }
            from_steam_api_updated = True
        if from_steam_api_updated:
            cache["updated"]["steamApi"] = datetime_to_timestamp()
            save_cache(cache, preferences)
        log.info("Getting friends list from Steam API")
        steam_friends_list: dict[int, SteamFriendFromList] = {}
        try:
            steam_friends_list = get_steam_friends_list(
                preferences["STEAM_API_KEY"], int(preferences["STEAMID64"])
            )
        except Exception:
            log.error("Failed to get Steam friends list", exc_info=True)
        ensure_dict_key_is_dict(cache, "friends")
        cache_friend: dict[str, Any]
        for friend_id, friend_info in steam_friends_list.items():
            if friend_id in friend_blacklist:
                log.debug(f"Skipping blacklisted friend ID '{friend_id}'")
                continue
            cache_friend = ensure_dict_key_is_dict(cache["friends"], str(friend_id))[0]
            cache_friend["friend_since"] = datetime_to_timestamp(
                friend_info["friend_since"]
            )
        if len(steam_friends_list) >= 1:
            from_steam_api_updated = True
        log.info("Getting friends info from Steam API")
        steam_friends_info: dict[int, SteamFriendInfo] = {}
        try:
            steam_friends_info = get_steam_friends_info(
                preferences["STEAM_API_KEY"], list(steam_friends_list.keys())
            )
        except Exception:
            log.error("Failed to get Steam friends info", exc_info=True)
        ensure_dict_key_is_dict(cache, "countries")
        city_names_to_download: dict[str, list[str]] = {}
        for steam_friend_info in steam_friends_info.values():
            if (
                steam_friend_info["country_code"] is None
                or steam_friend_info["state_code"] is None
            ):
                continue
            if (
                steam_friend_info["country_code"] not in cache["countries"].keys()
                and steam_friend_info["country_code"]
                not in city_names_to_download.keys()
            ):
                city_names_to_download[steam_friend_info["country_code"]] = []
            ensure_dict_key_is_dict(
                cache["countries"], steam_friend_info["country_code"]
            )
            if steam_friend_info["city_code"] is None:
                continue
            if (
                steam_friend_info["state_code"]
                not in cache["countries"][steam_friend_info["country_code"]].keys()
                and steam_friend_info["state_code"]
                not in city_names_to_download[steam_friend_info["country_code"]]
            ):
                if (
                    steam_friend_info["country_code"]
                    not in city_names_to_download.keys()
                ):
                    city_names_to_download[steam_friend_info["country_code"]] = []
                city_names_to_download[steam_friend_info["country_code"]].append(
                    steam_friend_info["state_code"]
                )
        for country_code in city_names_to_download.keys():
            state_names: dict[str, str] = get_state_or_city_codes(country_code)
            for state_code, state_name in state_names.items():
                ensure_dict_key_is_dict(cache["countries"][country_code], state_code)
                cache["countries"][country_code][state_code]["name"] = state_name
            for state_code in city_names_to_download[country_code]:
                city_names: dict[str, str] = get_state_or_city_codes(
                    country_code, state_code
                )
                for city_code, city_name in city_names.items():
                    cache["countries"][country_code][state_code][city_code] = city_name
        friend_icons_to_download: list[tuple[int, str]] = []
        for friend_id, friend_info in steam_friends_info.items():
            if friend_id in friend_blacklist:
                log.debug(f"Skipping blacklisted friend ID '{friend_id}'")
                continue
            cache_friend = ensure_dict_key_is_dict(cache["friends"], str(friend_id))[0]
            cache_friend["name"] = friend_info["name"]
            if friend_info["icon_hash"] is not None:
                cache_friend["icon_hash"] = friend_info["icon_hash"]
                friend_icons_to_download.append((friend_id, cache_friend["icon_hash"]))
            if friend_info["last_updated"] is not None:
                cache_friend["last_updated"] = datetime_to_timestamp(
                    friend_info["last_updated"]
                )
            if friend_info["real_name"] is not None:
                cache_friend["real_name"] = friend_info["real_name"]
            if friend_info["time_created"] is not None:
                cache_friend["time_created"] = datetime_to_timestamp(
                    friend_info["time_created"]
                )
            if friend_info["country_code"] is not None:
                cache_friend["country"] = friend_info["country_code"]
            if friend_info["state_code"] is not None:
                cache_friend["state"] = friend_info["state_code"]
            if friend_info["city_code"] is not None:
                cache_friend["city"] = friend_info["city_code"]
        if from_steam_api_updated:
            cache["updated"]["steamApi"] = datetime_to_timestamp()
            save_cache(cache, preferences)
        if len(app_icons_to_download) >= 1:
            log.info(f"Downloading {len(app_icons_to_download)} Steam app icons")
            for download in app_icons_to_download:
                download_steam_app_icon(download[0], download[1])
        if len(friend_icons_to_download) >= 1:
            log.info(f"Downloading {len(friend_icons_to_download)} Steam friend icons")
            for download in friend_icons_to_download:
                download_steam_friend_icon(download[0], download[1])
    log.info("Steam extension cache built")


if __name__ == "__main__":
    from const import get_preferences_from_env

    build_cache(get_preferences_from_env())
