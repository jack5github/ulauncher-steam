from cache import build_cache
from logging import getLogger, Logger
from typing import Any
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from ulauncher.api.shared.event import (
    ItemEnterEvent,
    KeywordQueryEvent,
    PreferencesEvent,
)
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

log: Logger = getLogger(__name__)


class SteamExtension(Extension):
    def __init__(self) -> None:
        log.debug("Initialising Steam extension")
        super().__init__()
        self.subscribe(PreferencesEvent, SteamExtensionStartListener())
        self.subscribe(KeywordQueryEvent, SteamExtensionQueryListener())
        self.subscribe(ItemEnterEvent, SteamExtensionItemListener())
        log.info("Steam extension initialised")


class SteamExtensionStartListener(EventListener):
    def on_event(self, event, _) -> None:
        manifest: dict[str, Any] = event.preferences
        log.debug("Steam extension started, building cache")
        build_cache(
            steamapps_folder=manifest["STEAMAPPS_FOLDER"],
            userdata_folder=manifest["USERDATA_FOLDER"],
            steam_api_key=manifest["STEAM_API_KEY"],
            steamid64=manifest["STEAMID64"],
            time_before_update=manifest["CACHE_UPDATE_DELAY"],
        )


class SteamExtensionQueryListener(EventListener):
    def on_event(self, event, extension) -> RenderResultListAction:
        from query import SteamExtensionItem, steam_extension_event

        log.debug("Entering Steam extension event listener main function")
        manifest: dict[str, Any] = extension.preferences
        items: list[SteamExtensionItem] = steam_extension_event(
            manifest, event.get_argument()
        )
        log.debug("Steam extension event listener main function finished")
        result_items: list[ExtensionResultItem] = []
        for item in items:
            log.debug(f"Converting to ExtensionResultItem: {repr(item)}")
            # TODO: Add tracking of last time item was used and number of times used
            result_dict: dict[str, Any] = item.to_result_dict()
            on_enter_class: (
                RunScriptAction | ExtensionCustomAction | HideWindowAction
            ) = (
                RunScriptAction(result_dict["on_enter"]["argument"])
                if result_dict["on_enter"]["class"] == "RunScriptAction"
                else (
                    ExtensionCustomAction(
                        [
                            manifest["STEAMAPPS_FOLDER"],
                            manifest["USERDATA_FOLDER"],
                            manifest["STEAM_API_KEY"],
                            manifest["STEAMID64"],
                            manifest["CACHE_UPDATE_DELAY"],
                        ]
                    )
                    if result_dict["on_enter"]["class"] == "ExtensionCustomAction"
                    else HideWindowAction()
                )
            )
            result_items.append(
                ExtensionResultItem(
                    icon=result_dict["icon"],
                    name=result_dict["name"],
                    description=result_dict["description"],
                    on_enter=on_enter_class,
                )
            )
        return RenderResultListAction(result_items)


class SteamExtensionItemListener(EventListener):
    def on_event(self, event, extension) -> None:
        manifest: dict[str, Any] = extension.preferences

        log.debug("User requested to rebuild cache")
        build_cache(
            steamapps_folder=manifest["STEAMAPPS_FOLDER"],
            userdata_folder=manifest["USERDATA_FOLDER"],
            steam_api_key=manifest["STEAM_API_KEY"],
            steamid64=manifest["STEAMID64"],
        )


if __name__ == "__main__":
    SteamExtension().run()
