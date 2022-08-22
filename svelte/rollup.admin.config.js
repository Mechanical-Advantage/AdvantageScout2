import svelte from "rollup-plugin-svelte";
import { terser } from "rollup-plugin-terser";
import css from "rollup-plugin-css-only";
import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";

export default {
    input: "src/admin/Admin.js",
    output: {
        format: "iife",
        name: "Admin",
        file: "build/admin.js"
    },
    plugins: [
        svelte(),
        css({ output: "admin_rollup.css" }),
        terser(),
        resolve({
            browser: true,
            dedupe: ["svelte"]
        }),
        commonjs()
    ]
};
