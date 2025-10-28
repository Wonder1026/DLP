import aiohttp
import hashlib
from pathlib import Path
from app.config import settings


class VirusTotalService:
    """Сервис для работы с VirusTotal API"""

    BASE_URL = "https://www.virustotal.com/api/v3"

    def __init__(self):
        self.api_key = settings.VIRUSTOTAL_API_KEY

    async def scan_file(self, file_path: str) -> dict:
        """
        Отправить файл на сканирование в VirusTotal

        Возвращает словарь с результатом
        """

        if self.api_key == "your_api_key_here":
            # Режим тестирования без реального API
            return await self._mock_scan_result(file_path)

        try:
            # Читаем файл
            with open(file_path, 'rb') as f:
                file_content = f.read()

            # Вычисляем SHA256 хеш файла
            file_hash = hashlib.sha256(file_content).hexdigest()

            # Сначала проверяем, есть ли уже отчёт по этому файлу
            async with aiohttp.ClientSession() as session:
                headers = {"x-apikey": self.api_key}

                # Проверяем существующий отчёт
                url = f"{self.BASE_URL}/files/{file_hash}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_report(data)

                # Если отчёта нет, загружаем файл на сканирование
                url = f"{self.BASE_URL}/files"
                data = aiohttp.FormData()
                data.add_field('file', file_content,
                               filename=Path(file_path).name,
                               content_type='application/octet-stream')

                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "status": "scanning",
                            "summary": "Файл отправлен на сканирование. Результат будет доступен через несколько минут.",
                            "analysis_id": result.get("data", {}).get("id")
                        }
                    else:
                        return {
                            "status": "error",
                            "summary": f"Ошибка отправки файла: {response.status}"
                        }

        except Exception as e:
            return {
                "status": "error",
                "summary": f"Ошибка при работе с VirusTotal: {str(e)}"
            }

    async def _mock_scan_result(self, file_path: str) -> dict:
        """Имитация результата сканирования для тестирования"""

        file_ext = Path(file_path).suffix.lower()

        # Имитируем результат в зависимости от типа файла
        if file_ext == '.exe':
            return {
                "status": "suspicious",
                "summary": "⚠️ Обнаружены подозрительные признаки (2/70 антивирусов)",
                "malicious": 2,
                "suspicious": 0,
                "undetected": 68,
                "harmless": 0
            }
        else:
            return {
                "status": "clean",
                "summary": "✅ Угроз не обнаружено (0/70 антивирусов)",
                "malicious": 0,
                "suspicious": 0,
                "undetected": 70,
                "harmless": 0
            }

    def _parse_report(self, data: dict) -> dict:
        """Парсинг отчёта от VirusTotal"""

        try:
            attributes = data.get("data", {}).get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})

            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            undetected = stats.get("undetected", 0)
            harmless = stats.get("harmless", 0)

            total = malicious + suspicious + undetected + harmless

            if malicious > 0:
                status = "malicious"
                summary = f"❌ Обнаружены вирусы ({malicious}/{total} антивирусов)"
            elif suspicious > 0:
                status = "suspicious"
                summary = f"⚠️ Обнаружены подозрительные признаки ({suspicious}/{total} антивирусов)"
            else:
                status = "clean"
                summary = f"✅ Угроз не обнаружено (0/{total} антивирусов)"

            return {
                "status": status,
                "summary": summary,
                "malicious": malicious,
                "suspicious": suspicious,
                "undetected": undetected,
                "harmless": harmless
            }

        except Exception as e:
            return {
                "status": "error",
                "summary": f"Ошибка парсинга отчёта: {str(e)}"
            }


# Создаём глобальный экземпляр
virustotal_service = VirusTotalService()