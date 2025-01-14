"""
This module contains functions for retrieving data from Steam for the purposes of caching it. This data includes:
- Installed Steam apps
- Owned Steam apps
- Non-Steam apps
"""

from const import get_logger
from datetime import datetime
from logging import Logger
from typing import Any, TypeAlias, TypedDict, Union

log: Logger = get_logger(__name__)

NestedStrDict: TypeAlias = dict[str, Union[str, "NestedStrDict"]]


def vdf_to_dict(path: str) -> dict[str, NestedStrDict]:
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
        if quote_count == 2:
            vdf_levels.append(line.split('"')[1])
            if len(vdf_levels) == 1:
                if len(vdf_dict) != 0:
                    raise KeyError(
                        f"Unexpectedly found additional top-level key '{vdf_levels[0]}' on line {index + 1}"
                    )
                vdf_dict[vdf_levels[0]] = {}
            else:
                add_dict: NestedStrDict = vdf_dict[vdf_levels[0]]
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
            add_dict: NestedStrDict = vdf_dict[vdf_levels[0]]
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
        install_dir (str): The name of the folder containing the Steam app.
        size_on_disk (int): The size of the Steam app on disk in bytes.
        last_updated (datetime | None): The time the app was last updated, or None if not updated.
        last_launched (datetime | None): The time the app was last launched, or None if not launched.
    """

    name: str
    install_dir: str
    size_on_disk: int
    last_updated: datetime | None
    last_launched: datetime | None


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
            app_vdf: dict[str, NestedStrDict] = vdf_to_dict(
                path_join(steamapps_folder, appmanifest_file)
            )
            name: str = app_vdf["AppState"]["name"].strip()  # type: ignore
            install_dir: str = app_vdf["AppState"]["installdir"]  # type: ignore
            last_updated_str: str = app_vdf["AppState"]["LastUpdated"]  # type: ignore
            last_updated: datetime | None = (
                datetime.fromtimestamp(int(last_updated_str))
                if last_updated_str != "0"
                else None
            )
            last_launched_str: str = app_vdf["AppState"]["LastPlayed"]  # type: ignore
            last_launched: datetime | None = (
                datetime.fromtimestamp(int(last_launched_str))
                if last_launched_str != "0"
                else None
            )
            size_on_disk_str: str = app_vdf["AppState"]["SizeOnDisk"]  # type: ignore
            if size_on_disk_str == "0":
                log.debug("Game has not finished installing, using BytesToStage")
                size_on_disk_str = app_vdf["AppState"]["BytesToStage"]  # type: ignore
            size_on_disk: int = int(size_on_disk_str)
            installed_steam_apps[app_id] = InstalledSteamApp(
                name=name,
                install_dir=install_dir,
                size_on_disk=size_on_disk,
                last_updated=last_updated,
                last_launched=last_launched,
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
        size_on_disk (int | None): The size of the non-Steam app on disk in bytes.
        last_launched (datetime | None): The time the app was last launched, or None if not launched.
    """

    name: str
    exe: str | None
    size_on_disk: int | None
    last_launched: datetime | None


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
    from subprocess import check_output as subprocess_check_output

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
            exe: str | None = (
                buffer[exe_start:cursor].decode(errors="ignore").strip('"')
            )
            if os.name != "nt":
                exe = (
                    subprocess_check_output(f"type {exe}", shell=True)
                    .decode()
                    .split(" is ")[1]
                    .strip()
                )
            size_on_disk: int | None = None
            if isfile(exe):
                size_on_disk = getsize(exe)
            else:
                log.warning(f"Non-Steam app executable '{exe}' does not exist")
                exe = None
            shortcuts_dict[shortcut_id]["exe"] = exe
            shortcuts_dict[shortcut_id]["size_on_disk"] = size_on_disk
            cursor += 1
        if cursor_match("\x02LastPlayTime\x00"):
            last_launched_int: int = int.from_bytes(
                buffer[cursor : cursor + 4], "little"
            )
            shortcuts_dict[shortcut_id]["last_launched"] = (
                datetime.fromtimestamp(last_launched_int)
                if last_launched_int != 0
                else None
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
                size_on_disk=app_info["size_on_disk"],
                last_launched=app_info["last_launched"],
            )
        except Exception:
            log.error(
                f"Failed to parse non-Steam app with shortcut ID {shortcut_id}",
                exc_info=True,
            )
    return non_steam_apps


