import sqlite3 as lite
import logging

logger = logging.getLogger(__name__)


class DatabaseManager(object):

    def __init__(self, path):
        try:
            self.conn = lite.connect(path, check_same_thread=False)
            self.conn.execute("pragma foreign_keys = on")
            self.conn.execute("pragma journal_mode = WAL")
            self.conn.execute("pragma synchronous = NORMAL")
            self.conn.commit()
            self.cur = self.conn.cursor()
            logger.info(f"База данных подключена: {path}")
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise

    def create_tables(self):
        try:
            # Создаем таблицу версий для миграций
            self.query(
                """
                CREATE TABLE IF NOT EXISTS db_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Создаем таблицы с улучшенной структурой
            self.query(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    idx TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            self.query(
                """
                CREATE TABLE IF NOT EXISTS products (
                    idx TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    body TEXT,
                    photo_path TEXT,
                    price REAL NOT NULL CHECK (price > 0),
                    tag TEXT,
                    category_idx TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_idx) REFERENCES categories(idx)
                )
            """
            )

            self.query(
                """
                CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cid INTEGER NOT NULL,
                    product_idx TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_idx) REFERENCES products(idx)
                )
            """
            )

            self.query(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cid INTEGER NOT NULL,
                    usr_name TEXT NOT NULL,
                    usr_address TEXT NOT NULL,
                    products TEXT NOT NULL,
                    total_price REAL NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            self.query(
                """
                CREATE TABLE IF NOT EXISTS wallet (
                    cid INTEGER PRIMARY KEY,
                    balance REAL DEFAULT 0.0 CHECK (balance >= 0),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            self.query(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cid INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Создаем индексы для улучшения производительности
            self.query(
                "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_idx)"
            )
            self.query("CREATE INDEX IF NOT EXISTS idx_cart_cid ON cart(cid)")
            self.query("CREATE INDEX IF NOT EXISTS idx_orders_cid ON orders(cid)")
            self.query("CREATE INDEX IF NOT EXISTS idx_questions_cid ON questions(cid)")

            # Применяем миграции
            self._apply_migrations()

            logger.info("Таблицы базы данных созданы/обновлены")

        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise

    def _apply_migrations(self):
        """Применяет миграции базы данных"""
        try:
            # Получаем текущую версию БД
            current_version = 0
            try:
                result = self.fetchone("SELECT MAX(version) FROM db_version")
                if result and result[0]:
                    current_version = result[0]
            except:
                pass

            # Список миграций
            migrations = [
                (1, self._migration_1_add_timestamps),
                (2, self._migration_2_add_status_fields),
                (3, self._migration_3_add_foreign_keys),
                (4, self._migration_4_move_photo_to_path),
            ]

            # Применяем новые миграции
            for version, migration_func in migrations:
                if version > current_version:
                    logger.info(f"Применяем миграцию {version}")
                    migration_func()
                    self.query(
                        "INSERT INTO db_version (version) VALUES (?)", (version,)
                    )
                    logger.info(f"Миграция {version} применена")

        except Exception as e:
            logger.error(f"Ошибка применения миграций: {e}")
            raise

    def _migration_1_add_timestamps(self):
        """Миграция 1: Добавление временных меток"""
        try:
            # Добавляем колонки created_at если их нет
            tables = ["categories", "products", "cart", "orders", "wallet", "questions"]
            for table in tables:
                try:
                    self.query(
                        f"ALTER TABLE {table} ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    )
                except:
                    pass  # Колонка уже существует
        except Exception as e:
            logger.error(f"Ошибка миграции 1: {e}")
            raise

    def _migration_2_add_status_fields(self):
        """Миграция 2: Добавление полей статуса"""
        try:
            # Добавляем поле status в orders
            try:
                self.query(
                    'ALTER TABLE orders ADD COLUMN status TEXT DEFAULT "pending"'
                )
            except:
                pass

            # Добавляем поле status в questions
            try:
                self.query(
                    'ALTER TABLE questions ADD COLUMN status TEXT DEFAULT "open"'
                )
            except:
                pass
        except Exception as e:
            logger.error(f"Ошибка миграции 2: {e}")
            raise

    def _migration_3_add_foreign_keys(self):
        """Миграция 3: Добавление внешних ключей"""
        try:
            # Добавляем внешний ключ для products.category_idx
            try:
                self.query("ALTER TABLE products ADD COLUMN category_idx TEXT")
                self.query(
                    "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_idx)"
                )
            except:
                pass
        except Exception as e:
            logger.error(f"Ошибка миграции 3: {e}")
            raise

    def _migration_4_move_photo_to_path(self):
        """Миграция 4: Перенос фото из BLOB в TEXT (путь к файлу)"""
        try:
            # Добавляем колонку photo_path, если её нет
            try:
                self.query("ALTER TABLE products ADD COLUMN photo_path TEXT")
            except:
                pass
            # Колонка photo остаётся для обратной совместимости; миграцию данных выполняем на уровне приложения при первом доступе
        except Exception as e:
            logger.error(f"Ошибка миграции 4: {e}")
            raise

    def query(self, arg, values=None):
        try:
            if values is None:
                self.cur.execute(arg)
            else:
                self.cur.execute(arg, values)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            self.conn.rollback()
            raise

    def fetchone(self, arg, values=None):
        try:
            if values is None:
                self.cur.execute(arg)
            else:
                self.cur.execute(arg, values)
            return self.cur.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения одной записи: {e}")
            raise

    def fetchall(self, arg, values=None):
        try:
            if values is None:
                self.cur.execute(arg)
            else:
                self.cur.execute(arg, values)
            return self.cur.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения всех записей: {e}")
            raise

    def close(self):
        """Закрывает соединение с базой данных"""
        try:
            if self.conn:
                self.conn.close()
                logger.info("Соединение с БД закрыто")
        except Exception as e:
            logger.error(f"Ошибка закрытия БД: {e}")

    def __del__(self):
        try:
            self.close()
        except:
            pass


"""

products: idx text, title text, body text, photo blob, price int, tag text

orders: cid int, usr_name text, usr_address text, products text

cart: cid int, idx text, quantity int ==> product_idx

categories: idx text, title text

wallet: cid int, balance real

questions: cid int, question text

"""
