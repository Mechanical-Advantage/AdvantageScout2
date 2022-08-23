/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./src/app/**/*.svelte"],
    theme: {
        extend: {}
    },
    plugins: [require("daisyui")]
};
