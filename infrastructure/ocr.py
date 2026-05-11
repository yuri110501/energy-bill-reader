"""
ocr.py
------
Motor de OCR para extração de texto de PDFs e imagens.
Responsabilidade única: converter arquivo em texto e tabelas estruturadas.
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
    Extrai somente o texto de um arquivo (compatibilidade com código legado).
    Prefira usar extract_structured() para obter também as tabelas.
    """
    text, _ = extract_structured(file_path)
    return text


def extract_structured(file_path: str) -> tuple[str, list]:
    """
    Extrai texto E tabelas estruturadas de um arquivo PDF ou imagem.

    Retorna:
        (raw_text: str, tables: list[list[list[str]]])
        - Para PDFs digitais: texto + tabelas via pdfplumber (alta precisão)
        - Para PDFs scaneados/imagens: texto via OCR + tabelas vazias []
    """
    if not os.path.exists(file_path):
        print(f"WARN (ocr): Arquivo não encontrado: {file_path}")
        return "", []

    try:
        if file_path.lower().endswith(".pdf"):
            # Tenta extração nativa com pdfplumber (PDFs digitais)
            if HAS_PDFPLUMBER:
                try:
                    with pdfplumber.open(file_path) as pdf:
                        if len(pdf.pages) > 0:
                            texts = []
                            all_tables = []

                            for page in pdf.pages:
                                # Extrai texto da página
                                page_text = page.extract_text()
                                if page_text:
                                    texts.append(page_text)

                                # Extrai tabelas da página
                                page_tables = page.extract_tables()
                                if page_tables:
                                    all_tables.extend(page_tables)

                            native_text = "\n\n".join(texts)

                            # Se extraiu bastante texto, é PDF digital (não scan)
                            if native_text and len(native_text.strip()) > 300:
                                print(
                                    f"DEBUG (ocr): Extraído via PDFPLUMBER "
                                    f"({len(native_text)} chars, "
                                    f"{len(pdf.pages)} pág., "
                                    f"{len(all_tables)} tabelas)"
                                )
                                return native_text, all_tables

                except Exception as e:
                    print(f"WARN (ocr): pdfplumber falhou ({e}). Recorrendo ao OCR...")

            # Fallback: PDF scaneado → PyMuPDF + Tesseract
            if not HAS_OCR:
                print("WARN (ocr): pytesseract/Pillow não instalados.")
                return "", []

            print("DEBUG (ocr): Tentando extração via OCR (PyMuPDF + Tesseract)...")
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            if len(doc) == 0:
                return "", []

            extracted_texts = []
            # Limita a 3 páginas para evitar travamentos longos no OCR
            max_pages = min(len(doc), 3)

            for page_num in range(max_pages):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                from io import BytesIO
                img_data = pix.tobytes("png")
                img_page = Image.open(BytesIO(img_data))
                img_page = _preprocess_image(img_page)

                custom_config = r"--oem 3 --psm 6 -l por+eng"
                page_text = pytesseract.image_to_string(img_page, config=custom_config)
                extracted_texts.append(page_text)

            doc.close()
            full_text = "\n\n".join(extracted_texts)
            print(f"DEBUG (ocr): Extraído via TESSERACT PDF ({len(full_text)} chars, {max_pages} pág.)")
            # PDFs scaneados não têm tabelas estruturadas
            return full_text, []

        else:
            # Imagens (JPG, PNG)
            if not HAS_OCR:
                print("WARN (ocr): pytesseract/Pillow não instalados.")
                return "", []

            print("DEBUG (ocr): Tentando extração via OCR para imagem...")
            img = Image.open(file_path)
            img = _preprocess_image(img)

            custom_config = r"--oem 3 --psm 6 -l por+eng"
            text = pytesseract.image_to_string(img, config=custom_config)
            print(f"DEBUG (ocr): Extraído via TESSERACT Imagem ({len(text)} chars)")
            return text, []

    except Exception as e:
        print(f"ERROR (ocr): Falha na extração: {e}")
        return "", []


def _preprocess_image(img: Image.Image) -> Image.Image:
    """
    Aplica melhorias na imagem para aumentar a qualidade do OCR:
    escala de cinza, contraste, nitidez e redimensionamento mínimo.
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
