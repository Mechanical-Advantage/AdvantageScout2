let copydir = require("copy-dir");

if (process.argv.length > 2) {
    const game = process.argv[2];
    copydir.sync("../games/" + game, "./src/app/game");
} else {
    throw new Error("No game was provided");
}
