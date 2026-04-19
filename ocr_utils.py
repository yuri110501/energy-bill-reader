"""
ocr_utils.py
------------
Extrai texto de imagens de contas de energia usando Tesseract OCR.
Aplica pré-processamento de imagem para melhorar a acurácia.
"""

import os

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

# Configuração para Windows (se o Tesseract estiver instalado no caminho padrão)
if os.name == 'nt' and HAS_OCR:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text(file_path: str) -> str:
    """
    Extrai texto de uma imagem via OCR.

    Args:
        file_path: Caminho para o arquivo de imagem (JPG, PNG, PDF).

    Returns:
        Texto extraído como string.
    """
    if not HAS_OCR:
        print("WARN (ocr_utils): pytesseract/Pillow não instalados. Retornando texto vazio.")
        return ""

    if not os.path.exists(file_path):
        print(f"WARN (ocr_utils): Arquivo não encontrado: {file_path}")
        return ""

    try:
        # Verifica se é PDF pela extensão
        if file_path.lower().endswith(".pdf"):
            import fitz  # PyMuPDF
            # Abre o PDF e pega apenas a primeira página
            doc = fitz.open(file_path)
            if len(doc) == 0:
                return ""
            page = doc.load_page(0)
            
            # Converte a página para imagem (aumentamos a resolução com zoom = 2)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            # Converte os bytes do pixmap para objeto Image do Pillow
            from io import BytesIO
            img_data = pix.tobytes("png")
            img = Image.open(BytesIO(img_data))
            doc.close()
        else:
            # Fluxo normal para imagens JPG, PNG
            img = Image.open(file_path)

        img = _preprocess_image(img)

        # Configura Tesseract para português
        custom_config = r"--oem 3 --psm 6 -l por+eng"
        text = pytesseract.image_to_string(img, config=custom_config)
        print(f"DEBUG (ocr_utils): Texto extraído ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"ERROR (ocr_utils): Falha no OCR: {e}")
        return ""


def _preprocess_image(img):
    """
    Aplica melhorias na imagem para aumentar a qualidade do OCR:
    - Converte para escala de cinza
    - Aumenta contraste
    - Aplica nitidez
    - Redimensiona se muito pequena
    """
    # Converte para RGB se necessário
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Escala de cinza
    img = img.convert("L")

    # Aumenta contraste
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # Nitidez
    img = img.filter(ImageFilter.SHARPEN)

    # Redimensiona se muito pequena (melhora OCR)
    min_width = 1500
    if img.width < min_width:
        ratio = min_width / img.width
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    return img
