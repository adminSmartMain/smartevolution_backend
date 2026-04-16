const puppeteer = require("puppeteer");

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", chunk => (data += chunk));
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

(async () => {
  try {
    const rawInput = await readStdin();

    let htmlContent = rawInput;
    let pdfType = null;

    try {
      const parsed = JSON.parse(rawInput);
      if (parsed && typeof parsed === "object") {
        htmlContent = parsed.html || "";
        pdfType = parsed.pdf_type || null;
      }
    } catch (error) {
      // compatibilidad con llamados viejos que envían HTML plano
    }

    if (!htmlContent) {
      throw new Error("No se recibió contenido HTML");
    }

    const browser = await puppeteer.launch({
      headless: "new",
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
      executablePath: "/usr/bin/chromium"
    });

    const page = await browser.newPage();
    await page.setContent(htmlContent, { waitUntil: "networkidle0" });

    const pdfBuffer = await page.pdf(buildPdfOptions(pdfType));

    await browser.close();

    console.log(JSON.stringify({
      status: "success",
      pdf: pdfBuffer.toString("base64")
    }));
  } catch (error) {
    console.log(JSON.stringify({
      status: "error",
      message: error.message
    }));
  }
})();