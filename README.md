# uLauncher Steam integration extension

This extension allows you to search and launch Steam apps and menus from uLauncher. Simply type `s ` (or whatever keyword the extension is set to use) and search for the desired app or menu.

## Installation

Copy the repository link and paste it into the dialog that appears when you click `uLauncher > Settings > Extensions > Add extension`.

## Contributing

If you would like to improve this extension, feel free to fork it, make your changes and submit a pull request.

### Debugging

- **Linux**: Code changes can be tested directly in uLauncher by first shutting it down, then executing the command `ulauncher --dev -v`. Search the console for `com.github.jack5github.obsidian-steam-integration |` to find the extension's output.
- **Windows**: As uLauncher is not available on Windows, only the **.py** files that do not import uLauncher packages can be tested. Additionally, the values of preferences must be set using an **.env** file, which must start with `[PREFERENCES]` and represent keys and values in the format `KEY=value`. These files can be invoked using the command `python <filename> <argument>`, with `argument` being the string input after the Steam extension keyword (only used for **query.py**). A **logging.conf** file is also supported to configure logging (see [this HOWTO page](https://docs.python.org/3/howto/logging.html#configuring-logging) for more information).
