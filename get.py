"""
This module contains functions for retrieving data from Steam for the purposes of caching it. This data includes:
- Installed Steam apps
- Owned Steam apps
- Non-Steam apps
"""

from const import DIR_SEP, get_logger
from datetime import datetime
from logging import Logger
from typing import Any, TypeAlias, TypedDict, Union

log: Logger = get_logger(__name__)

NestedStrDict: TypeAlias = dict[str, Union[str, "NestedStrDict"]]


def _vdf_to_dict(path: str) -> dict[str, NestedStrDict]:
    """
    Converts a file of uncompressed VDF data to a dictionary. This function is not compatible with compressed VDF files.

    Args:
        path (str): The uncompressed VDF file.

    Raises:
        KeyError: If more than one top-level key is found.
        KeyError: If a top-level key has a non-dictionary value.
        ValueError: If a closing brace appears and there are no levels left to pop.
        KeyError: If no top-level key is found.

    Returns:
        dict[str, NestedStrDict]: The dictionary representation of the VDF data.
    """
    vdf_lines: list[str]
    with open(path, "r", encoding="utf-8") as f:
        vdf_lines = f.readlines()
    vdf_dict: dict[str, NestedStrDict] = {}
    vdf_levels: list[str] = []
    for index, line in enumerate(vdf_lines):
        quote_count: int = line.count('"') - line.count('\\"')
        # If a line contains two quote marks, it is a new level
        add_dict: NestedStrDict
        if quote_count == 2:
            vdf_levels.append(line.split('"')[1])
            if len(vdf_levels) == 1:
                if len(vdf_dict) != 0:
                    raise KeyError(
                        f"Unexpectedly found additional top-level key '{vdf_levels[0]}' on line {index + 1}"
                    )
                vdf_dict[vdf_levels[0]] = {}
            else:
                add_dict = vdf_dict[vdf_levels[0]]
                if len(vdf_levels) >= 3:
                    for level in vdf_levels[1:-1]:
                        add_dict = add_dict[level]  # type: ignore
                add_dict[vdf_levels[-1]] = {}
        # If a line contains four quote marks, it is a key-value pair
        elif quote_count == 4:
            add_key: str = line.split('"')[1]
            if len(vdf_levels) == 0:
                raise KeyError(
                    f"Unexpectedly found top-level key '{add_key}' with value on line {index + 1}"
                )
            add_dict = vdf_dict[vdf_levels[0]]
            if len(vdf_levels) >= 2:
                for level in vdf_levels[1:]:
                    add_dict = add_dict[level]  # type: ignore
            add_dict[add_key] = line.split('"')[3]
        # If a line contains a closing brace, it is the end of a level
        elif "}" in line:
            if len(vdf_levels) == 0:
                raise ValueError(
                    f"Unexpectedly found extra closing brace on line {index + 1}"
                )
            vdf_levels.pop()
    if len(vdf_dict) == 0:
        raise KeyError("No top-level key found")
    return vdf_dict


class InstalledSteamApp(TypedDict):
    """
    A dictionary representation of an installed Steam app.

    Args:
        name (str): The name of the Steam app.
        dir (str): The path to the folder containing the Steam app.
        size (int): The size of the Steam app on disk in bytes.
        updated (datetime | None): The time the app was last updated, or None if not updated.
        launched (datetime | None): The time the app was last launched, or None if not launched.
    """

    name: str
    dir: str
    size: int
    updated: datetime | None
    launched: datetime | None


