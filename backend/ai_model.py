import numpy as np
import re
import torch
from transformers import AutoTokenizer, AutoModel

# 🔥 Load model once
tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
model = AutoModel.from_pretrained("distilbert-base-uncased")


# ================= EMBEDDING =================
def get_embedding(text):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    )

    with torch.no_grad():
        outputs = model(**inputs)

    emb = outputs.last_hidden_state.mean(dim=1).squeeze()
    return emb.numpy()


# ================= SEMANTIC SCORE =================
def semantic_score(text):
    try:
        emb = get_embedding(text)
        norm = np.linalg.norm(emb)
        return float(norm / (norm + 10))
    except:
        return 0.3


# ================= CONTENT QUALITY =================
def content_quality(text):
    words = text.split()
    word_count = len(words)

    length_score = min(word_count / 1000, 1)
    unique_ratio = len(set(words)) / (word_count + 1)

    return (0.6 * length_score + 0.4 * unique_ratio)


# ================= STRUCTURE =================
def structure_score(text):
    score = 0

    if re.search(r"(#|\n[A-Z]{5,})", text):
        score += 0.2

    if "def " in text or "class " in text:
        score += 0.2

    if "-" in text or "*" in text:
        score += 0.1

    return min(score, 1)


# ================= KEYWORDS =================
def keyword_score(text):
    keywords = [
        "important", "project", "report", "final",
        "research", "analysis", "summary", "result"
    ]

    text_lower = text.lower()
    matches = sum(1 for k in keywords if k in text_lower)

    return min(matches / len(keywords), 1)


# ================= FILENAME SCORE =================
def filename_score(name):
    keywords = [
        "final", "important", "project", "report",
        "resume", "cv", "invoice", "data"
    ]

    name_lower = name.lower()
    score = sum(1 for k in keywords if k in name_lower)

    return min(score / len(keywords), 1)


# ================= VIEWS SCORE =================
def views_score(views):
    return min(views / 20, 1)


# ================= FINAL IMPORTANCE =================
def calculate_importance(text, filename, views):
    try:
        if not text or len(text) < 20:
            base = 0.1
        else:
            sem = semantic_score(text)
            quality = content_quality(text)
            structure = structure_score(text)
            keyword = keyword_score(text)

            base = (
                0.30 * sem +
                0.25 * quality +
                0.20 * structure +
                0.10 * keyword
            )

        # 🔥 add filename + views
        f_score = filename_score(filename)
        v_score = views_score(views)

        final_score = (
            0.65 * base +
            0.20 * v_score +
            0.15 * f_score
        )

        return round(min(final_score, 1), 2)

    except Exception as e:
        print("Importance error:", e)
        return 0.2