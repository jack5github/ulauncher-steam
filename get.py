"""
This module contains functions for retrieving data from Steam for the purposes of caching it. This data includes:
- Installed Steam apps
- Owned Steam apps
- Non-Steam apps
"""

from const import EXTENSION_PATH
from datetime import datetime
from logging import getLogger, Logger
from logging.config import fileConfig as logging_fileConfig
import os
from os.path import join as path_join
from typing import TypeAlias, TypedDict, Union

if os.name == "nt":
    try:
        logging_fileConfig(f"{EXTENSION_PATH}logging.conf", disable_existing_loggers=False)
    except FileNotFoundError:
        pass
log: Logger = getLogger(__name__)

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
        last_updated (datetime | None): The time the app was last updated, or None if not updated.
        last_launched (datetime | None): The time the app was last launched, or None if not launched.
        size_on_disk (int): The size of the Steam app on disk in bytes.
    """

    name: str
    install_dir: str
    last_updated: datetime | None
    last_launched: datetime | None
    size_on_disk: int


def get_installed_steam_apps(
    steamapps_folder: str, app_blacklist: list[int]
) -> dict[int, InstalledSteamApp]:
    """
    Returns a list of InstalledSteamApp instances for all installed Steam apps.

    Args:
        steamapps_folder (str): The path to the steamapps folder.
        app_blacklist (list[int]): A list of app IDs to ignore.

    Returns:
        dict[int, InstalledSteamApp]: A list of InstalledSteamApp instances for all installed Steam apps, indexed by app ID.
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
        app_id: int = int(appmanifest_file.split("_")[1].split(".")[0])
        if app_id in app_blacklist:
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
            size_on_disk_str = app_vdf["AppState"]["BytesToStage"]  # type: ignore
        size_on_disk: int = int(size_on_disk_str)
        installed_steam_apps[app_id] = InstalledSteamApp(
            name=name,
            install_dir=install_dir,
            last_updated=last_updated,
            last_launched=last_launched,
            size_on_disk=size_on_disk,
        )
    return installed_steam_apps


class NonSteamApp(TypedDict):
    """
    A dictionary representation of a non-Steam app.

    Args:
        name (str): The name of the non-Steam app.
        exe (str): The location of the non-Steam app.
        last_launched (datetime | None): The time the app was last launched, or None if not launched.
        size_on_disk (int): The size of the non-Steam app on disk in bytes.
    """

    name: str
    exe: str
    last_launched: datetime | None
    size_on_disk: int


# TODO: Make this more efficient by reducing number of keys to check for
def get_non_steam_apps(
    userdata_folder: str, app_blacklist: list[int]
) -> dict[int, NonSteamApp]:
    from binascii import hexlify
    from typing import Any

    # Locate the user shortcuts file
    user_shortcuts_file: str = path_join(userdata_folder, "config")
    user_shortcuts_file = path_join(user_shortcuts_file, "shortcuts.vdf")
    # Shortcuts are represented as hex, flanked by keys in plain English
    # https://steamcommunity.com/discussions/forum/1/5560306947036116992/
    buffer: bytearray
    with open(user_shortcuts_file, "rb") as f:
        buffer = bytearray.fromhex(hexlify(f.read()).decode())
    cursor: int = 20
    shortcut_id: int = 0
    shortcuts: dict[int, dict[str, Any]] = {}
    while cursor < len(buffer):
        if buffer[cursor] != 0:
            cursor += 1
            continue
        next_shortcut_id_len: int = len(str(shortcut_id + 1))
        if buffer[cursor - next_shortcut_id_len - 1] == 0 and (
            buffer[cursor - next_shortcut_id_len : cursor].decode(errors="ignore")
            == str(shortcut_id + 1)
        ):
            shortcut_id += 1
            cursor += 1
            continue
        # TODO: Get last launched time and get size on disk (os.path.getsize)
        vdf_keys: tuple[str, ...] = "appid", "AppName", "Exe", "StartDir"
        try:
            vdf_key: str = next(
                key
                for key in vdf_keys
                if buffer[cursor - len(key) : cursor].decode(errors="ignore") == key
            )

            def insert_key_value(value: str | int) -> None:
                nonlocal shortcuts

                if shortcut_id not in shortcuts.keys():
                    shortcuts[shortcut_id] = {}
                shortcuts[shortcut_id][vdf_key] = value

            if vdf_key == "appid":
                # The next four bytes are the app ID (reversed), followed by 02 00 00 00
                insert_key_value(
                    int.from_bytes(
                        buffer[cursor + 4 : cursor : -1] + b"\x02\x00\x00\x00", "big"
                    )
                )
                cursor += 1
                continue
            value_cursor: int = cursor + 1
            if vdf_key == "Icon" and buffer[value_cursor] == 0:
                # No icon
                cursor += 1
                continue
            # Everything until the next zero_byte is the value
            while buffer[value_cursor] != 0:
                value_cursor += 1
            insert_key_value(buffer[cursor + 1 : value_cursor].decode(errors="ignore"))
        except StopIteration:
            pass
        cursor += 1
    non_steam_apps: dict[int, NonSteamApp] = {
        v["appid"]: NonSteamApp(
            name=v["AppName"].strip(),
            exe=v["Exe"],
            last_launched=None,
            size_on_disk=0,
        )
        for v in shortcuts.values()
        if v["appid"] not in app_blacklist
    }
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


def get_owned_steam_apps(api_key: str, steam_id64: str) -> dict[int, OwnedSteamApp]:
    """
    Returns a dictionary of owned Steam apps.

    Args:
        api_key (str): The Steam API key.
        steam_id64 (str): The steamid64 of the user.

    Raises:
        ValueError: If the Steam API key is invalid.
        ValueError: If the steamid64 is invalid.

    Returns:
        dict[int, OwnedSteamApp]: The dictionary of owned Steam apps.
    """
    from http.client import HTTPSConnection
    from json import loads as json_loads

    owned_steam_apps: dict[int, OwnedSteamApp] = {}
    owned_apps_url: str = (
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key="
        + api_key
        + "&steamid="
        + steam_id64
        + "&include_appinfo=1&include_played_free_games=1&format=json"
    )
    conn: HTTPSConnection = HTTPSConnection("api.steampowered.com")
    conn.request("GET", owned_apps_url)
    response: bytes = conn.getresponse().read()
    if (
        response
        == b"<html><head><title>Unauthorized</title></head><body><h1>Unauthorized</h1>Access is denied. Retrying will not help. Please verify your <pre>key=</pre> parameter.</body></html>"
    ):
        raise ValueError(f"Steam API key '{api_key}' is invalid")
    elif (
        response
        == b"<html><head><title>Bad Request</title></head><body><h1>Bad Request</h1>Please verify that all required parameters are being sent</body></html>"
    ):
        raise ValueError(f"User steamid64 '{steam_id64}' is invalid")
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
