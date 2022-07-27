# AdvantageScoutTest

This is an example structure for dynmically loading the bundled app (web and Android).

-   The web server is at the root level along with the HTML and server interfaces. These are packaged in the Android app and sent directly to the web client.

-   The "app" directory contains the main game-agnostic Svelte app. The game specific data is copied from the "games" directory during the build process. The server periodically builds the app and makes it avilable to clients (this could be also done when changes are detected).

*   The "capacitor" directory contains a capacitor project for Android. It copies "index.html" and "ServerInterfaceApp.js" during the build process. The actual Bluetooth communication isn't implemented yet (because it'll be much more complex than the HTTP interface), but the bundled app can be cached and loaded the same way as the web version.
