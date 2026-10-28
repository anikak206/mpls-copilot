// Build configuration: adds the "@" -> src import alias to Create React App.
const path = require("path");

module.exports = {
  webpack: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  jest: {
    configure: {
      moduleNameMapper: { "^@/(.*)$": "<rootDir>/src/$1" },
    },
  },
};
