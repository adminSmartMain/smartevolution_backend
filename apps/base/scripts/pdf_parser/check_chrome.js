const { spawnSync } = require("child_process");
const puppeteer = require("puppeteer");

const chromePath = puppeteer.executablePath();
console.log("Puppeteer:", require("./node_modules/puppeteer/package.json").version);
console.log("Chrome path:", chromePath);

const version = spawnSync(chromePath, ["--version"], { encoding: "utf8" });
console.log("Chrome version stdout:", (version.stdout || "").trim());
console.log("Chrome version stderr:", (version.stderr || "").trim());
console.log("Chrome version status:", version.status);

const test = spawnSync(chromePath, [
  "--headless=new",
  "--no-sandbox",
  "--disable-setuid-sandbox",
  "--disable-dev-shm-usage",
  "--disable-gpu",
  "--dump-dom",
  "about:blank"
], {
  encoding: "utf8",
  timeout: 20000
});

console.log("Dump DOM stdout:", (test.stdout || "").slice(0, 300).trim());
console.log("Dump DOM stderr:", (test.stderr || "").slice(0, 1000).trim());
console.log("Dump DOM status:", test.status);
console.log("Dump DOM signal:", test.signal || "");

process.exit(test.status || 0);
