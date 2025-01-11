from const import EXTENSION_PATH
from logging import getLogger, Logger
from os.path import isfile

log: Logger = getLogger(__name__)


def download_steam_app_icon(appid: int, icon_url: str) -> None:
    """
    Downloads the Steam icon for the given app ID and saves it to the images/apps folder.

    Args:
        appid (int): The ID of the Steam app.
        icon_url (str): The URL of the Steam icon.
    """
    from os import remove
    from urllib.error import HTTPError
    from urllib.request import urlretrieve

    if isfile(f"{EXTENSION_PATH}images/apps/{appid}.jpg"):
        remove(f"{EXTENSION_PATH}images/apps/{appid}.jpg")
    try:
        urlretrieve(icon_url, f"{EXTENSION_PATH}images/apps/{appid}.jpg")
    except HTTPError:
        log.warning(f"Failed to download Steam icon for app ID {appid} at '{icon_url}'")


def build_cache(
    steamapps_folder: str,
    userdata_folder: str,
    steam_api_key: str,
    steamid64: str,
    time_before_update: str = "",
) -> None:
    """
    Builds the Steam extension cache if enough time has passed, saving it to cache.json. This includes non-Steam apps, installed Steam apps and owned Steam apps.

    Args:
        steamapps_folder (str): The path to the steamapps folder.
        userdata_folder (str): The path to the userdata folder of the current user.
        steam_api_key (str): The Steam API key to use.
        steamid64 (str): The Steam ID64 of the current user.
        time_before_update (str, optional): The time in minutes before the cache should be updated. Defaults to "".
    """
    from datetime import datetime, timedelta
    from get import (
        get_all_owned_steam_apps,
        get_installed_steam_apps,
        get_non_steam_apps
    )
    from json import dumps as json_dumps, loads as json_loads
    from os import mkdir
    from os.path import isdir
    from typing import Any

    log.info("Building Steam extension cache")
    cache: dict[str, Any] = {}
    try:
        log.debug("Loading cache.json")
        if isfile(f"{EXTENSION_PATH}cache.json"):
            with open(f"{EXTENSION_PATH}cache.json", "r", encoding="utf-8") as f:
                cache = json_loads(f.read())
        if "updated-last" in cache.keys() and time_before_update != "":
            log.debug("Checking updated last time")
            updated_last: datetime = datetime.strptime(
                cache["updated-last"], "%Y-%m-%d %H:%M:%S"
            )
            update_time: timedelta = timedelta(minutes=float(time_before_update))
            time_difference: timedelta = datetime.now() - updated_last
            if time_difference < update_time:
                log.info(
                    f"It is too soon to update the cache, wait {((update_time - time_difference).total_seconds() / 60):2f} minutes"
                )
                return
        log.debug("Getting non-Steam apps")
        non_steam_apps: list[tuple[int, str]] = get_non_steam_apps(userdata_folder)
        if "non-steam-apps" not in cache.keys():
            cache["non-steam-apps"] = {}
        else:
            existing_non_steam_apps: list[str] = list(cache["non-steam-apps"].keys())
            for existing_non_steam_app in existing_non_steam_apps:
                if existing_non_steam_app not in [app[0] for app in non_steam_apps]:
                    del cache["non-steam-apps"][existing_non_steam_app]
        for non_steam_app in non_steam_apps:
            appid: int = non_steam_app[0]
            name: str = non_steam_app[1]
            if str(appid) not in cache["non-steam-apps"].keys():
                cache["non-steam-apps"][str(appid)] = {"name": name}
        log.debug("Getting installed Steam apps")
        installed_steam_apps: list[tuple[int, str]] = get_installed_steam_apps(
            steamapps_folder
        )
        if "steam-apps" not in cache.keys():
            cache["steam-apps"] = {}
        else:
            existing_steam_apps: list[str] = list(cache["steam-apps"].keys())
            for existing_steam_app in existing_steam_apps:
                if existing_steam_app not in [app[0] for app in installed_steam_apps]:
                    if "installed" in cache["steam-apps"][existing_steam_app].keys():
                        del cache["steam-apps"][existing_steam_app]["installed"]
        for installed_steam_app in installed_steam_apps:
            appid: int = installed_steam_app[0]
            name: str = installed_steam_app[1]
            if str(appid) in cache["steam-apps"].keys():
                cache["steam-apps"][str(appid)]["installed"] = True
                continue
            cache["steam-apps"][str(appid)] = {"name": name, "installed": True}
        log.debug("Saving cache.json before querying Steam APIs")
        cache["updated-last"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(f"{EXTENSION_PATH}cache.json", "w", encoding="utf-8") as f:
            f.write(json_dumps(cache, indent=4))
        owned_steam_apps: dict[int, dict[str, str | int]] | str = get_all_owned_steam_apps(
            steam_api_key, steamid64
        )
        app_icons_to_download: list[tuple[int, int]] = []
        if isinstance(owned_steam_apps, str):
            if owned_steam_apps == "Unauthorized":
                raise ValueError("Steam API key is invalid")
            elif owned_steam_apps == "Bad Request":
                raise ValueError("Steam ID is invalid")
            else:
                raise ConnectionError(owned_steam_apps)
        else:
            if not isdir(f"{EXTENSION_PATH}images/apps"):
                mkdir(f"{EXTENSION_PATH}images/apps")
            for appid, appinfo in owned_steam_apps.items():
                if str(appid) not in cache["steam-apps"].keys():
                    cache["steam-apps"][str(appid)] = {
                        "name": appinfo["name"],
                        "icon-hash": appinfo["icon-hash"],
                        "playtime-total": appinfo["playtime-total"],
                    }
                    log.debug(f"Downloading Steam icon for app ID {appid}, not in cache")
                    app_icons_to_download.append((appid, appinfo["icon-url"]))
                    continue
                cache["steam-apps"][str(appid)]["name"] = appinfo["name"]
                cache["steam-apps"][str(appid)]["playtime-total"] = appinfo["playtime-total"]
                # TODO: Check hashes of icons for difference if possible
                if "icon-hash" != cache["steam-apps"][str(appid)]["icon-hash"]:
                    log.warning(f"Icon hash for app ID {appid} does not match cache: '{appinfo['icon-hash']}' != '{cache['steam-apps'][str(appid)]['icon-hash']}'")
                if (
                    "icon-hash" not in cache["steam-apps"][str(appid)].keys()
                    or not isfile(f"{EXTENSION_PATH}images/apps/{appid}.jpg")
                ):
                    log.debug(f"Downloading Steam icon for app ID {appid}, icon does not exist")
                    app_icons_to_download.append((appid, appinfo["icon-url"]))
                cache["steam-apps"][str(appid)]["icon-hash"] = appinfo["icon-hash"]
            log.debug("Saving cache.json after querying Steam APIs")
            cache["updated-last"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(f"{EXTENSION_PATH}cache.json", "w", encoding="utf-8") as f:
                f.write(json_dumps(cache, indent=4))
        log.info("Steam extension cache built")
        if len(app_icons_to_download) >= 1:
            log.info(f"Downloading {len(app_icons_to_download)} Steam app icons")
            for download in app_icons_to_download:
                download_steam_app_icon(download[0], download[1])
            log.info("Steam app icons downloaded")
    except Exception as err:
        log.error(f"Failed to build Steam extension cache ({err.__class__.__name__}): {err}")
