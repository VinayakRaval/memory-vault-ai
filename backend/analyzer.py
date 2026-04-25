import re
import os
from PyPDF2 import PdfReader
from docx import Document

# 🔥 OPTIONAL AI MODEL
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    USE_AI = True
except:
    USE_AI = False


# ================= FILENAME =================
def filename_score(name):
    keywords = ["important", "final", "project", "report", "resume", "invoice"]
    name = name.lower()

    matches = sum(1 for k in keywords if k in name)

    return min(matches / len(keywords), 1)


# ================= EXTRACT TEXT =================
def extract_text(file_path):
    try:
        if file_path.endswith(".txt"):
            return open(file_path, "r", encoding="utf-8", errors="ignore").read()

        elif file_path.endswith(".pdf"):
            reader = PdfReader(file_path)
            return "\n".join([p.extract_text() or "" for p in reader.pages])

        elif file_path.endswith(".docx"):
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])

        elif file_path.endswith((".jpg", ".png", ".jpeg")):
            return "image_file"

        elif file_path.endswith((".mp3", ".wav", ".mp4")):
            return "media_file"

        else:
            return ""

    except:
        return ""


# ================= CONTENT SCORE =================
def content_score(file_path):
    text = extract_text(file_path)

    if not text:
        return 0.1

    # 🔥 media / image base score
    if text == "image_file":
        return 0.5
    if text == "media_file":
        return 0.6

    # 🔥 fallback logic
    words = re.findall(r'\w+', text)
    length_score = min(len(words) / 800, 1)

    # 🔥 optional AI boost
    if USE_AI:
        try:
            emb = model.encode(text[:500])
            ai_boost = min(sum(abs(emb)) / 200, 1)
        except:
            ai_boost = 0.3
    else:
        ai_boost = 0.3

    return 0.7 * length_score + 0.3 * ai_boost


# ================= VIEWS SCORE =================
def views_score(views):
    # smooth scaling (important fix)
    return min((views ** 0.5) / 5, 1)


# ================= FINAL IMPORTANCE =================
def calculate_importance(file_path, name, views=0):

    c = content_score(file_path)      # 🔥 main factor
    v = views_score(views)            # 🔥 user behavior
    f = filename_score(name)          # 🔥 hint

    # 🔥 FINAL WEIGHTS (CORRECTED)
    importance = (
        0.55 * c +    # content is primary
        0.30 * v +    # user behavior
        0.15 * f      # filename hint
    )

    importance = round(min(importance, 1), 2)

    # 🔥 CLASSIFICATION
    if importance > 0.75:
        category = "High"
    elif importance > 0.4:
        category = "Medium"
    else:
        category = "Low"

    return importance, category