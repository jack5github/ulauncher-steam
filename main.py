from cache import build_cache
from const import get_logger
from logging import Logger
from typing import Any
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import (
    ItemEnterEvent,
    KeywordQueryEvent,
    PreferencesEvent,
)
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

log: Logger = get_logger(__name__)


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
        from const import EXTENSION_PATH
        from query import SteamExtensionItem, query_cache

        log.debug("Entering Steam extension event listener main function")
        preferences: dict[str, Any] = extension.preferences
        items: list[SteamExtensionItem] = query_cache(preferences, event.get_argument())
        log.debug("Steam extension event listener main function finished")
        result_items: list[ExtensionResultItem] = []
        for item in items:
            log.debug(f"Converting to ExtensionResultItem: {item}")
            result_items.append(
                ExtensionResultItem(
                    icon=item.icon.replace(EXTENSION_PATH, ""),
                    name=item.get_name(),
                    description=item.get_description(),
                    on_enter=ExtensionCustomAction(item.get_action()),
                )
            )
        return RenderResultListAction(result_items)


class SteamExtensionItemListener(EventListener):
    # TODO: Add tracking of last time item was used and number of times used
    def on_event(self, event, extension) -> None:
        log.debug("User requested to rebuild cache")
        preferences: dict[str, Any] = extension.preferences
        build_cache(preferences, force=True)


if __name__ == "__main__":
    SteamExtension().run()
