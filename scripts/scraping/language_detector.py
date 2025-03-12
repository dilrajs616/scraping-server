from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# To get consistent results (optional)
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    try:
        # Detect language of the provided text
        language = detect(text)
        return language
    except LangDetectException:
        return "Unknown"
    