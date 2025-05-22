from const import get_logger
from logging import Logger
from typing import Any

log: Logger = get_logger(__name__)


def execute_action(
    action: str, preferences: dict[str, Any], execute: bool = True
) -> None:
    """
    Executes the given action from the Steam extension.

    Args:
        action (str): The action to execute.
        preferences (dict[str, Any]): The preferences dictionary.
        execute (bool, optional): Whether to execute the action. If this is False, the action is only logged in the cache as having been launched. Defaults to True.
    """
    from cache import (
        build_cache,
        clear_cache,
        clear_images,
        datetime_to_timestamp,
        ensure_dict_key_is_dict,
        load_cache,
        save_cache,
    )
    from const import DIR_SEP
    from datetime import datetime
    from os import name as os_name
    from subprocess import Popen as SubprocessPopen
    from typing import Literal
    from query import get_launches

    command: str = "steam"
    if os_name == "nt":
        if not preferences["STEAM_FOLDER"].endswith(DIR_SEP):
            preferences["STEAM_FOLDER"] = f"{preferences['STEAM_FOLDER']}{DIR_SEP}"
        command = f'"{preferences["STEAM_FOLDER"]}steam.exe"'
    cache: dict[str, Any] = load_cache()
    cache_item: dict[str, Any]
    force_cache: bool | Literal["skip"] = False
    if action.startswith("APP"):
        app_id: int = int(action.split("/")[-1])
        if "apps" in cache.keys() and str(app_id) in cache["apps"].keys():
            cache_item = cache["apps"][str(app_id)]
        elif "nonSteam" in cache.keys() and str(app_id) in cache["nonSteam"].keys():
            cache_item = cache["nonSteam"][str(app_id)]
        else:
            log.error(f"Cannot execute '{action}', app ID {app_id} not found in cache")
            return
        if execute:
            app_action: str = f"{command} {action[3:]}"
            log.info(f"Launching app ID {app_id} via '{app_action}'")
            SubprocessPopen(app_action, shell=True)
    elif action.startswith("FRIEND"):
        friend_id: int = int(action[6:])
        if "friends" in cache.keys() and str(friend_id) in cache["friends"].keys():
            cache_item = cache["friends"][str(friend_id)]
        else:
            log.error(
                f"Cannot execute action, friend ID {friend_id} not found in cache"
            )
            return
        if execute:
            friend_action: str
            if preferences["FRIEND_ACTION"] == "chat":
                friend_action = f"{command} steam://friends/message/{friend_id}"
            elif preferences["FRIEND_ACTION"] == "profile":
                friend_action = f"{command} steam://url/SteamIDPage/{friend_id}"
            else:
                log.error(
                    f"Unknown default friend action '{preferences['FRIEND_ACTION']}'"
                )
                return
            log.info(f"Launching friend ID {friend_id} via '{friend_action}'")
            SubprocessPopen(friend_action, shell=True)
    elif action.startswith("s:") or action.startswith("w:"):
        to_run: str
        if action.startswith("s:"):
            to_run = f"{command} steam://{action[2:]}"
        elif os_name == "nt":  # "w:"
            to_run = f"xdg-open https://{action[2:]}"
        else:
            # TODO (low priority): Add support for opening URLs in Windows
            log.error("Opening URLs is not supported on this platform")
            return
        ensure_dict_key_is_dict(cache, "navs")
        ensure_dict_key_is_dict(cache["navs"], action)
        cache_item = cache["navs"][action]
        if execute:
            log.info(f"Launching navigation '{action}' via '{to_run}'")
            SubprocessPopen(to_run, shell=True)
    elif action == "update_cache":
        log.info("Updating cache")
        ensure_dict_key_is_dict(cache, "navs")
        ensure_dict_key_is_dict(cache["navs"], action)
        cache_item = cache["navs"][action]
        if execute:
            force_cache = True
    elif action == "clear_cache":
        log.info("Clearing cache")
        if execute:
            clear_cache()
            return
        ensure_dict_key_is_dict(cache, "navs")
        ensure_dict_key_is_dict(cache["navs"], action)
        cache_item = cache["navs"][action]
    elif action == "clear_images":
        log.info("Clearing images")
        ensure_dict_key_is_dict(cache, "navs")
        ensure_dict_key_is_dict(cache["navs"], action)
        cache_item = cache["navs"][action]
        if execute:
            clear_images()
            force_cache = "skip"
    elif action == "rebuild_cache":
        log.info("Rebuilding cache")
        if execute:
            clear_cache()
            clear_images()
            build_cache(preferences)
            return
        ensure_dict_key_is_dict(cache, "navs")
        ensure_dict_key_is_dict(cache["navs"], action)
        cache_item = cache["navs"][action]
    elif action in ("no_results", "error"):
        return
    else:
        log.error(f"Invalid action '{action}'")
        return
    launched: datetime | None
    times: int
    launched, times = get_launches(cache_item)
    times += 1
    cache_item["launched"] = f"{datetime_to_timestamp(launched)}x{times}"
    save_cache(cache, preferences)
    if execute and not isinstance(force_cache, str):  # != "skip"
        build_cache(preferences, force=force_cache)


if __name__ == "__main__":
    from const import get_preferences_from_env
    import sys

    preferences: dict[str, Any] = get_preferences_from_env()
    execute_action(" ".join(sys.argv[1:]), preferences)
