from app.dlp.analyzers.text_analyzer import TextAnalyzer
from app.dlp.analyzers.sensitive_data_analyzer import SensitiveDataAnalyzer
from app.dlp.analyzers.url_analyzer import URLAnalyzer
from typing import Dict


class DLPEngine:
    """Главный движок DLP системы"""

    def __init__(self):
        self.text_analyzer = TextAnalyzer()
        self.sensitive_data_analyzer = SensitiveDataAnalyzer()
        self.url_analyzer = URLAnalyzer()

    def check_message(self, text: str, user: str) -> Dict:
        """
        Проверка сообщения через DLP
        """
        # 1. Проверяем на запрещённые слова (блокируем всегда)
        keyword_result = self.text_analyzer.analyze(text)

        if keyword_result["status"] == "block":
            return {
                "allowed": False,
                "status": "block",
                "reason": keyword_result["message"],
                "found_keywords": keyword_result.get("found_keywords", []),
                "sensitive_data": None,
                "urls": None,
                "register_violation": False
            }

        # 2. Проверяем на конфиденциальные данные
        sensitive_result = self.sensitive_data_analyzer.analyze(text)

        if sensitive_result["has_sensitive_data"]:
            # РАЗРЕШАЕМ отправку, но регистрируем нарушение
            return {
                "allowed": True,
                "status": "warning",
                "reason": f"⚠️ {sensitive_result['message']}",
                "found_keywords": [],
                "sensitive_data": sensitive_result,
                "urls": None,
                "register_violation": True
            }

        # 3. Проверяем на наличие URL
        url_result = self.url_analyzer.analyze(text)

        if url_result["has_urls"]:
            # РАЗРЕШАЕМ отправку, но требуем проверки URL
            return {
                "allowed": True,
                "status": "url_check_required",
                "reason": f"🔗 {url_result['message']}",
                "found_keywords": [],
                "sensitive_data": None,
                "urls": url_result,
                "register_violation": False
            }

        return {
            "allowed": True,
            "status": "allow",
            "reason": "Сообщение разрешено",
            "found_keywords": [],
            "sensitive_data": None,
            "urls": None,
            "register_violation": False
        }


# Создаём глобальный экземпляр DLP движка
dlp_engine = DLPEngine()