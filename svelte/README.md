This folder contains code that's loaded dynamically (i.e. NOT bundled with the app). The main entry point is a JS module "src/App.js", which can load one or more Svelte components. It also loads the main game module from the "games" folder; see the [README](/games/README.md) for more details.

The following commands will build the app, including copying the source for a single game (2022 in this case):

```
npm install
npm run build -- 2022
```
