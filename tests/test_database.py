import pytest
import os
import tempfile
from utils.db.storage import DatabaseManager


class TestDatabase:
    """Тесты для базы данных"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Создаем временный файл базы данных
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db = DatabaseManager(self.temp_db.name)

    def teardown_method(self):
        """Очистка после каждого теста"""
        # Удаляем временный файл
        self.temp_db.close()
        os.unlink(self.temp_db.name)

    def test_create_tables(self):
        """Тест создания таблиц"""
        self.db.create_tables()

        # Проверяем, что таблицы созданы
        tables = self.db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [table[0] for table in tables]

        assert "categories" in table_names
        assert "products" in table_names
        assert "cart" in table_names
        assert "orders" in table_names
        assert "wallet" in table_names
        assert "questions" in table_names

    def test_insert_and_select(self):
        """Тест вставки и выборки данных"""
        self.db.create_tables()

        # Вставляем тестовые данные
        self.db.query("INSERT INTO categories (title) VALUES (?)", ("Test Category",))

        # Проверяем, что данные вставлены
        result = self.db.fetchone(
            "SELECT title FROM categories WHERE title = ?", ("Test Category",)
        )
        assert result is not None
        assert result[0] == "Test Category"

    def test_empty_database(self):
        """Тест пустой базы данных"""
        self.db.create_tables()

        # Проверяем, что таблицы пустые
        categories = self.db.fetchall("SELECT * FROM categories")
        assert len(categories) == 0


if __name__ == "__main__":
    pytest.main([__file__])
