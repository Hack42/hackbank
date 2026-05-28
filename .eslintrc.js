module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: "eslint:recommended",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "script",
  },
  globals: {
    $: "readonly",
    dolog: "readonly",
    EventSource: "readonly",
    jQuery: "readonly",
    runtext: "readonly",
    showusers: "readonly",
  },
  overrides: [
    {
      files: ["tests/js/*.test.js"],
      env: {
        node: true,
      },
    },
  ],
};
