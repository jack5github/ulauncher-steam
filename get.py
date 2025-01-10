from logging import getLogger, Logger
from os.path import join as path_join

log: Logger = getLogger(__name__)


def get_installed_steam_apps(steamapps_folder: str) -> list[tuple[int, str]]:
    """
    Returns the names and app IDs of all installed Steam apps.

    Args:
        steamapps_folder (str): The path to the steamapps folder.

    Returns:
        list[tuple[int, str]]: A list of tuples containing the app ID and name of all installed Steam apps.
    """
    from os import listdir

    # Get all appmanifest_#.acf files in the steamapps folder
    appmanifest_files: tuple[str, ...] = tuple(
        file for file in listdir(steamapps_folder) if file.startswith("appmanifest_") and file.endswith(".acf")
    )
    log.debug(appmanifest_files)
    # Each file is a JSON-like object using the following syntax:
    """
    "AppState"
    {
        "Key"       "Value"
        "NumKey"    "0"
        "NestedKey"
        {
            "Key"   "Value"
        }
    }
    """
    installed_steam_apps: list[tuple[int, str]] = []
    for file in appmanifest_files:
        log.debug(path_join(steamapps_folder, file))
        with open(path_join(steamapps_folder, file), "r", encoding="utf-8") as f:
            name: str | None = None
            appid: int | None = None
            # Extract all relevant keys and values from the JSON-like object
            for line in f.readlines():
                line = line.strip()
                log.debug(line)
                if line.startswith('"name"'):
                    name = line[1:].split('"')[2]
                    log.debug(f"Name found: {name}")
                if line.startswith('"appid"'):
                    appid = int(line[1:].split('"')[2])
                    log.debug(f"App ID found: {appid}")
                if name is not None and appid is not None:
                    installed_steam_apps.append((appid, name))
                    break
    log.debug(installed_steam_apps)
    return installed_steam_apps


# TODO: Make this more efficient by reducing number of keys to check for
def get_non_steam_apps(userdata_folder: str) -> list[tuple[int, str]]:
    """
    Returns the names and app IDs of all non-Steam apps.

    Args:
        userdata_folder (str): The path to the Steam userdata folder.

    Returns:
        list[tuple[int, str]]: A list of tuples containing the app ID and name of all non-Steam apps for the current user.
    """
    from binascii import hexlify
    from typing import Any

    # Locate the user shortcuts file
    user_shortcuts_file: str = path_join(userdata_folder, "config")
    user_shortcuts_file = path_join(user_shortcuts_file, "shortcuts.vdf")
    log.debug(user_shortcuts_file)
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
            buffer[cursor - next_shortcut_id_len:cursor].decode(errors="ignore") == str(shortcut_id + 1)
        ):
            shortcut_id += 1
            cursor += 1
            continue
        vdf_keys: tuple[str, ...] = "appid", "AppName", "Exe", "StartDir", "Icon"
        try:
            vdf_key: str = next(key for key in vdf_keys if buffer[cursor - len(key):cursor].decode(errors="ignore") == key)

            def insert_key_value(value: str | int) -> None:
                nonlocal shortcuts

                if shortcut_id not in shortcuts.keys():
                    shortcuts[shortcut_id] = {}
                shortcuts[shortcut_id][vdf_key] = value

            if vdf_key == "appid":
                # The next four bytes are the app ID (reversed), followed by 02 00 00 00
                insert_key_value(int.from_bytes(buffer[cursor + 4:cursor:-1] + b"\x02\x00\x00\x00", "big"))
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
            insert_key_value(buffer[cursor + 1:value_cursor].decode(errors="ignore"))
        except StopIteration:
            pass
        cursor += 1
    log.debug(shortcuts)
    non_steam_apps: list[tuple[int, str]] = []
    for shortcut in shortcuts.values():
        non_steam_apps.append((shortcut["appid"], shortcut["AppName"], ))
    log.debug(non_steam_apps)
    return non_steam_apps


def get_all_owned_steam_apps(api_key: str, steam_id64: str) -> dict[int, dict[str, str | int]]:
    """
    Returns the names, app IDs and icon URLs of all owned Steam apps.

    Args:
        api_key (str): The Steam API key.
        steam_id64 (str): The Steam ID64 of the user.

    Returns:
        dict[int, dict[str, str | int]]: A dictionary containing various information about all owned Steam apps for the current user.
    """
    from http.client import HTTPSConnection
    from json import loads as json_loads

    owned_games_url: str = (
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" +
        api_key +
        "&steamid=" +
        steam_id64 +
        "&include_appinfo=1&include_played_free_games=1&format=json"
    )
    conn: HTTPSConnection = HTTPSConnection("api.steampowered.com")
    conn.request("GET", owned_games_url)
    response: bytes = conn.getresponse().read()
    owned_games: dict[int, dict[str, str | int]] = {}
    for game in json_loads(response)["response"]["games"]:
        owned_games[game["appid"]] = {
            "name": game["name"],
            "playtime-2-weeks": game["playtime_2weeks"],
            "playtime-total": game["playtime_forever"],
            "icon-url": f"https://media.steampowered.com/steamcommunity/public/images/apps/{game['appid']}/{game['img_icon_url']}.jpg",
            "icon-hash": game["img_icon_url"],
        }
    log.debug(owned_games)
    return owned_games
