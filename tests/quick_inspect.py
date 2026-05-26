import pdfplumber
import sys

def inspect(path):
    with pdfplumber.open(path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        print(text)

if __name__ == "__main__":
    inspect(sys.argv[1])
