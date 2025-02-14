# Extension cache JSON schema

This document outlines the structure of the cache file **cache.json** saved and used by this extension.

> TODO: This schema has not been fully implemented. A cross (❌) beside a property indicates that the cache does not adhere to its specification, whether due to the property name being incorrect or the value not matching the specification.

All of the below dictionaries (except `countries` and `updated`) contain data directly related to list items displayed by the extension. For all of these dictionaries, the generic keyword `s` can be used to search through them. Additionally, if their IDs are added to the appropriate blacklist, their data will be removed from the cache. ❌

## `apps` (Keyword: `sa`)

A dictionary of all Steam applications owned by the user, both installed and not.

- ID (string) - The integer ID of the application. This ID is used when retrieving icons from `/images/apps/<id>.jpg`.
- `name` (string) - The name of the application.
- `playtime` (integer) - The total playtime of the application in minutes. ❌
- `dir` (string) - The path to the folder containing the application. ❌
- `size` (integer) - The size of the application on disk in bytes. ❌
- `launched` (integer) - A timestamp of the last time the application was launched. Unlike other `launched` properties, this timestamp can be acquired both through the Steam API and uLauncher activations. ❌

## `nonSteam` (Keyword: `sa`)

A dictionary of all non-Steam applications associated with the current installed instance of Steam. These are accessible under the same keyword as owned Steam applications for simplicity.

- ID (string) - The integer ID of the application. This ID is used when retrieving icons from `/images/apps/`. ❌
- `name` (string) - The name of the application.
- `launched` (integer) - A timestamp of the last time the application was launched through uLauncher. ❌

## `friends` (Keyword: `sf`)

A dictionary of all the user's Steam friends.

- ID (string) - The steamid64 integer ID of the friend. This ID is used when retrieving icons from `/images/friends/<id>.jpg`.
- `name` (string) - The display name of the friend.
- `realName` (string) - The real name of the friend. ❌
- `country` (string) - The country code of the friend.
- `state` (string) - The state code of the friend.
- `city` (integer) - The city code of the friend. ❌
- `since` (integer) - A timestamp of when the friend was added to the user's friend list. ❌
- `updated` (integer) - A timestamp of when the friend's profile was last updated. ❌
- `launched` (integer) - A timestamp of the last time the application was launched through uLauncher. ❌

## `countries`

A dictionary of country, state and city codes in use by the user's Steam friends. Only countries, states and cities in active use by the Steam friends in the cache are stored. ❌

- ID (string) - The country code.
- **States** (dictionaries)
    - ID (string) - The state code.
    - `name` (string) - The name of the state.
    - **Cities** (dictionaries)
        - ID (string) - The city code.
        - Value (string) - The name of the city.

## `groups` (Keyword: `sf`) ❌

A dictionary of all the user's Steam groups. These are accessible under the same keyword as Steam friends for simplicity.

- ID (string) - The integer ID of the group. This ID is used when retrieving icons from `/images/groups/<id>.jpg`. ❌
- `name` (string) - The name of the group. ❌
- `launched` (integer) - A timestamp of the last time the application was launched through uLauncher. ❌

## `navs` (Keyword: `sn`)

A dictionary of the additional navigation items supplied by the extension when they are activated by the user. These include items that directly relate to a Steam application or friend which are not the default action for each of them, in which case they will appear when using the `sa` or `sf` keywords. A few special navigation items directly related to extension functionality are also included, and these can be accessed using the `se` keyword.

- ID (string) - The URL of the navigation item, or a string identifier for a special navigation item. If the URL begins with "steam://" or "https://", the protocol is shortened to "s:" and "w:" respectively. This identifier is used when retrieving icons from `/images/navs/<id>.jpg`, though the app or friend IDs are replaced with `%a` or `%f` respectively, and all special characters except `%` are replaced with `-` for the icon path. ❌
- `launched` (integer) - A timestamp of the last time the application was launched through uLauncher. ❌

## `updated`

A dictionary of the last times the cache was updated as it relates to individual functions of the extension.

- `files` (integer) - The timestamp of the last time the cache was updated from files on disk. ❌
- `steamApi` (integer) - The timestamp of the last time the cache was updated from the Steam API. ❌
