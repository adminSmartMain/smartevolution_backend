const puppeteer = require("puppeteer");

(async () => {
  try {
    const browser = await puppeteer.launch({ 
      headless: "new",
      args: ["--no-sandbox", "--disable-setuid-sandbox"], 
      executablePath: "/usr/bin/chromium"
 });
    const page = await browser.newPage();

    const htmlContent = process.argv[2];
    await page.setContent(htmlContent);

    const pdfBuffer = await page.pdf({ format: "A4", printBackground: true });
    await browser.close();

    const base64Data = pdfBuffer.toString("base64");

    console.log(JSON.stringify({ status: "success", pdf: base64Data }));
  } catch (error) {
    console.log(JSON.stringify({ status: "error", message: error.message }));
  }
})();