def get_installed_steam_apps(
    steamapps_folder: str, app_blacklist: list[int]
) -> dict[int, InstalledSteamApp]:
    """
    Returns a dictionary of InstalledSteamApp instances for all installed Steam apps.

    Args:
        steamapps_folder (str): The path to the steamapps folder.
        app_blacklist (list[int]): A list of app IDs to ignore.

    Returns:
        dict[int, InstalledSteamApp]: A dictionary of InstalledSteamApp instances for all installed Steam apps, indexed by app ID.
    """
    from os import listdir
    from os.path import join as path_join

    if not steamapps_folder.endswith(DIR_SEP):
        steamapps_folder += DIR_SEP
    installed_steam_apps: dict[int, InstalledSteamApp] = {}
    appmanifest_files: tuple[str, ...] = tuple(
        file
        for file in listdir(steamapps_folder)
        if file.startswith("appmanifest_") and file.endswith(".acf")
    )
    for appmanifest_file in appmanifest_files:
        try:
            app_id: int = int(appmanifest_file.split("_")[1].split(".")[0])
            if app_id in app_blacklist:
                log.debug(f"Skipping blacklisted app ID {app_id}")
                continue
            app_vdf: dict[str, NestedStrDict] = _vdf_to_dict(
                path_join(steamapps_folder, appmanifest_file)
            )
            name: str = app_vdf["AppState"]["name"].strip()  # type: ignore
            dir: str = f"{steamapps_folder}{app_vdf['AppState']['installdir']}"
            updated_str: str = app_vdf["AppState"]["LastUpdated"]  # type: ignore
            updated: datetime | None = (
                datetime.fromtimestamp(int(updated_str)) if updated_str != "0" else None
            )
            launched_str: str = app_vdf["AppState"]["LastPlayed"]  # type: ignore
            launched: datetime | None = (
                datetime.fromtimestamp(int(launched_str))
                if launched_str != "0"
                else None
            )
            size_str: str = app_vdf["AppState"]["SizeOnDisk"]  # type: ignore
            if size_str == "0":
                log.debug("Game has not finished installing, using BytesToStage")
                size_str = app_vdf["AppState"]["BytesToStage"]  # type: ignore
            size: int = int(size_str)
            installed_steam_apps[app_id] = InstalledSteamApp(
                name=name,
                dir=dir,
                size=size,
                updated=updated,
                launched=launched,
            )
        except Exception:
            log.error(
                f"Failed to get installed Steam app from '{appmanifest_file}'",
                exc_info=True,
            )
    return installed_steam_apps


class NonSteamApp(TypedDict):
    """
    A dictionary representation of a non-Steam app.

    Args:
        name (str): The name of the non-Steam app.
        exe (str | None): The location of the non-Steam app, or None if it is invalid.
        size (int | None): The size of the non-Steam app on disk in bytes.
        launched (datetime | None): The time the app was last launched, or None if not launched.
    """

    name: str
    exe: str | None
    size: int | None
    launched: datetime | None


# TODO: Get non-Steam app icons from userdata/<user>/config/grid/<appid>_icon.*
def get_non_steam_apps(
    shortcuts_path: str, app_blacklist: list[int]
) -> dict[int, NonSteamApp]:
    """
    Returns a dictionary of NonSteamApp instances for all non-Steam apps.

    Args:
        shortcuts_path (str): The path to the user's shortcuts.vdf file.
        app_blacklist (list[int]): A list of app IDs to ignore.

    Returns:
        dict[int, NonSteamApp]: A dictionary of NonSteamApp instances for all non-Steam apps, indexed by app ID.
    """
    from binascii import hexlify
    import os
    from os.path import getsize, isfile
    from subprocess import CalledProcessError, check_output as subprocess_check_output

    non_steam_apps: dict[int, NonSteamApp] = {}
    buffer: bytearray
    with open(shortcuts_path, "rb") as f:
        buffer = bytearray.fromhex(hexlify(f.read()).decode())
    cursor: int = 11
    shortcut_id: int = -1
    shortcuts_dict: dict[int, dict[str, Any]] = {}
    while cursor < len(buffer):
        cursor_moved: bool = False

        def cursor_match(string: str) -> bool:
            nonlocal cursor
            nonlocal cursor_moved

            cursor_matched: bool = string == buffer[
                cursor : cursor + len(string)
            ].decode(errors="ignore")
            if cursor_matched:
                cursor += len(string)
                cursor_moved = True
            return cursor_matched

        if cursor_match(f"\x00{shortcut_id + 1}\x00"):
            shortcut_id += 1
            shortcuts_dict[shortcut_id] = {}
        if cursor_match("\x02appid\x00"):
            shortcuts_dict[shortcut_id]["app_id"] = int.from_bytes(
                buffer[cursor + 3 : cursor - 1 : -1] + b"\x02\x00\x00\x00", "big"
            )
            cursor += 4
        if cursor_match("\x01AppName\x00"):
            app_name_start: int = cursor
            while cursor < len(buffer) and buffer[cursor] != 0:
                cursor += 1
            shortcuts_dict[shortcut_id]["name"] = buffer[app_name_start:cursor].decode(
                errors="ignore"
            )
            cursor += 1
        if cursor_match("\x01Exe\x00"):
            exe_start: int = cursor
            while cursor < len(buffer) and buffer[cursor] != 0:
                cursor += 1
            exe: str | None = buffer[exe_start:cursor].decode(errors="ignore").strip()
            if os.name != "nt":
                try:
                    which_exe: str = subprocess_check_output(
                        f"which {exe}", shell=True
                    ).decode()
                    if which_exe != "":
                        exe = which_exe
                except CalledProcessError:
                    log.warning(f"Failed to evaluate system location of '{exe}'")
            size: int | None = None
            if isfile(exe):
                size = getsize(exe)
            else:
                log.warning(f"Non-Steam app executable '{exe}' does not exist")
                exe = None
            shortcuts_dict[shortcut_id]["exe"] = exe
            shortcuts_dict[shortcut_id]["size_on_disk"] = size
            cursor += 1
        if cursor_match("\x02LastPlayTime\x00"):
            launched_int: int = int.from_bytes(buffer[cursor : cursor + 4], "little")
            shortcuts_dict[shortcut_id]["launched"] = (
                datetime.fromtimestamp(launched_int) if launched_int != 0 else None
            )
            cursor += 4
        if not cursor_moved:
            cursor += 1
    for shortcut_id, app_info in shortcuts_dict.items():
        if app_info["app_id"] in app_blacklist:
            log.debug(f"Skipping blacklisted app {app_info['app_id']}")
            continue
        try:
            non_steam_apps[app_info["app_id"]] = NonSteamApp(
                name=app_info["name"],
                exe=app_info["exe"],
                size=app_info["size"],
                launched=app_info["launched"],
            )
        except Exception:
            log.error(
                f"Failed to parse non-Steam app with shortcut ID {shortcut_id}",
                exc_info=True,
            )
    return non_steam_apps


