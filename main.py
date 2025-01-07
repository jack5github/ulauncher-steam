from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction

class SteamExtension(Extension):
	def __init__(self):
		super().__init__()
		self.subscribe(KeywordQueryEvent, SteamExtensionKeywordEventListener())

def get_installed_steam_apps(steamapps_folder: str, userdata_folder: str) -> list[tuple[str, int]]:
	"""
	Returns the names and app IDs of all installed Steam apps.

	Args:
		steamapps_folder (str): The path to the steamapps folder.
		userdata_folder (str): The path to the user's userdata folder.

	Returns:
		list[tuple[str, int]]: A list of tuples containing the name and app ID of all installed Steam apps.
	"""
	from logging import getLogger, Logger
	import os

	log: Logger = getLogger(__name__)
	# Get all appmanifest_#.acf files in the steamapps folder
	appmanifest_files: tuple[str, ...] = tuple(
		file for file in os.listdir(steamapps_folder) if file.startswith("appmanifest_") and file.endswith(".acf")
	)
	log.debug(appmanifest_files)
	# Each file is a JSON-like object using the following syntax:
	"""
	"AppState"
	{
		"Key"       "Value"
		"NumKey"    "0"
		"NestedKey"
		{
			"Key"   "Value"
		}
	}
	"""
	installed_steam_apps: list[tuple[str, int]] = []
	for file in appmanifest_files:
		log.debug(os.path.join(steamapps_folder, file))
		with open(os.path.join(steamapps_folder, file), "r", encoding="utf-8") as f:
			name: str | None = None
			appid: int | None = None
			# Extract all relevant keys and values from the JSON-like object
			for line in f.readlines():
				line = line.strip()
				log.debug(line)
				if line.startswith('"name"'):
					name = line[1:].split('"')[2]
					log.debug(f"Name found: {name}")
				if line.startswith('"appid"'):
					appid = int(line[1:].split('"')[2])
					log.debug(f"App ID found: {appid}")
				if name is not None and appid is not None:
					installed_steam_apps.append((name, appid))
					break
	"""
	# Locate the user shortcuts file
	user_shortcuts_file: str = os.path.join(userdata_folder, "/config/shortcuts.vdf")
	log.debug(user_shortcuts_file)
	# Shortcuts are represented as hex, flanked by keys in plain English
	# https://steamcommunity.com/discussions/forum/1/5560306947036116992/
	with open(os.path.join(user_shortcuts_file), "r", encoding="hex") as f:
		pass
	"""
	log.debug(installed_steam_apps)
	installed_steam_apps = sorted(installed_steam_apps, key=lambda x: x[0].lower())
	return installed_steam_apps

# https://developer.valvesoftware.com/wiki/Steam_browser_protocol

class SteamExtensionKeywordEventListener(EventListener):
	def on_event(self, event, extension):
		items: list[ExtensionResultItem] = []
		if event.get_keyword() == extension.preferences["game_keyword"]:
			installed_steam_apps: list[str] = get_installed_steam_apps(
				extension.preferences["steamapps_folder"], extension.preferences["userdata_folder"]
			)
			for app in installed_steam_apps:
				items.append(
					ExtensionResultItem(
						icon='images/icon.png',
						name=app[0],
						on_enter=RunScriptAction(f"steam steam://rungameid/{app[1]}")
					)
				)
		else:
			items = [
				ExtensionResultItem(
					icon='images/icon.png',
					name='DX-Ball 2: 20th Anniversary Edition',
					description='Longbow Games',
					on_enter=RunScriptAction("steam steam://rungameid/922400")
				),
				ExtensionResultItem(
					icon='images/icon.png',
					name=f"{str(event.get_argument())} {str(event.get_keyword())} {str(event.get_query().get_argument())} {str(event.get_query().get_keyword())}",
					description=str(extension),
					on_enter=RunScriptAction("steam steam://rungameid/922400")
				)
			]
		return RenderResultListAction(items)

if __name__ == '__main__':
	SteamExtension().run()
