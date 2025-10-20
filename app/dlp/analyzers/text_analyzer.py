from flashtext import KeywordProcessor
from typing import List, Dict


class TextAnalyzer:
    """Анализатор текста на запрещённые слова"""

    def __init__(self):
        self.keyword_processor = KeywordProcessor()
        # Добавляем тестовые запрещённые слова
        self.forbidden_keywords = [
            "конфиденциально",
            "секретно",
            "пароль",
            "password",
            "банковская карта",
            "кредитная карта"
        ]
        self._load_keywords()

    def _load_keywords(self):
        """Загрузка ключевых слов в процессор"""
        for keyword in self.forbidden_keywords:
            self.keyword_processor.add_keyword(keyword)

    def analyze(self, text: str) -> Dict:
        """
        Анализ текста на запрещённые слова

        Возвращает:
        {
            "status": "allow" | "block" | "quarantine",
            "found_keywords": [...],
            "message": "..."
        }
        """
        # Ищем запрещённые слова
        found = self.keyword_processor.extract_keywords(text.lower())

        if not found:
            return {
                "status": "allow",
                "found_keywords": [],
                "message": "Сообщение разрешено"
            }

        # Если найдены запрещённые слова - блокируем
        return {
            "status": "block",
            "found_keywords": found,
            "message": f"Обнаружены запрещённые слова: {', '.join(found)}"
        }

    def add_keyword(self, keyword: str):
        """Добавить новое ключевое слово"""
        if keyword.lower() not in self.forbidden_keywords:
            self.forbidden_keywords.append(keyword.lower())
            self.keyword_processor.add_keyword(keyword.lower())

    def remove_keyword(self, keyword: str):
        """Удалить ключевое слово"""
        if keyword.lower() in self.forbidden_keywords:
            self.forbidden_keywords.remove(keyword.lower())
            self.keyword_processor.remove_keyword(keyword.lower())

    def get_keywords(self) -> List[str]:
        """Получить список всех ключевых слов"""
        return self.forbidden_keywords.copy()