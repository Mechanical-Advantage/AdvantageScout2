const fs = require("fs");
const path = require("path");

module.exports = (context) => {
    fs.copyFileSync(
        path.join("platforms", "android", "app", "build", "outputs", "apk", "debug", "app-debug.apk"),
        "AdvantageScout.apk"
    );
};
