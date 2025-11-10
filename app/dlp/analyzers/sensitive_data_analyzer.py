import re
from typing import List, Dict


class SensitiveDataAnalyzer:
    """Анализатор конфиденциальных данных"""

    def __init__(self):
        # Паттерны для поиска конфиденциальных данных
        self.patterns = {
            "bank_card": {
                "regex": r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',
                "name": "Номер банковской карты",
                "severity": "high"
            },
            "email": {
                "regex": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                "name": "Email адрес",
                "severity": "medium"
            },
            "phone": {
                "regex": r'\b(?:\+7|8)[\s\-]?\(?(\d{3})\)?[\s\-]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})\b',
                "name": "Номер телефона",
                "severity": "medium"
            },
            "passport": {
                "regex": r'\b\d{4}[\s\-]?\d{6}\b',
                "name": "Серия и номер паспорта",
                "severity": "high"
            },
            "inn": {
                "regex": r'\b\d{10}(?:\d{2})?\b',
                "name": "ИНН",
                "severity": "medium"
            },
            "snils": {
                "regex": r'\b\d{3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}\b',
                "name": "СНИЛС",
                "severity": "high"
            }
        }

    def analyze(self, text: str) -> Dict:
        """
        Анализ текста на наличие конфиденциальных данных

        Возвращает:
        {
            "has_sensitive_data": True/False,
            "found_data": [...],
            "severity": "low/medium/high",
            "message": "..."
        }
        """
        found_data = []
        max_severity = "low"

        for data_type, pattern_info in self.patterns.items():
            matches = re.findall(pattern_info["regex"], text)

            if matches:
                # Для номера телефона matches это кортежи, преобразуем
                if data_type == "phone":
                    matches = [f"+7 ({m[0]}) {m[1]}-{m[2]}-{m[3]}" for m in matches]

                for match in matches:
                    found_data.append({
                        "type": data_type,
                        "name": pattern_info["name"],
                        "value": self._mask_value(str(match), data_type),
                        "severity": pattern_info["severity"]
                    })

                # Обновляем максимальную критичность
                if pattern_info["severity"] == "high":
                    max_severity = "high"
                elif pattern_info["severity"] == "medium" and max_severity != "high":
                    max_severity = "medium"

        if found_data:
            data_types = ", ".join(set([d["name"] for d in found_data]))
            return {
                "has_sensitive_data": True,
                "found_data": found_data,
                "severity": max_severity,
                "message": f"Обнаружены конфиденциальные данные: {data_types}"
            }

        return {
            "has_sensitive_data": False,
            "found_data": [],
            "severity": "low",
            "message": "Конфиденциальные данные не обнаружены"
        }

    def _mask_value(self, value: str, data_type: str) -> str:
        """Маскирование значения для отображения"""
        if data_type == "bank_card":
            # Показываем только последние 4 цифры
            digits = re.sub(r'\D', '', value)
            return f"****-****-****-{digits[-4:]}" if len(digits) >= 4 else "****"

        elif data_type == "email":
            parts = value.split('@')
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                masked_username = username[0] + "*" * (len(username) - 1) if len(username) > 1 else "*"
                return f"{masked_username}@{domain}"

        elif data_type == "phone":
            return re.sub(r'\d(?=\d{2})', '*', value)

        elif data_type in ["passport", "inn", "snils"]:
            return re.sub(r'\d', '*', value)

        return value