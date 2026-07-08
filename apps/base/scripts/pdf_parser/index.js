const fs = require("fs");
const os = require("os");
const path = require("path");
const puppeteer = require("puppeteer");

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", chunk => {
      data += chunk;
    });
    process.stdin.on("end", () => resolve(data));
    process.stdin.on("error", reject);
  });
}

function buildPdfOptions(pdfType) {
  if (pdfType !== "massive_operation_receipt") {
    return {
      format: "A4",
      printBackground: true
    };
  }

  return {
    format: "A4",
    printBackground: true,
    displayHeaderFooter: true,
    preferCSSPageSize: true,
    margin: {
      top: "22mm",
      right: "16mm",
      bottom: "40mm",
      left: "16mm"
    },
    headerTemplate: `<div></div>`,
    footerTemplate: `
      <div style="
        width: 100%;
        font-size: 10px;
        color: #888;
        padding: 0 16mm;
        box-sizing: border-box;
        font-family: Arial, Helvetica, sans-serif;
      ">
        <div style="
          border-top: 1px solid #d9d9d9;
          padding-top: 8px;
          text-align: center;
          line-height: 1.5;
        ">
          Este documento es un soporte electrónico de SMART EVOLUTION S.A.S.<br>
          La información aquí contenida debe ser validada con la carga manual final en la plataforma.<br>
          <strong>www.app.smartevolution.com.co</strong>
        </div>

        <div style="
          width: 100%;
          text-align: right;
          margin-top: 4px;
          color: #666;
        ">
          Página <span class="pageNumber"></span> de <span class="totalPages"></span>
        </div>
      </div>
    `
  };
}

function parseInput(rawInput) {
  let htmlContent = rawInput;
  let pdfType = null;

  try {
    const parsed = JSON.parse(rawInput);
    if (parsed && typeof parsed === "object") {
      htmlContent = parsed.html || "";
      pdfType = parsed.pdf_type || null;
    }
  } catch (error) {
    // Compatibilidad con llamados viejos que envían HTML plano.
  }

  if (!htmlContent) {
    throw new Error("No se recibió contenido HTML");
  }

  return { htmlContent, pdfType };
}

function buildLaunchEnv() {
  const launchEnv = {
    ...process.env,
    XDG_RUNTIME_DIR: "/tmp"
  };

  // No enviar D-Bus vacío ni a /dev/null.
  delete launchEnv.DBUS_SESSION_BUS_ADDRESS;
  delete launchEnv.DBUS_SYSTEM_BUS_ADDRESS;

  return launchEnv;
}

function getChromeExecutablePath() {
  const configuredPath = process.env.PUPPETEER_EXECUTABLE_PATH;

  // En este proyecto /usr/bin/chromium fue el binario que crasheaba.
  // Solo respetamos la variable si apunta a otro ejecutable real.
  if (configuredPath && configuredPath !== "/usr/bin/chromium") {
    return configuredPath;
  }

  return puppeteer.executablePath();
}

function buildChromeArgs(paths) {
  return [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-sync",
    "--disable-translate",
    "--disable-breakpad",
    "--disable-crash-reporter",
    "--disable-crashpad",
    "--disable-features=Crashpad",
    "--hide-scrollbars",
    "--mute-audio",
    "--no-first-run",
    "--no-default-browser-check",
    "--no-proxy-server",
    `--user-data-dir=${paths.userDataDir}`,
    `--data-path=${paths.dataPath}`,
    `--disk-cache-dir=${paths.cacheDir}`,
    `--crash-dumps-dir=${paths.crashDir}`
  ];
}

async function launchBrowser(paths) {
  const executablePath = getChromeExecutablePath();

  return puppeteer.launch({
    headless: "new",
    executablePath,
    protocolTimeout: 120000,
    timeout: 120000,
    env: buildLaunchEnv(),
    args: buildChromeArgs(paths)
  });
}

(async () => {
  let browser = null;
  let tmpRoot = null;

  try {
    const rawInput = await readStdin();
    const { htmlContent, pdfType } = parseInput(rawInput);

    tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "smartevolution-pdf-"));
    const paths = {
      userDataDir: path.join(tmpRoot, "profile"),
      dataPath: path.join(tmpRoot, "data"),
      cacheDir: path.join(tmpRoot, "cache"),
      crashDir: path.join(tmpRoot, "crashes")
    };

    for (const dir of Object.values(paths)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    browser = await launchBrowser(paths);

    const page = await browser.newPage();
    page.setDefaultTimeout(60000);
    page.setDefaultNavigationTimeout(60000);

    await page.setContent(htmlContent, {
      waitUntil: "domcontentloaded",
      timeout: 60000
    });

    await page.emulateMediaType("screen");

    const pdfBuffer = await page.pdf(buildPdfOptions(pdfType));

    console.log(JSON.stringify({
      status: "success",
      pdf: Buffer.from(pdfBuffer).toString("base64")
    }));
  } catch (error) {
    console.log(JSON.stringify({
      status: "error",
      message: error && error.stack ? error.stack : String(error)
    }));
  } finally {
    if (browser) {
      try {
        await browser.close();
      } catch (error) {
        // No romper la respuesta por errores cerrando Chrome.
      }
    }

    if (tmpRoot) {
      try {
        fs.rmSync(tmpRoot, { recursive: true, force: true });
      } catch (error) {
        // No romper la respuesta por limpieza temporal.
      }
    }
  }
})();
