import logging
logger = logging.getLogger(__name__)
logger.debug("Importing Extension")
from ulauncher.api.client.Extension import Extension
logger.debug("Importing EventListener")
from ulauncher.api.client.EventListener import EventListener
logger.debug("Importing KeywordQueryEvent")
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
logger.debug("Importing ExtensionResultItem")
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
logger.debug("Importing RenderResultListAction")
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
logger.debug("Importing RunScriptAction")
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction

logger.debug("Creating SteamExtension")
class SteamExtension(Extension):
	logger.debug("Initialising SteamExtension")
	def __init__(self):
		super().__init__()
		logger.debug("Subscribing SteamExtension")
		self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

// https://developer.valvesoftware.com/wiki/Steam_browser_protocol

logger.debug("Creating KeywordQueryEventListener")
class KeywordQueryEventListener(EventListener):
	logger.debug("Creating on_event")
	def on_event(self, event, extension):
		logger.debug("Importing os")
		import os

		logger.debug("Creating ExtensionResultItem")
		items = [ExtensionResultItem(
			icon='images/icon.png',
			name='DX-Ball 2: 20th Anniversary Edition',
			description='Longbow Games',
			on_enter=RunScriptAction("steam steam://rungameid/922400")
		)]
		logger.debug("Returning items")
		return RenderResultListAction(items)

if __name__ == '__main__':
	logger.debug("Running SteamExtension")
	SteamExtension().run()
