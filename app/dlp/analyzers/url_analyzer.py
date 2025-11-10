import re
from typing import List, Dict


class URLAnalyzer:
    """Анализатор URL в сообщениях"""

    def __init__(self):
        # Паттерн для поиска URL
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )

    def extract_urls(self, text: str) -> List[str]:
        """Извлечение всех URL из текста"""
        urls = self.url_pattern.findall(text)
        return list(set(urls))  # Убираем дубликаты

    def analyze(self, text: str) -> Dict:
        """
        Анализ текста на наличие URL

        Возвращает:
        {
            "has_urls": True/False,
            "urls": [...],
            "message": "..."
        }
        """
        urls = self.extract_urls(text)

        if urls:
            return {
                "has_urls": True,
                "urls": urls,
                "url_count": len(urls),
                "message": f"Обнаружено ссылок: {len(urls)}"
            }

        return {
            "has_urls": False,
            "urls": [],
            "url_count": 0,
            "message": "Ссылки не обнаружены"
        }