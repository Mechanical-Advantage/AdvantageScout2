import svelte from "rollup-plugin-svelte";
import { terser } from "rollup-plugin-terser";
import css from "rollup-plugin-css-only";
import commonjs from "@rollup/plugin-commonjs";
import resolve from "@rollup/plugin-node-resolve";

export default {
    input: "src/App.js",
    output: {
        format: "iife",
        name: "App",
        file: "build/bundle.js"
    },
    plugins: [
        svelte(),
        css({ output: "bundle.css" }),
        terser(),
        resolve({
            browser: true,
            dedupe: ["svelte"]
        }),
        commonjs()
    ]
};