def _get_response_from_steam_api(url: str) -> dict[str, Any]:
    """
    Gets a response from the Steam API.

    Args:
        url (str): The URL to get the response from.

    Raises:
        ValueError: If the Steam API key is invalid.
        ValueError: If the parameters sent to the Steam API are invalid.
        ConnectionError: If an unknown error occurs with the Steam API.

    Returns:
        dict[str, Any]: The response from the Steam API.
    """
    from http.client import HTTPSConnection
    from json import loads as json_loads

    conn: HTTPSConnection = HTTPSConnection("api.steampowered.com")
    conn.request("GET", url)
    response: bytes = conn.getresponse().read()
    if (
        response
        == b"<html><head><title>Unauthorized</title></head><body><h1>Unauthorized</h1>Access is denied. Retrying will not help. Please verify your <pre>key=</pre> parameter.</body></html>"
    ):
        raise ValueError("Steam API key is invalid")
    elif (
        response
        == b"<html><head><title>Bad Request</title></head><body><h1>Bad Request</h1>Please verify that all required parameters are being sent</body></html>"
    ):
        raise ValueError("Parameters sent to Steam API are invalid")
    elif response.startswith(b"<html>"):
        raise ConnectionError(f"Unknown error with Steam API: {response.decode()}")
    return json_loads(response)


class OwnedSteamApp(TypedDict):
    """
    A dictionary representation of an owned Steam app.

    Args:
        name (str): The name of the Steam app.
        playtime (int): The total playtime of the Steam app in minutes.
        icon_hash (str | None): The hash of the icon of the Steam app, or None if no icon is available.
    """

    name: str
    playtime: int
    icon_hash: str | None


def get_owned_steam_apps(api_key: str, steamid64: int) -> dict[int, OwnedSteamApp]:
    """
    Returns a dictionary of owned Steam apps, retrieved from the Steam API.

    Args:
        api_key (str): The Steam API key.
        steamid64 (str): The steamid64 of the user.

    Returns:
        dict[int, OwnedSteamApp]: The dictionary of owned Steam apps.
    """
    log.info(f"Getting owned Steam apps from Steam API for user {steamid64}")
    owned_steam_apps: dict[int, OwnedSteamApp] = {}
    owned_apps_url: str = (
        f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steamid64}&include_appinfo=1&include_played_free_games=1&format=json"
    )
    owned_apps_response: list[dict[str, Any]] = []
    try:
        owned_apps_response = _get_response_from_steam_api(owned_apps_url)["response"][
            "games"
        ]
    except Exception:
        log.error("Failed to retrieve owned apps from Steam API", exc_info=True)
    for owned_steam_app in owned_apps_response:
        app_id: int = owned_steam_app["appid"]
        name: str = owned_steam_app["name"].strip()
        playtime: int = owned_steam_app["playtime_forever"]
        icon_hash: str | None = owned_steam_app["img_icon_url"]
        if icon_hash == "":
            icon_hash = None
        owned_steam_apps[app_id] = OwnedSteamApp(
            name=name,
            playtime=playtime,
            icon_hash=icon_hash,
        )
    return owned_steam_apps


