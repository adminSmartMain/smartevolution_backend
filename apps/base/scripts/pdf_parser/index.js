const puppeteer = require("puppeteer");

(async () => {
  try {
    const chromiumPath = "/usr/bin/chromium";

    const browser = await puppeteer.launch({
      executablePath: chromiumPath,
      headless: "new",
    });
    const page = await browser.newPage();

    // Define el contenido HTML que deseas convertir a PDF
    const htmlContent = process.argv[2];

    // Establece el contenido HTML para la página
    await page.setContent(htmlContent);

    // Genera el PDF
    const pdfBuffer = await page.pdf({ format: "A4", printBackground: true });

    // Cierra el navegador
    await browser.close();

    // Convierte el archivo PDF a Base64
    const base64Data = pdfBuffer.toString("base64");

    console.log(
      JSON.stringify({
        status: "success",
        pdf: base64Data,
      })
    );
  } catch (error) {
    console.log(
      JSON.stringify({
        status: "error",
        message: error.message,
      })
    );
  }
})();
