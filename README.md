# Advantage Scout 2

Advantage Scout 2 is a new major version of our electronic scouting system [Advantage Scout](https://github.com/Mechanical-Advantage/AdvantageScout). This project is still under active development.

-   The web server is at the root level along with the HTML and server interfaces. These are packaged in the Android app and sent directly to the web client.

-   The "svelte" directory contains the main game-agnostic Svelte app and admin page. The game specific data is copied from the "games" directory during the build process. The server builds the app when changes occur and makes it avilable to clients. The clients store a the hash of the bundle and compares it to the server periodically.

*   The "cordova" directory contains a Cordova project for Android. It copies "app.html" and "ServerInterfaceApp.js" during the build process. The actual Bluetooth communication isn't implemented yet (because it'll be much more complex than the HTTP interface), but the bundled app can be cached and loaded the same way as the web version.
