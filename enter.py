from const import get_logger
from logging import Logger
from typing import Any

log: Logger = get_logger(__name__)


def execute_action(action: str, preferences: dict[str, Any]) -> None:
    """
    Executes the given action from the Steam extension.

    Args:
        action (str): The action to execute.
        preferences (dict[str, Any]): The preferences dictionary.
    """
    from cache import build_cache, clear_cache, clear_images, load_cache, save_cache
    from datetime import datetime
    from subprocess import Popen as SubprocessPopen

    cache: dict[str, Any] = load_cache()
    if action.startswith("APP"):
        app_id: int = int(action.split("/")[-1])
        cache_app: dict[str, Any]
        if "apps" in cache.keys() and str(app_id) in cache["apps"].keys():
            cache_app = cache["apps"][str(app_id)]
        elif "nonSteam" in cache.keys() and str(app_id) in cache["nonSteam"].keys():
            cache_app = cache["nonSteam"][str(app_id)]
        else:
            log.error(f"Cannot execute '{action}', app ID {app_id} not found in cache")
            return
        app_action: str = f"steam {action[3:]}"
        log.info(f"Launching app ID {app_id} via '{app_action}'")
        SubprocessPopen(app_action, shell=True)
        cache_app["launched"] = datetime.now().timestamp()
    elif action.startswith("FRIEND"):
        friend_id: int = int(action[6:])
        cache_friend: dict[str, Any]
        if "friends" in cache.keys() and str(friend_id) in cache["friends"].keys():
            cache_friend = cache["friends"][str(friend_id)]
        else:
            log.error(
                f"Cannot execute action, friend ID {friend_id} not found in cache"
            )
            return
        friend_action: str
        if preferences["FRIEND_ACTION"] == "chat":
            friend_action = f"steam steam://friends/message/{friend_id}"
        elif preferences["FRIEND_ACTION"] == "profile":
            friend_action = f"steam steam://url/SteamIDPage/{friend_id}"
        else:
            log.error(f"Unknown default friend action '{preferences['FRIEND_ACTION']}'")
            return
        log.info(f"Launching friend ID {friend_id} via '{friend_action}'")
        SubprocessPopen(friend_action, shell=True)
        cache_friend["launched"] = datetime.now().timestamp()
    elif action.startswith("NAV"):
        nav_action: str = action[3:]
        nav_execute: str = f"steam steam://{nav_action}"
        log.info(f"Launching navigation '{nav_action}' via '{nav_execute}'")
        SubprocessPopen(nav_execute, shell=True)
        if "navs" not in cache.keys():
            cache["navs"] = {}
        if f"s:{nav_action}" not in cache["navs"].keys():
            cache["navs"][f"s:{nav_action}"] = {}
        cache_nav: dict[str, Any] = cache["navs"][f"s:{nav_action}"]
        cache_nav["launched"] = datetime.now().timestamp()
    elif action == "update_cache":
        log.info("Updating cache")
        build_cache(preferences, force=True)
        return
    elif action == "clear_cache":
        log.info("Clearing cache")
        clear_cache()
        return
    elif action == "clear_images":
        log.info("Clearing images")
        clear_images()
        return
    elif action == "rebuild_cache":
        log.info("Rebuilding cache")
        clear_cache()
        clear_images()
        build_cache(preferences)
        return
    elif action == "no_results":
        return
    else:
        log.error(f"Invalid action '{action}'")
        return
    save_cache(cache, preferences)
    build_cache(preferences)


if __name__ == "__main__":
    from const import get_preferences_from_env
    import sys

    preferences: dict[str, Any] = get_preferences_from_env()
    execute_action(" ".join(sys.argv[1:]), preferences)
