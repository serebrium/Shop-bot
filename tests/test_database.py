import pytest
import tempfile
import os
from utils.db.storage import DatabaseManager


@pytest.fixture
def temp_db():
    """Создает временную базу данных для тестов"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = DatabaseManager(db_path)
    yield db

    # Очистка после тестов
    db.close()
    os.unlink(db_path)


class TestDatabaseManager:
    """Тесты для DatabaseManager"""

    def test_create_tables(self, temp_db):
        """Тест создания таблиц"""
        temp_db.create_tables()

        # Проверяем, что таблицы созданы
        tables = temp_db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [table[0] for table in tables]

        assert "categories" in table_names
        assert "products" in table_names
        assert "cart" in table_names
        assert "orders" in table_names
        assert "wallet" in table_names
        assert "questions" in table_names
        assert "db_version" in table_names

    def test_insert_and_fetch(self, temp_db):
        """Тест вставки и получения данных"""
        temp_db.create_tables()

        # Вставляем тестовую категорию (idx, title, created_at)
        temp_db.query(
            "INSERT INTO categories (idx, title) VALUES (?, ?)",
            ("test_idx", "Test Category"),
        )

        # Получаем данные
        result = temp_db.fetchone(
            "SELECT * FROM categories WHERE idx = ?", ("test_idx",)
        )

        assert result is not None
        assert result[0] == "test_idx"
        assert result[1] == "Test Category"

    def test_error_handling(self, temp_db):
        """Тест обработки ошибок"""
        temp_db.create_tables()

        # Пытаемся выполнить неверный запрос
        with pytest.raises(Exception):
            temp_db.query("INVALID SQL QUERY")
