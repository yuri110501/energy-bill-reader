"""
ocr.py
------
Motor de OCR para extração de texto de PDFs e imagens.
Movido de ocr_utils.py — responsabilidade única: converter arquivo em texto.
"""

import os

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

# Configuração para Windows (se o Tesseract estiver instalado no caminho padrão)
if os.name == 'nt' and HAS_OCR:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extract_text(file_path: str) -> str:
    """
    Extrai texto de um arquivo (PDF ou imagem).
    Estratégia: pdfplumber (nativo) → PyMuPDF+Tesseract (OCR) → imagem direta.
    """
    if not HAS_OCR:
        print("WARN (ocr): pytesseract/Pillow não instalados. Retornando texto vazio.")
        return ""

    if not os.path.exists(file_path):
        print(f"WARN (ocr): Arquivo não encontrado: {file_path}")
        return ""

    try:
        if file_path.lower().endswith(".pdf"):
            # Tenta extração nativa com pdfplumber primeiro
            if HAS_PDFPLUMBER:
                try:
                    with pdfplumber.open(file_path) as pdf:
                        if len(pdf.pages) > 0:
                            page = pdf.pages[0]
                            native_text = page.extract_text()
                            # Se extraiu bastante texto, é PDF digital (não scan)
                            if native_text and len(native_text.strip()) > 300:
                                print(f"DEBUG (ocr): Texto extraído via PDFPLUMBER ({len(native_text)} chars)")
                                return native_text
                except Exception as e:
                    print(f"WARN (ocr): Falha ao tentar ler com pdfplumber ({e}). Recorrendo ao OCR...")

            # Fallback para OCR (PyMuPDF -> Tesseract)
            print("DEBUG (ocr): Tentando extração via OCR (PyMuPDF + Tesseract)...")
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            if len(doc) == 0:
                return ""
            page = doc.load_page(0)
            # Aumenta a resolução com zoom = 2
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            from io import BytesIO
            img_data = pix.tobytes("png")
            img = Image.open(BytesIO(img_data))
            doc.close()
        else:
            # Fluxo normal para imagens JPG, PNG
            print("DEBUG (ocr): Tentando extração via OCR nativo para imagem...")
            img = Image.open(file_path)

        img = _preprocess_image(img)

        # Configura Tesseract para português
        custom_config = r"--oem 3 --psm 6 -l por+eng"
        text = pytesseract.image_to_string(img, config=custom_config)
        print(f"DEBUG (ocr): Texto extraído via TESSERACT ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"ERROR (ocr): Falha no OCR: {e}")
        return ""


def _preprocess_image(img: Image.Image) -> Image.Image:
    """
    Aplica melhorias na imagem para aumentar a qualidade do OCR:
    - Escala de cinza, aumento de contraste, nitidez, redimensionamento.
    """
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    img = img.convert("L")
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)

    min_width = 1500
    if img.width < min_width:
        ratio = min_width / img.width
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    return img
