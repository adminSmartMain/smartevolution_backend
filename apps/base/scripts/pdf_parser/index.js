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

(async () => {
  try {
    const htmlContent = await readStdin();

    const browser = await puppeteer.launch({
      headless: "new",
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
      executablePath: "/usr/bin/chromium"
    });

    const page = await browser.newPage();
    await page.setContent(htmlContent);

    const pdfBuffer = await page.pdf({ format: "A4", printBackground: true });
    await browser.close();

    console.log(JSON.stringify({ status: "success", pdf: pdfBuffer.toString("base64") }));
  } catch (error) {
    console.log(JSON.stringify({ status: "error", message: error.message }));
  }
})();
