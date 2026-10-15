import fitz
import re

def extract_pdf_text(file_path):
    pages=[]
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text=page.get_text("text")
            pages.append(text)

    return "\n\n".join(pages)

def clean_text(text):

    text = text.replace("\x00", "")

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

def split_text(
        text,
        chunk_size=800,
        overlap=150
):
    if chunk_size<=0:
        raise ValueError("chunk_size必须大于0")

    if overlap<0 or overlap>=chunk_size:
        raise ValueError("overlap必须小于chunk_size")

    chunks=[]

    start=0

    while start < len(text):
        end=min(
            start+chunk_size,
            len(text)
        )

        chunk=text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end-overlap

    return chunks

def process_pdf(file_path):
    text=extract_pdf_text(file_path)

    text=clean_text(text)

    if not text:
        raise ValueError(
            "PDF没有可提取的文本，可能需要OCR"
        )

    chunks=split_text(text)

    return chunks