const fs = require("fs");
const path = require("path");

module.exports = (context) => {
    fs.copyFileSync(path.join("..", "app.html"), path.join("www", "app.html"));
    fs.copyFileSync(path.join("..", "ServerInterfaceApp.js"), path.join("www", "ServerInterfaceApp.js"));
};
