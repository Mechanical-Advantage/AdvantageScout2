## Svelte

This folder contains all of the code for the app and admin page. The main entry points are JS moduls ("src/app/App.js" and "src/admin/Admin.js"), which can load one or more Svelte components. The app data is loaded dynamically, and includes the game module from the "games" folder; see the [README](/games/README.md) for more details.

The following commands will build the app and admin page. The app build also requires a game to be selected. The bundles are saved to the "build" folder.

```
npm install
npm run build-app -- 2022
npm run build-admin
```
