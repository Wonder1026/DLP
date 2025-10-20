from app.dlp.analyzers.text_analyzer import TextAnalyzer
from typing import Dict


class DLPEngine:
    """Главный движок DLP системы"""

    def __init__(self):
        self.text_analyzer = TextAnalyzer()

    def check_message(self, text: str, user: str) -> Dict:
        """
        Проверка сообщения через DLP

        Возвращает:
        {
            "allowed": True/False,
            "status": "allow" | "block" | "quarantine",
            "reason": "...",
            "found_keywords": [...]
        }
        """
        # Анализируем текст
        result = self.text_analyzer.analyze(text)

        return {
            "allowed": result["status"] == "allow",
            "status": result["status"],
            "reason": result["message"],
            "found_keywords": result.get("found_keywords", [])
        }


# Создаём глобальный экземпляр DLP движка
dlp_engine = DLPEngine()