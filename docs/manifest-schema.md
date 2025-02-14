# Preferences manifest JSON schema

This document outlines the structure of the preferences file **manifest.json** used by this extension. The preference IDs are capitalised to maintain compatibility with Windows for testing purposes.

> TODO: This schema has not been fully implemented. A cross (❌) beside a property indicates that the cache does not adhere to its specification, whether due to the property name being incorrect or the value not matching the specification.

## Keywords

### `KEYWORD`: Steam search

*Search through everything Steam* (keyword)

Default: `s`

This is the primary keyword that activates the extension, and allows for the searching of all possible list items.

### `KEYWORD_APPS`: Steam apps

*Search through Steam apps* (keyword)

Default: `sa`

This keyword filters the list to only show Steam apps and their dependent navigation items if they are enabled.

### `KEYWORD_FRIENDS`: Steam friends

*Search through Steam friends* (keyword)

Default: `sf`

This keyword filters the list to only show Steam friends and their dependent navigation items if they are enabled.

### `KEYWORD_NAVIGATIONS`: Steam navigations

*Search through Steam navigation items* (keyword)

Default: `sn`

This keyword filters the list to only show non-dependent navigation items.

### `KEYWORD_EXTENSION`: Steam extension actions ❌

*Take control of the Steam extension* (keyword)

Default: `se`

This keyword filters the list to only show critical actions that directly affect the extension.

## Essential configuration

### `STEAM_FOLDERS`: Steam folder paths

*Paths to folders containing 'steamapps' folders, separated by commas, first should have 'userdata' folder* (input)

Default: `/home/<username>/.steam/steam/`

This setting is required in order to search for **appmanifest_*.acf** files, which document the Steam apps installed by the user. The primary Steam folder is assumed to include a 'userdata' folder, which is necessary in order to read the **shortcuts.vdf** file, which documents the non-Steam apps installed by the user.

### `STEAM_USERDATA`: Steam userdata folder name ❌

*Steam userdata folder name (a number) of current user in primary Steam folder* (input)

Default: Empty

This setting is combined with `STEAM_FOLDERS` to form the full 'userdata' folder path in the primary Steam folder. It is required in order to read the **shortcuts.vdf** file, which documents the non-Steam apps installed by the user.

### `STEAM_API_KEY`: Steam Web API key

*API key to use when fetching data (found at steamcommunity.com/dev/apikey)* (input)

Default: Empty

This setting is required in order to fetch data from the Steam Web API.

### `STEAMID64`: Steam ID

*64-bit Steam ID to use when fetching data (found at store.steampowered.com/account)* (input)

Default: Empty

This setting is required in order to fetch data from the Steam Web API, specifically the user's friend list and information about each friend.

### `LANGUAGE`: Language ❌

*Language to display list items in, affects static titles and descriptions* (select)

Options:

- `en-GB` - *English (United Kingdom)*
- `en-US` - *English (United States)* (default)

This setting affects the display of list items, specifically the titles and descriptions that are included in the **lang.csv** file. It does not affect the language of the app or friend names, nor the preference descriptions.

## Customisation

### `MAX_ITEMS`: Maximum list items

*Maximum number of list items to show for results* (input)

Default: `5`

This setting limits the number of list items to show for results to prevent the list from being too large, as smaller monitors may not be able to display all of the items, and the list does not wrap around vertically.

### `SHOW_UNINSTALLED`: Show uninstalled apps ❌

*Whether to show uninstalled apps in the list* (select)

Options:

- `true` - *Yes* (default)
- `false` - *No*

This setting enables or disables the display of uninstalled apps in the list. If they are displayed, selecting them will show the installation dialog.

### `FRIEND_ACTION`: Default friend action ❌

*Default action to perform when a friend is selected* (select)

Options:

- `chat` - *Open chat window* (default)
- `profile` - *Open Steam profile*

This setting controls the default action to perform when a friend is selected in the list. It also controls whether the chat or profile dependent navigation items are visible, as it is not necessary for both to be visible at the same time.

### `SHOW_REAL`: Show friends' real info ❌

*Whether to show friends' real names and locations in the list* (select)

Options:

- `all` - *Yes* (default)
- `onlyNames` - *Only real names*
- `onlyLocations` - *Only locations*
- `none` - *No*

This setting controls the display of friends' real names and locations in the list. It is preferrable for users to be able to hide this information, as it contains sensitive information that ought not to be screenshotted.

### `SHOW_DEPENDENT`: Show app and friend navigations ❌

*Whether to show extra navigation items for apps and friends* (select)

Options:

- `all` - *Yes* (default)
- `onlyApps` - *Only owned apps* ❌
- `onlyFriends` - *Only friends and groups* ❌
- `none` - *No*

This setting controls the display of navigation items that depend on app and friend IDs. There are a lot of these, so the user may prefer to hide them altogether.

### `APP_BLACKLIST`: App blacklist

*IDs of apps to hide from the list, separated by commas* (input)

Default: Empty

This setting hides apps from the list if they match one of the specified IDs. This is useful for hiding apps that are marked as hidden in Steam, are not games, or are otherwise not of interest to the user.

### `FRIEND_BLACKLIST`: Friend blacklist

*64-bit Steam IDs of friends to hide from the list, separated by commas* (input)

Default: Empty

This setting hides friends from the list if they match one of the specified IDs. This is useful for hiding friends that are not of interest to the user.

## Caching

### `UPDATE_FILES`: Time between file reads ❌

*Time to wait before reading files on disk to update the cache* (input)

Default: `1m`

This setting controls when the extension is allowed to read files on disk to update the cache. The time files were last read is stored in the cache under `updated > files`. Low values may be computationally expensive on older hardware.

### `UPDATE_STEAM_API`: Time between Steam API calls ❌

*Time to wait before querying the Steam API to update the cache* (input)

Default: `1h`

This setting controls when the extension is allowed to query the Steam API to update the cache. The time the Steam API was last queried is stored in the cache under `updated > steamApi`. Low values may cause the user to be banned from the Steam API.

### `TRACK_SCORES`: Track list item scores ❌

*Whether to track selected list items and scoring metrics (Warning: Large file)* (select) ❌

Options:

- `true` - *Yes* ❌
- `false` - *No* (default) ❌

This setting is exclusively for debugging. It allows developers to extract from the extension how it grades each selected list item based on the user's search string. The metrics along with the title and description of the selected list item are stored in the file **scores.csv**. This helps developers tweak the multipliers for each metric that affect how items are placed on the list.
