
import os
from fastapi import Request
from weasyprint import HTML as WeasyHTML
#from playwright.async_api import async_playwright
import base64
from app.config import get_base_url


# 🔧 Exemple de fonction à adapter à ton projet
def get_pdf_path(filename: str) -> str:
    output_dir = os.path.join(os.getcwd(), "fichiers")
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, filename)

def encode_file_to_base64(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

"""async def generate_pdf_dynamic(html_content: str, filename: str, request: Request, use_js: bool = False) -> dict:
    base_url = get_base_url(request)
    pdf_path = get_pdf_path(filename)

    if not use_js:
        try:
            WeasyHTML(string=html_content).write_pdf(pdf_path)
        except Exception as e:
            raise Exception(f"Erreur avec WeasyPrint : {str(e)}")
    else:
        try:
            html_temp_path = pdf_path.replace(".pdf", ".html")
            with open(html_temp_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(f"file://{os.path.abspath(html_temp_path)}")
                await page.pdf(path=pdf_path, format="A4")
                await browser.close()

            os.remove(html_temp_path)

        except Exception as e:
            raise Exception(f"Erreur avec Playwright : {str(e)}")

    encoded_file = encode_file_to_base64(pdf_path) if os.path.exists(pdf_path) else None
    file_url = f"{base_url}/fichiers/{filename}"

    return {
        "filename": filename,
        "file_url": file_url,
        "file_encoded": encoded_file
    }"""