class SteamFriendFromList(TypedDict):
    """
    A dictionary representation of a Steam friend from the Steam API when retrieving a list of friends.
    """

    since: datetime


def get_steam_friends_list(
    api_key: str, steamid64: int
) -> dict[int, SteamFriendFromList]:
    """
    Returns a dictionary of Steam friends in the user's friend list, retrieved from the Steam API.

    Args:
        api_key (str): The Steam API key.
        steamid64 (int): The steamid64 of the user.

    Returns:
        dict[int, SteamFriendFromList]: The dictionary of Steam friends in the user's friend list.
    """
    log.info(f"Getting Steam friends from Steam API for user {steamid64}")
    steam_friends: dict[int, SteamFriendFromList] = {}
    steam_friends_url: str = (
        f"https://api.steampowered.com/ISteamUser/GetFriendList/v1/?key={api_key}&steamid={steamid64}&relationship=friend"
    )
    steam_friends_response: list[dict[str, Any]] = []
    try:
        steam_friends_response = _get_response_from_steam_api(steam_friends_url)[
            "friendslist"
        ]["friends"]
    except Exception:
        log.error("Failed to retrieve friends from Steam API", exc_info=True)
    for steam_friend in steam_friends_response:
        steam_friend_id64: int = int(steam_friend["steamid"])
        since: datetime = datetime.fromtimestamp(steam_friend["friend_since"])
        steam_friends[steam_friend_id64] = SteamFriendFromList(since=since)
    return steam_friends


class SteamFriendInfo(TypedDict):
    """
    A dictionary representation of a Steam friend from the Steam API when retrieving their info. Nicknames are not included as part of this, as nicknames are not stored in a file nor exposed by the Steam API.
    """

    name: str | None
    icon_hash: str | None
    updated: datetime | None
    real_name: str | None
    created: datetime | None
    country_code: str | None
    state_code: str | None
    city_code: int | None


def get_steam_friends_info(
    api_key: str, steamid64s: list[int]
) -> dict[int, SteamFriendInfo]:
    """
    Returns a dictionary of Steam friends info, retrieved from the Steam API.

    Args:
        api_key (str): The Steam API key.
        steamid64s (list[int]): The list of steamid64s of the friends.

    Returns:
        dict[int, SteamFriendInfo]: The dictionary of Steam friends info.
    """
    log.info(f"Getting Steam friends info from Steam API for users")
    steam_friend_infos: dict[int, SteamFriendInfo] = {}
    for i in range(0, len(steamid64s), 100):
        batch_steamid64s = steamid64s[i : min(i + 100, len(steamid64s))]
        log.debug(f"Getting Steam friends info for batch {batch_steamid64s}")
        steam_friend_info_url: str = (
            f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={api_key}&steamids={','.join(map(str, batch_steamid64s))}"
        )
        steam_friend_info_response: list[dict[str, Any]] = []
        try:
            steam_friend_info_response = _get_response_from_steam_api(
                steam_friend_info_url
            )["response"]["players"]
        except Exception:
            log.error("Failed to retrieve friends info from Steam API", exc_info=True)
        for steam_friend_info in steam_friend_info_response:
            steamid64: int = int(steam_friend_info["steamid"])
            name: str | None = steam_friend_info["personaname"]
            icon_hash: str | None = None
            # TODO: Add default icon to images for extension to use by default
            if (
                steam_friend_info["avatarhash"]
                != "fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb"  # Default icon
            ):
                icon_hash = steam_friend_info["avatarhash"]
            updated: datetime | None = None
            real_name: str | None = None
            created: datetime | None = None
            country: str | None = None
            state: str | None = None
            city: int | None = None
            if steam_friend_info["communityvisibilitystate"] == 3:
                if "lastlogoff" in steam_friend_info.keys():
                    updated = datetime.fromtimestamp(steam_friend_info["lastlogoff"])
                if "realname" in steam_friend_info.keys():
                    real_name = steam_friend_info["realname"]
                created = datetime.fromtimestamp(steam_friend_info["timecreated"])
                if "loccountrycode" in steam_friend_info.keys():
                    country = steam_friend_info["loccountrycode"]
                if "locstatecode" in steam_friend_info.keys():
                    state = steam_friend_info["locstatecode"]
                if "loccityid" in steam_friend_info.keys():
                    city = steam_friend_info["loccityid"]
            steam_friend_infos[steamid64] = SteamFriendInfo(
                name=name,
                icon_hash=icon_hash,
                updated=updated,
                real_name=real_name,
                created=created,
                country_code=country,
                state_code=state,
                city_code=city,
            )
    return steam_friend_infos


