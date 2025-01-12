from cache import build_cache
from const import EXTENSION_PATH
from logging import getLogger, Logger
from logging.config import fileConfig as logging_fileConfig
import os
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

if os.name == "nt":
    try:
        logging_fileConfig(f"{EXTENSION_PATH}logging.conf", disable_existing_loggers=False)
    except FileNotFoundError:
        pass
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
        log.debug("Steam extension started, building cache")
        preferences: dict[str, Any] = event.preferences
        build_cache(preferences)


class SteamExtensionQueryListener(EventListener):
    def on_event(self, event, extension) -> RenderResultListAction:
        from query import SteamExtensionItem, steam_extension_event

        log.debug("Entering Steam extension event listener main function")
        preferences: dict[str, Any] = extension.preferences
        items: list[SteamExtensionItem] = steam_extension_event(
            preferences, event.get_argument()
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
                    ExtensionCustomAction(preferences)
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
        log.debug("User requested to rebuild cache")
        preferences: dict[str, Any] = extension.preferences
        build_cache(preferences, force=True)


if __name__ == "__main__":
    SteamExtension().run()
