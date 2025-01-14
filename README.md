# uLauncher Steam extension

This extension integrates Steam file searches and API calls into uLauncher, allowing you to search for and launch Steam apps, menus and more directly from uLauncher. Simply type any of the extension's keywords (Default: `s`, `sa`, `sf`, `se`) followed by whatever you are looking for, and it will naturally rise to the top of the list.

## Installation

- **Linux**: Copy the repository link and paste it into the uLauncher dialog that appears when you click `uLauncher > Settings > Extensions > Add extension`.
- **Windows**: uLauncher is not available on Windows, but you are free to test this extension by cloning the repository normally.

## Contributing

If you would like to improve this extension, feel free to fork it, make your changes and submit a pull request.

### Debugging

- **Linux**: Code changes can be tested directly in uLauncher by first shutting it down, then executing the command `ulauncher --dev -v`. Search the console for `com.github.jack5github.obsidian-steam-integration |` to find the extension's output. (Note that having a **logging.conf** file present will make this more difficult.)
- **Windows**: As uLauncher is not available on Windows, only the **.py** files that do not import uLauncher packages can be tested. Additionally, the values of preferences must be set using an **.env** file, which must start with `[PREFERENCES]` and represent keys and values in the format `KEY=value`. These files can be invoked using the command `python <filename> <argument>`, with `argument` being the string input after the Steam extension keyword (only used for **query.py** and **enter.py**). A **logging.conf** file is also supported to configure logging (see [this HOWTO page](https://docs.python.org/3/howto/logging.html#configuring-logging) for more information).