def get_state_or_city_codes(
    country_code: str, state_code: str | None = None
) -> dict[str, str]:
    """
    Returns the states or cities belonging to the codes given in the arguments as a dictionary, with IDs for keys and names for values.

    Args:
        country_code (str): The country code.
        state_code (str | None, optional): The state code if getting city names. Defaults to None.

    Returns:
        dict[str, str]: The associated codes and names for states or cities.
    """
    steam_countries_url: str = (
        f"https://steamcommunity.com/actions/QueryLocations/{country_code}{f'/{state_code}' if state_code is not None else ''}"
    )
    steam_countries_response: list[dict[str, Any]] = []
    state_or_city_codes: dict[str, str] = {}
    try:
        steam_countries_response = _get_response_from_steam_api(  # type: ignore
            steam_countries_url  # This URL returns a list of dictionaries
        )
        for item in steam_countries_response:
            if state_code is None:
                state_or_city_codes[item["statecode"]] = item["statename"]
                continue
            state_or_city_codes[str(item["cityid"])] = item["cityname"]
    except Exception:
        log.error(
            f"Failed to retrieve country information from Steam API for country '{country_code}'{f', state \'{state_code}\'' if state_code is not None else ''}",
            exc_info=True,
        )
    return state_or_city_codes


if __name__ == "__main__":
    from cache import get_blacklist, get_steam_folders
    from const import get_preferences_from_env

    preferences: dict[str, Any] = get_preferences_from_env()
    app_blacklist: list[int] = get_blacklist("app", preferences)
    option: str = input(
        "\n".join(
            (
                "Enter an option:",
                "fri - Get Steam friends information",
                "frl - Get Steam friends list",
                "ins - Get installed Steam apps",
                "non - Get non-Steam apps",
                "own - Get owned Steam apps\n",
            )
        )
    )
    if option == "fri":
        steamid64s: list[int] = [
            int(steamid64)
            for steamid64 in input("Enter steamid64s separated by commas: ").split(",")
        ]
        print(
            "\n".join(
                f"{k} {v}"
                for k, v in get_steam_friends_info(
                    preferences["STEAM_API_KEY"], steamid64s
                ).items()
            )
        )
    elif option == "frl":
        print(
            "\n".join(
                f"{k} {v}"
                for k, v in get_steam_friends_list(
                    preferences["STEAM_API_KEY"], int(preferences["STEAMID64"])
                ).items()
            )
        )
    elif option == "ins":
        for steam_folder in get_steam_folders(preferences):
            print(
                "\n".join(
                    f"{k} {v}"
                    for k, v in get_installed_steam_apps(
                        f"{steam_folder}steamapps", app_blacklist
                    ).items()
                )
            )
    elif option == "non":
        for steam_folder in get_steam_folders(preferences):
            print(
                "\n".join(
                    f"{k} {v}"
                    for k, v in get_non_steam_apps(
                        f"{steam_folder}userdata{DIR_SEP}{preferences['STEAM_USERDATA']}{DIR_SEP}config{DIR_SEP}shortcuts.vdf",
                        app_blacklist,
                    ).items()
                )
            )
    elif option == "own":
        print(
            "\n".join(
                f"{k} {v}"
                for k, v in get_owned_steam_apps(
                    preferences["STEAM_API_KEY"], int(preferences["STEAMID64"])
                ).items()
            )
        )
