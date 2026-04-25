import re
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import pytesseract
import speech_recognition as sr
from moviepy.editor import VideoFileClip


def extract_text(file_path):
    try:
        # TXT
        if file_path.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        # PDF
        elif file_path.endswith(".pdf"):
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
            return text

        # DOCX
        elif file_path.endswith(".docx"):
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])

        # IMAGE → OCR
        elif file_path.endswith((".jpg", ".png", ".jpeg")):
            img = Image.open(file_path)
            return pytesseract.image_to_string(img)

        # AUDIO
        elif file_path.endswith((".mp3", ".wav")):
            r = sr.Recognizer()
            with sr.AudioFile(file_path) as source:
                audio = r.record(source)
            return r.recognize_google(audio)

        # VIDEO → AUDIO → TEXT
        elif file_path.endswith(".mp4"):
            audio_path = file_path + ".wav"
            clip = VideoFileClip(file_path)
            clip.audio.write_audiofile(audio_path)

            r = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = r.record(source)

            return r.recognize_google(audio)

        else:
            return ""

    except Exception as e:
        print("Error:", e)
        return ""