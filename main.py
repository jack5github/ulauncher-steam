from logging import getLogger, Logger
from typing import Any
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction

log: Logger = getLogger(__name__)

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
	from os.path import join as path_join

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
		log.debug(path_join(steamapps_folder, file))
		with open(path_join(steamapps_folder, file), "r", encoding="utf-8") as f:
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

# http://docs.ulauncher.io/en/stable/extensions/libs.html

def get_all_owned_steam_apps(api_key: str, steam_id64: str) -> list[tuple[str, int, str]]:
	"""
	Returns the names, app IDs and icon URLs of all owned Steam apps.

	Args:
		api_key (str): The Steam API key.
		steam_id64 (str): The Steam ID64 of the user.

	Returns:
		list[tuple[str, int]]: A list of tuples containing the name, app ID and icon URL of all owned Steam apps.
	"""
	from http.client import HTTPSConnection
	from json import loads as json_loads

	owned_games_url: str = (
		"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" +
		api_key +
		"&steamid=" +
		steam_id64 + 
		"&include_appinfo=1&include_played_free_games=1&format=json"
	)
	conn = HTTPSConnection("api.steampowered.com")
	conn.request("GET", owned_games_url)
	response = conn.getresponse().read()
	owned_games: list[tuple[str, int, str]] = [
		(
			game["name"],
			game["appid"],
			f"https://media.steampowered.com/steamcommunity/public/images/apps/{game['appid']}/{game['img_icon_url']}.jpg"
		)
		for game in json_loads(response)["response"]["games"]
	]
	owned_games = sorted(owned_games, key=lambda x: x[0].lower())
	return owned_games

def fuzzy_match_filter(items: list[tuple[str, Any, ...]], match: str | None) -> list[tuple[str, Any, ...]]:
	if match is None:
		return items
	matches: list[str] = match.strip().lower().split()
	return [item for item in items if all(word in item[0].lower() for word in matches)]

def get_extension_path() -> str:
	return "/".join(__file__.split("/")[:-1])

# https://developer.valvesoftware.com/wiki/Steam_browser_protocol

class SteamExtensionKeywordEventListener(EventListener):
	def on_event(self, event, extension):
		from os import mkdir
		from os.path import isdir, isfile
		from urllib.error import HTTPError
		from urllib.request import urlretrieve

		items: list[ExtensionResultItem] = []
		if event.get_keyword() == extension.preferences["game_keyword"]:
			installed_steam_apps: tuple[str, int] = get_installed_steam_apps(
				extension.preferences["steamapps_folder"], extension.preferences["userdata_folder"]
			)
			log.debug(event.get_argument())
			installed_steam_apps = fuzzy_match_filter(installed_steam_apps, event.get_argument())
			for app in installed_steam_apps:
				items.append(
					ExtensionResultItem(
						icon='images/icon.png',
						name=app[0],
						on_enter=RunScriptAction(f"steam steam://rungameid/{app[1]}")
					)
				)
		elif event.get_keyword() == extension.preferences["api_keyword"]:
			owned_steam_apps: tuple[str, int, str] = get_all_owned_steam_apps(
				extension.preferences["api_key"], extension.preferences["steam_id"]
			)
			owned_steam_apps = fuzzy_match_filter(owned_steam_apps, event.get_argument())
			ext_path: str = get_extension_path()
			if not isdir(f"{ext_path}/images/apps"):
				mkdir(f"{ext_path}/images/apps")
			for app in owned_steam_apps:
				if not isfile(f"{ext_path}/images/apps/{app[1]}.jpg"):
					# Download the icon
					try:
						urlretrieve(app[2], f"{ext_path}/images/apps/{app[1]}.jpg")
					except HTTPError:
						pass
				items.append(
					ExtensionResultItem(
						icon=f"images/apps/{app[1]}.jpg",
						name=app[0],
						on_enter=RunScriptAction(f"steam steam://rungameid/{app[1]}")
					)
				)
		"""
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
				),
				ExtensionResultItem(
					icon='images/icon.png',
					name=str(__file__),
					description=str([item for item in dir(extension) if not item.startswith("_")]),
					on_enter=RunScriptAction("steam steam://rungameid/922400")
				)
			]
		"""
		return RenderResultListAction(items)

if __name__ == '__main__':
	SteamExtension().run()
