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

    async def check_message(self, text: str, user: str, db_session=None) -> Dict:
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

        # 2. Проверяем на наличие URL (БЛОКИРУЕМ до модерации)
        url_result = self.url_analyzer.analyze(text)

        if url_result["has_urls"]:
            # Проверяем, есть ли URL в белом/черном списке
            if db_session:
                url_status = await self._check_urls_in_database(url_result["urls"], db_session)

                # Если все URL в белом списке - разрешаем
                if url_status["all_safe"]:
                    # Продолжаем проверку дальше
                    pass
                # Если хотя бы один URL в черном списке - блокируем
                elif url_status["has_malicious"]:
                    return {
                        "allowed": False,
                        "status": "block",
                        "reason": "❌ Обнаружены заблокированные ссылки",
                        "found_keywords": [],
                        "sensitive_data": None,
                        "urls": url_result,
                        "register_violation": False
                    }
                # Если есть неизвестные URL - блокируем и отправляем на модерацию
                elif url_status["has_unknown"]:
                    return {
                        "allowed": False,
                        "status": "url_moderation_required",
                        "reason": "🔗 Сообщение отправлено на модерацию (содержит ссылки)",
                        "found_keywords": [],
                        "sensitive_data": None,
                        "urls": url_result,
                        "register_violation": False
                    }
            else:
                # Если нет доступа к БД - блокируем по умолчанию
                return {
                    "allowed": False,
                    "status": "url_moderation_required",
                    "reason": "🔗 Сообщение отправлено на модерацию (содержит ссылки)",
                    "found_keywords": [],
                    "sensitive_data": None,
                    "urls": url_result,
                    "register_violation": False
                }

        # 3. Проверяем на конфиденциальные данные
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

        return {
            "allowed": True,
            "status": "allow",
            "reason": "Сообщение разрешено",
            "found_keywords": [],
            "sensitive_data": None,
            "urls": None,
            "register_violation": False
        }

    async def _check_urls_in_database(self, urls: list, db_session) -> dict:
        """Проверка URL в базе белых/черных списков"""
        from sqlalchemy import select
        from app.models.url_check import URLCheck

        result = {
            "all_safe": True,
            "has_malicious": False,
            "has_unknown": False
        }

        for url in urls:
            # Ищем URL в базе
            db_result = await db_session.execute(
                select(URLCheck)
                .where(URLCheck.url == url)
                .where(URLCheck.is_reviewed == True)
                .order_by(URLCheck.created_at.desc())
            )
            url_check = db_result.scalar_one_or_none()

            if url_check:
                if url_check.status == "malicious":
                    result["has_malicious"] = True
                    result["all_safe"] = False
                elif url_check.status != "safe":
                    result["all_safe"] = False
                    result["has_unknown"] = True
            else:
                # URL не найден в базе - неизвестный
                result["all_safe"] = False
                result["has_unknown"] = True

        return result


# Создаём глобальный экземпляр DLP движка
dlp_engine = DLPEngine()