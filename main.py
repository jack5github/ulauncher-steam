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
    """
    The uLauncher Steam extension class.
    """
    def __init__(self) -> None:
        """
        Initialises a new SteamExtension instance.
        """
        log.debug("Initialising Steam extension")
        super().__init__()
        self.subscribe(PreferencesEvent, SteamExtensionStartListener())
        self.subscribe(KeywordQueryEvent, SteamExtensionQueryListener())
        self.subscribe(ItemEnterEvent, SteamExtensionItemListener())
        log.info("Steam extension initialised")


class SteamExtensionStartListener(EventListener):
    def on_event(self, event, _) -> None:
        """
        Called when the Steam extension is started.

        Args:
            event (PreferencesEvent): The event that triggered this listener.
            _ (Extension): The Steam extension, unused in this context due to it being empty.
        """
        log.debug("Steam extension started, building cache")
        preferences: dict[str, Any] = event.preferences
        build_cache(preferences)


class SteamExtensionQueryListener(EventListener):
    def on_event(self, event, extension) -> RenderResultListAction:
        """
        Called when the Steam extension is queried.

        Args:
            event (KeywordQueryEvent): The event that triggered this listener, containing the search argument.
            extension (Extension): The Steam extension, containing the preferences dictionary.

        Returns:
            RenderResultListAction: A call for uLauncher to render the query results.
        """
        from const import EXTENSION_PATH
        from query import SteamExtensionItem, query_cache

        preferences: dict[str, Any] = extension.preferences
        items: list[SteamExtensionItem] = query_cache(
            event.get_keyword(), preferences, event.get_argument()
        )
        log.debug("Converting query results to ExtensionResultItems")
        result_items: list[ExtensionResultItem] = []
        for item in items:
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
    def on_event(self, event, extension) -> None:
        """
        Called when an item as presented in uLauncher is selected.

        Args:
            event (ItemEnterEvent): The event that triggered this listener, containing the selected action.
            extension (Extension): The Steam extension, containing the preferences dictionary.
        """
        from enter import execute_action

        action: str = event.get_data()
        preferences: dict[str, Any] = extension.preferences
        execute_action(action, preferences)


if __name__ == "__main__":
    SteamExtension().run()
