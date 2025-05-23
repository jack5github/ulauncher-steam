# Extension cache JSON schema

This document outlines the structure of the cache file **cache.json** saved and used by this extension. All property names are stored in camelCase and value types are chosen carefully to reduce the size of the cache.

> TODO: This schema has not been fully implemented. A cross (❌) beside a property indicates that the cache does not adhere to its specification, whether due to the property name being incorrect or the value not matching the specification.

## Keyword-related data

All of the below dictionaries contain data directly related to list items displayed by the extension. For all of these dictionaries, the generic keyword `s` can be used to search through them. Additionally, if their IDs are added to the appropriate blacklist, their data will be removed from the cache. ❌

### `apps` (Keyword: `sa`)

A dictionary of all Steam applications owned by the user, both installed and not.

- ID (string) - The integer ID of the application. This ID is used when retrieving icons from `/images/apps/<id>.jpg`.
- `name` (string) - The name of the application.
- `playtime` (integer) - The total playtime of the application in minutes.
- `dir` (string) - The path to the folder containing the application.
- `size` (integer) - The size of the application on disk in bytes.
- `launched` (integer | string) - A timestamp of the last time the application was launched, followed by an `x` then the number of times the application has been launched through uLauncher (if more than 0, otherwise the timestamp is represented as an integer). Unlike other `launched` properties, the timestamp can be acquired both through the Steam API and uLauncher activations.

### `nonSteam` (Keyword: `sa`)

A dictionary of all non-Steam applications associated with the current installed instance of Steam. These are accessible under the same keyword as owned Steam applications for simplicity.

- ID (string) - The integer ID of the application. This ID is used when retrieving icons from `/images/apps/<id>.*`. **.jpg** and **.png** image files are supported, with **.png** being preferred.
- `name` (string) - The name of the application.
- `launched` (string) - A timestamp of the last time the application was launched, followed by an `x` then the number of times the application has been launched through uLauncher if more than 0.

### `friends` (Keyword: `sf`)

A dictionary of all the user's Steam friends.

- ID (string) - The steamID64 integer ID of the friend. This ID is used when retrieving icons from `/images/friends/<id>.jpg`.
- `name` (string) - The display name of the friend.
- `realName` (string) - The real name of the friend.
- `country` (string) - The country code of the friend.
- `state` (string) - The state code of the friend.
- `city` (integer) - The city code of the friend as an integer. Note that this differs from how city codes are stored in the `countries` dictionary.
- `since` (integer) - A timestamp of when the friend was added to the user's friend list.
- `created` (integer) - A timestamp of when the friend's profile was created.
- `updated` (integer) - A timestamp of when the friend's profile was last updated.
- `launched` (string) - A timestamp of the last time the friend was launched, followed by an `x` then the number of times the friend has been launched through uLauncher.

### `groups` (Keyword: `sf`) ❌

A dictionary of all the user's Steam groups. These are accessible under the same keyword as Steam friends for simplicity.

- ID (string) - The integer ID of the group. This ID is used when retrieving icons from `/images/groups/<id>.jpg`. ❌
- `name` (string) - The name of the group. ❌
- `launched` (string) - A timestamp of the last time the group was launched, followed by an `x` then the number of times the group has been launched through uLauncher. ❌

### `navs` (Keyword: `sn`)

A dictionary of the additional navigation items supplied by the extension when they are activated by the user. These include items that directly relate to a Steam application or friend which are not the default action for each of them, in which case they will appear when using the `sa` or `sf` keywords. A few special navigation items directly related to extension functionality are also included, and these can be accessed using the `se` keyword.

- ID (string) - The URL of the navigation item, or a string identifier for a special navigation item. If the URL begins with "steam://" or "https://", the protocol is shortened to "s:" and "w:" respectively. This identifier is used when retrieving icons from `/images/navs/<id>.jpg`, though the app or friend IDs are replaced with `%a` or `%f` respectively, and all reserved characters according to Windows file naming conventions are replaced with `-` for the icon path.
- `launched` (string) - A timestamp of the last time the navigation item was launched, followed by an `x` then the number of times the navigation item has been launched through uLauncher.

## Internal data

The below dictionaries contain data that is not directly related to list items displayed by the extension but must still be stored.

### `countries`

A dictionary of country, state and city codes in use by the user's Steam friends. Only countries, states and cities in active use by the Steam friends in the cache are stored. ❌

- ID (string) - The country code.
- **States** (dictionaries)
    - ID (string) - The state code.
    - `name` (string) - The name of the state.
    - **Cities** (dictionaries)
        - ID (string) - The city code as a string. Note that this differs from how city codes are stored in the `friends` dictionary, due to JSON property name limitations.
        - Value (string) - The name of the city.

### `extension`

A dictionary of property values that directly relate to individual functions of the extension.

- `username` (string) - The username of the current user as entered into the extension preferences. This must be stored in the cache in order to check if the username has changed, requiring `id` to be updated.
- `id` (integer) - The 64-bit Steam ID of the current user derived from the username in the cache.
- `files` (integer) - The timestamp of the last time the cache was updated from files on disk.
- `steamApi` (integer) - The timestamp of the last time the cache was updated from the Steam API.