class OwnedSteamApp(TypedDict):
    """
    A dictionary representation of an owned Steam app.

    Args:
        name (str): The name of the Steam app.
        total_playtime (int): The total playtime of the Steam app in minutes.
        icon_hash (str | None): The hash of the icon of the Steam app, or None if no icon is available.
    """

    name: str
    total_playtime: int
    icon_hash: str | None


def get_owned_steam_apps(api_key: str, steamid64: str) -> dict[int, OwnedSteamApp]:
    """
    Returns a dictionary of owned Steam apps, retrieved from the Steam API.

    Args:
        api_key (str): The Steam API key.
        steamid64 (str): The steamid64 of the user.

    Returns:
        dict[int, OwnedSteamApp]: The dictionary of owned Steam apps.
    """
    from http.client import HTTPSConnection
    from json import loads as json_loads

    log.info(f"Getting owned Steam apps from Steam API for user {steamid64}")
    owned_steam_apps: dict[int, OwnedSteamApp] = {}
    owned_apps_url: str = (
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key="
        + api_key
        + "&steamid="
        + steamid64
        + "&include_appinfo=1&include_played_free_games=1&format=json"
    )
    conn: HTTPSConnection = HTTPSConnection("api.steampowered.com")
    conn.request("GET", owned_apps_url)
    response: bytes = conn.getresponse().read()
    if (
        response
        == b"<html><head><title>Unauthorized</title></head><body><h1>Unauthorized</h1>Access is denied. Retrying will not help. Please verify your <pre>key=</pre> parameter.</body></html>"
    ):
        log.error(f"Steam API key '{api_key}' is invalid")
        return {}
    elif (
        response
        == b"<html><head><title>Bad Request</title></head><body><h1>Bad Request</h1>Please verify that all required parameters are being sent</body></html>"
    ):
        log.error(f"User steamid64 '{steamid64}' is invalid")
        return {}
    for owned_steam_app in json_loads(response)["response"]["games"]:
        app_id: int = owned_steam_app["appid"]
        name: str = owned_steam_app["name"].strip()
        total_playtime: int = owned_steam_app["playtime_forever"]
        icon_hash: str | None = owned_steam_app["img_icon_url"]
        if icon_hash == "":
            icon_hash = None
        owned_steam_apps[app_id] = OwnedSteamApp(
            name=name,
            total_playtime=total_playtime,
            icon_hash=icon_hash,
        )
    return owned_steam_apps


if __name__ == "__main__":
    from cache import get_blacklist
    from const import DIR_SEP, get_preferences_from_env

    preferences: dict[str, Any] = get_preferences_from_env()
    app_blacklist: list[int] = get_blacklist("app", preferences)
    option: str = input(
        "\n".join(
            (
                "Enter an option:",
                "ins - Get installed Steam apps",
                "non - Get non-Steam apps",
                "own - Get owned Steam apps\n",
            )
        )
    )
    if option == "ins":
        print(
            "\n".join(
                f"{k} {v}"
                for k, v in get_installed_steam_apps(
                    f"{preferences["STEAM_FOLDER"]}steamapps", app_blacklist
                ).items()
            )
        )
    elif option == "non":
        print(
            "\n".join(
                f"{k} {v}"
                for k, v in get_non_steam_apps(
                    f"{preferences["STEAM_FOLDER"]}userdata{DIR_SEP}{preferences["STEAM_USERDATA_ID"]}{DIR_SEP}config{DIR_SEP}shortcuts.vdf",
                    app_blacklist,
                ).items()
            )
        )
    elif option == "own":
        print(
            "\n".join(
                f"{k} {v}"
                for k, v in get_owned_steam_apps(
                    preferences["STEAM_API_KEY"],
                    preferences["STEAMID64"],
                ).items()
            )
        )
