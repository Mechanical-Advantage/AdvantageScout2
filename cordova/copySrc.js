const fs = require("fs");
const path = require("path");

module.exports = (context) => {
    app_html = fs.readFileSync(path.join("..", "app.html"), "utf-8");
    app_html = app_html.replace("ISWEB", "false");
    fs.writeFileSync(path.join("www", "app.html"), app_html);
    fs.copyFileSync(path.join("..", "ServerInterfaceApp.js"), path.join("www", "ServerInterfaceApp.js"));
};
