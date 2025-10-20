from fastapi import APIRouter
from typing import List
from pydantic import BaseModel
from app.dlp.engine import dlp_engine

router = APIRouter()


class KeywordAdd(BaseModel):
    """Схема для добавления ключевого слова"""
    keyword: str


class KeywordRemove(BaseModel):
    """Схема для удаления ключевого слова"""
    keyword: str


@router.get("/keywords")
def get_keywords():
    """Получить список всех запрещённых слов"""
    return {
        "keywords": dlp_engine.text_analyzer.get_keywords(),
        "count": len(dlp_engine.text_analyzer.get_keywords())
    }


@router.post("/keywords")
def add_keyword(data: KeywordAdd):
    """Добавить новое запрещённое слово"""
    dlp_engine.text_analyzer.add_keyword(data.keyword)
    return {
        "status": "success",
        "message": f"Ключевое слово '{data.keyword}' добавлено",
        "keywords": dlp_engine.text_analyzer.get_keywords()
    }


@router.delete("/keywords")
def remove_keyword(data: KeywordRemove):
    """Удалить запрещённое слово"""
    dlp_engine.text_analyzer.remove_keyword(data.keyword)
    return {
        "status": "success",
        "message": f"Ключевое слово '{data.keyword}' удалено",
        "keywords": dlp_engine.text_analyzer.get_keywords()
    }


@router.post("/keywords/test")
def test_message(text: str):
    """Тестирование сообщения через DLP"""
    result = dlp_engine.check_message(text, "TestUser")
    return result