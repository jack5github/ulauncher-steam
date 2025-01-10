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
    def on_event(self, event, _):
        manifest: dict[str, Any] = event.preferences
        log.debug("Steam extension started, building cache")
        build_cache(
            steamapps_folder=manifest["steamapps-folder"],
            userdata_folder=manifest["userdata-folder"],
            steam_api_key=manifest["api-key"],
            steamid64=manifest["steam-id"],
            time_before_update=manifest["time-before-update"],
        )


class SteamExtensionQueryListener(EventListener):
    def on_event(self, _, extension) -> RenderResultListAction:
        from query import SteamExtensionItem, steam_extension_event

        log.debug("Entering Steam extension event listener main function")
        manifest: dict[str, Any] = extension.preferences
        items: list[SteamExtensionItem] = steam_extension_event(manifest, event.get_argument())
        log.debug("Steam extension event listener main function finished")
        result_items: list[ExtensionResultItem] = []
        for item in items:
            log.debug(f"Converting to ExtensionResultItem: {repr(item)}")
            result_dict: dict[str, Any] = item.to_result_dict()
            on_enter_class: RunScriptAction | ExtensionCustomAction | HideWindowAction = (
                RunScriptAction(result_dict["on_enter"]["argument"])
                if result_dict["on_enter"]["class"] == "RunScriptAction"
                else ExtensionCustomAction([
                    manifest["steamapps-folder"],
                    manifest["userdata-folder"],
                    manifest["api-key"],
                    manifest["steam-id"],
                    manifest["time-before-update"],
                ])
                if result_dict["on_enter"]["class"] == "ExtensionCustomAction"
                else HideWindowAction()
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
            steamapps_folder=manifest["steamapps-folder"],
            userdata_folder=manifest["userdata-folder"],
            steam_api_key=manifest["api-key"],
            steamid64=manifest["steam-id"],
        )


if __name__ == '__main__':
    SteamExtension().run()
