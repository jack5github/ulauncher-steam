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
    from cache import build_cache, clear_cache, load_cache, save_cache
    import os

    cache: dict[str, Any] = load_cache()
    if action.startswith("APP"):
        app_id: int = int(action.split("/")[-1])
        cache_app: dict[str, Any]
        if "steam_apps" in cache.keys() and str(app_id) in cache["steam_apps"].keys():
            cache_app = cache["steam_apps"][str(app_id)]
        elif "non_steam_apps" in cache.keys() and str(app_id) in cache["non_steam_apps"].keys():
            cache_app = cache["non_steam_apps"][str(app_id)]
        else:
            log.error(f"Cannot execute '{action}', app ID {app_id} not found in cache")
            return
        log.info(f"Launching app ID {app_id}")
        os.system(action[3:])
        cache_app["last_launched"] = datetime.now().timestamp()
        if "times_launched" in cache_app.keys():
            cache_app["times_launched"] += 1
        else:
            cache_app["times_launched"] = 1
    elif action.startswith("NAV"):
        nav_action: str = action[3:]
        log.info(f"Launching navigation '{nav_action}'")
        os.system(nav_action)
        if "steam_navs" not in cache.keys():
            cache["steam_navs"] = {}
        if nav_action not in cache["steam_navs"].keys():
            cache["steam_navs"][nav_action] = {}
        cache_nav: dict[str, Any] = cache["steam_navs"][nav_action]
        cache_nav["last_launched"] = datetime.now().timestamp()
        if "times_launched" in cache_nav.keys():
            cache_nav["times_launched"] += 1
        else:
            cache_nav["times_launched"] = 1
    elif action == "update_cache":
        log.info("Updating cache")
        build_cache(preferences, force=True)
        return
    elif action == "clear_cache":
        log.info("Clearing cache")
        clear_cache()
        return
    elif action == "rebuild_cache":
        log.info("Rebuilding cache")
        clear_cache()
        build_cache(preferences)
        return
    save_cache(cache, preferences)
    build_cache(preferences)
