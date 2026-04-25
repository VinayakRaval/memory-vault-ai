import os
import pandas as pd
from docx import Document
from PyPDF2 import PdfReader


def read_file(file_path):
    try:
        # ❌ File not found
        if not os.path.exists(file_path):
            return {"type": "error", "content": "❌ File not found"}

        ext = os.path.splitext(file_path)[1].lower().strip()

        # 🔥 TEXT + CODE FILES
        TEXT_TYPES = [
            ".txt", ".py", ".js", ".css", ".json", ".md", ".xml",
            ".csv", ".log", ".sql", ".php", ".c", ".cpp", ".java",
            ".rb", ".sh", ".bat", ".yaml", ".yml", ".ini"
        ]

        # ================= TEXT / CODE =================
        if ext in TEXT_TYPES:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                    if not content.strip():
                        return {
                            "type": "text",
                            "content": "⚠️ File is empty"
                        }

                    return {
                        "type": "text",
                        "content": content
                    }

            except Exception as e:
                return {
                    "type": "error",
                    "content": f"❌ Error reading text file: {str(e)}"
                }

        # ================= DOCX =================
        elif ext == ".docx":
            try:
                doc = Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs])

                return {
                    "type": "text",
                    "content": text if text else "⚠️ Empty DOCX file"
                }

            except Exception as e:
                return {
                    "type": "error",
                    "content": f"❌ DOCX read error: {str(e)}"
                }

        # ================= EXCEL =================
        elif ext in [".xlsx", ".xls"]:
            try:
                df = pd.read_excel(file_path)

                if df.empty:
                    return {
                        "type": "text",
                        "content": "⚠️ Empty Excel file"
                    }

                return {
                    "type": "text",
                    "content": df.to_string(index=False)
                }

            except Exception as e:
                return {
                    "type": "error",
                    "content": f"❌ Excel read error: {str(e)}"
                }

        # ================= HTML =================
        elif ext in [".html", ".htm", ".mhtml"]:
            return {
                "type": "html",
                "path": file_path
            }

        # ================= PDF =================
        elif ext == ".pdf":
            return {
                "type": "pdf",
                "path": file_path
            }

            # 🔥 OPTIONAL: Extract PDF text
            # try:
            #     reader = PdfReader(file_path)
            #     text = ""
            #     for page in reader.pages:
            #         t = page.extract_text()
            #         if t:
            #             text += t + "\n"
            #
            #     return {
            #         "type": "text",
            #         "content": text if text else "⚠️ No readable text"
            #     }
            # except:
            #     return {"type": "pdf", "path": file_path}

        # ================= IMAGE =================
        elif ext in [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"]:
            return {
                "type": "image",
                "path": file_path
            }

        # ================= MEDIA =================
        elif ext in [".mp3", ".mp4", ".wav", ".webm", ".ogg"]:
            return {
                "type": "media",
                "path": file_path
            }

        # ================= UNKNOWN =================
        else:
            return {
                "type": "binary",
                "content": f"⚠️ Preview not supported for {ext.upper()} file"
            }

    except Exception as e:
        return {
            "type": "error",
            "content": f"❌ System error: {str(e)}"
        }