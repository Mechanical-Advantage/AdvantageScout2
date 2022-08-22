const fs = require("fs");
const path = require("path");

const type = process.argv[2];
rollup_css = fs.readFileSync(path.join("build", type + "_rollup.css"), "utf-8");
tailwind_css = fs.readFileSync(path.join("build", type + "_tailwind.css"), "utf-8");
fs.writeFileSync(path.join("build", type + ".css"), rollup_css + "\n" + tailwind_css);
