# 🚨 Чеклист исправления критических проблем Shop-bot

## Приоритет: КРИТИЧЕСКИЙ 🔴

### ⚡ 1. Удаление небезопасного динамического управления администраторами

**Проблема**: Любой пользователь может стать администратором через UI бота.

#### Шаги исправления:

- [ ] **1.1. Удалить опасные обработчики из app.py**
  ```python
  # Удалить строки 82-141 в app.py:
  # - функцию user_mode()
  # - функцию admin_mode()
  # - соответствующие декораторы @dp.message()
  ```

- [ ] **1.2. Удалить кнопки выбора режима из /start**
  ```python
  # В функции cmd_start() удалить:
  # - переменные user_message и admin_message (строки 37-38)
  # - создание markup с кнопками (строки 56-60)
  # - параметр reply_markup из await message.answer()
  ```

- [ ] **1.3. Обновить обработчик /start**
  ```python
  @dp.message(Command("start"))
  async def cmd_start(message: types.Message):
      try:
          if not message.from_user:
              logger.warning("Получено сообщение без информации о пользователе")
              return

          user_id = message.from_user.id
          if not user_id or user_id <= 0:
              logger.warning(f"Некорректный ID пользователя: {user_id}")
              return

          logger.info(f"Пользователь {user_id} запустил бота")

          await message.answer(
              """Привет! 👋

  🤖 Я бот-магазин по продаже товаров любой категории.
      
  🛍️ Чтобы перейти в каталог и выбрать приглянувшиеся товары, воспользуйтесь командой /menu.

  💰 Пополнить счет можно через Яндекс.Кассу, Сбербанк или Qiwi.

  ❓ Возникли вопросы? Не проблема! Команда /sos поможет связаться с администраторами, которые постараются как можно быстрее откликнуться.

  🤝 Заказать похожего бота? Свяжитесь с разработчиком <a href="https://t.me/NikolaySimakov">Nikolay Simakov</a>, он не кусается! 😄
          """
          )
      except Exception as e:
          logger.error(f"Ошибка в команде start: {e}")
          await message.answer("Произошла ошибка при запуске бота. Попробуйте позже.")
  ```

- [ ] **1.4. Убедиться, что ADMINS загружается только из .env**
  ```python
  # В data/config.py проверить, что ADMINS - это неизменяемый список
  # Можно сделать его кортежем:
  ADMINS = tuple(map(int, admins_str.split(","))) if admins_str else ()
  ```

---

### ⚡ 2. Исправление SQL инъекций

**Проблема**: Прямая конкатенация пользовательских данных в SQL запросах.

#### Шаги исправления:

- [ ] **2.1. Проверить handlers/admin/add.py на SQL инъекции**
  ```python
  # Строка 63 - ОПАСНО:
  # WHERE product.tag = (SELECT title FROM categories WHERE idx=?)
  # Проверить, что category_idx правильно экранируется
  ```

- [ ] **2.2. Исправить все динамические SQL запросы**
  ```python
  # НЕПРАВИЛЬНО:
  db.query(f"SELECT * FROM {table_name} WHERE id = {user_id}")
  
  # ПРАВИЛЬНО:
  db.query("SELECT * FROM products WHERE id = ?", (user_id,))
  ```

- [ ] **2.3. Добавить валидацию callback_data**
  ```python
  # В handlers/admin/add.py строка 59:
  try:
      category_idx = int(query.data.split("_")[-1])
  except (ValueError, IndexError):
      await query.answer("Некорректные данные")
      return
  ```

- [ ] **2.4. Проверить все обработчики на безопасность**
  - handlers/admin/add.py
  - handlers/admin/orders.py
  - handlers/admin/questions.py
  - handlers/user/cart.py
  - handlers/user/catalog.py

---

### ⚡ 3. Обновление документации под aiogram 3.x

**Проблема**: Документация указывает aiogram 2.9.2, но используется 3.22.0+.

#### Шаги исправления:

- [ ] **3.1. Обновить .cursor/rules/shop-bot-complete.mdc**
  ```markdown
  # Изменить строку 30:
  - **aiogram**: 3.22.0+ (актуальная версия)
  
  # Обновить примеры кода под aiogram 3.x синтаксис
  ```

- [ ] **3.2. Обновить README.md**
  ```markdown
  ## Требования
  - Python 3.9+
  - aiogram 3.22.0+
  ```

- [ ] **3.3. Обновить примеры в документации**
  - Заменить устаревший синтаксис aiogram 2.x
  - Обновить импорты
  - Исправить примеры обработчиков

---

### ⚡ 4. Создание виртуального окружения

**Проблема**: Отсутствует venv, невозможно проверить установленные пакеты.

#### Шаги исправления:

- [ ] **4.1. Создать виртуальное окружение**
  ```bash
  python3.9 -m venv venv
  ```

- [ ] **4.2. Активировать окружение**
  ```bash
  source venv/bin/activate  # Linux/macOS
  # или
  venv\Scripts\activate  # Windows
  ```

- [ ] **4.3. Установить зависимости**
  ```bash
  pip install --upgrade pip
  pip install -r requirements.txt
  ```

- [ ] **4.4. Проверить установленные версии**
  ```bash
  pip list
  pip check  # Проверка совместимости
  ```

- [ ] **4.5. Создать файл .env из примера**
  ```bash
  cp env.example .env
  # Отредактировать .env и добавить BOT_TOKEN
  ```

---

### ⚡ 5. Добавление валидации входных данных

**Проблема**: Отсутствует проверка пользовательского ввода.

#### Шаги исправления:

- [ ] **5.1. Создать модуль валидации**
  ```python
  # utils/validators.py
  import re
  from typing import Optional
  
  def validate_price(price: str) -> Optional[int]:
      """Валидация цены товара"""
      try:
          price_int = int(price)
          if price_int <= 0 or price_int > 1000000:
              return None
          return price_int
      except ValueError:
          return None
  
  def validate_text_input(text: str, max_length: int = 1000) -> Optional[str]:
      """Валидация текстового ввода"""
      if not text or len(text) > max_length:
          return None
      # Удаляем опасные символы
      cleaned = re.sub(r'[<>\"\'&]', '', text)
      return cleaned.strip()
  
  def validate_callback_data(data: str, expected_prefix: str) -> Optional[str]:
      """Валидация callback_data"""
      if not data or not data.startswith(expected_prefix):
          return None
      return data
  ```

- [ ] **5.2. Применить валидацию в обработчиках**
  ```python
  # В handlers/admin/add.py
  from utils.validators import validate_price, validate_text_input
  
  @router.message(IsAdmin(), ProductState.price)
  async def process_price(message: Message, state: FSMContext):
      price = validate_price(message.text)
      if not price:
          await message.answer("Укажите корректную цену (число от 1 до 1000000)")
          return
      
      # Продолжение обработки...
  ```

- [ ] **5.3. Добавить лимиты на размер данных**
  - Название товара: максимум 100 символов
  - Описание: максимум 1000 символов
  - Адрес доставки: максимум 500 символов

---

### ⚡ 6. Улучшение обработки ошибок

**Проблема**: Использование общих except без специфичной обработки.

#### Шаги исправления:

- [ ] **6.1. Заменить общие исключения на специфичные**
  ```python
  # НЕПРАВИЛЬНО:
  except Exception as e:
      logger.error(f"Ошибка: {e}")
  
  # ПРАВИЛЬНО:
  except sqlite3.IntegrityError as e:
      logger.error(f"Ошибка целостности БД: {e}")
      await message.answer("Такая запись уже существует")
  except sqlite3.OperationalError as e:
      logger.error(f"Ошибка операции БД: {e}")
      await message.answer("Временная ошибка базы данных")
  except Exception as e:
      logger.error(f"Неожиданная ошибка: {e}", exc_info=True)
      await message.answer("Произошла непредвиденная ошибка")
  ```

- [ ] **6.2. Удалить голые except:**
  ```python
  # Найти и заменить все:
  except:
      pass
  
  # На:
  except Exception:
      logger.exception("Ошибка в миграции")
  ```

- [ ] **6.3. Добавить контекст в логирование**
  ```python
  logger.error(
      f"Ошибка при добавлении товара",
      extra={
          "user_id": message.from_user.id,
          "product_title": title,
          "error": str(e)
      }
  )
  ```

---

### ⚡ 7. Защита от спама и флуда

**Проблема**: Отсутствует защита от массовых запросов.

#### Шаги исправления:

- [ ] **7.1. Создать middleware для rate limiting**
  ```python
  # middlewares/antiflood.py
  from aiogram import BaseMiddleware
  from aiogram.types import Message
  from typing import Dict, Any, Callable, Awaitable
  import time
  
  class AntiFloodMiddleware(BaseMiddleware):
      def __init__(self, rate_limit: float = 0.5):
          self.rate_limit = rate_limit
          self.user_last_message = {}
      
      async def __call__(
          self,
          handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
          event: Message,
          data: Dict[str, Any]
      ) -> Any:
          user_id = event.from_user.id
          current_time = time.time()
          
          if user_id in self.user_last_message:
              if current_time - self.user_last_message[user_id] < self.rate_limit:
                  await event.answer("Слишком много запросов. Подождите немного.")
                  return
          
          self.user_last_message[user_id] = current_time
          return await handler(event, data)
  ```

- [ ] **7.2. Подключить middleware**
  ```python
  # В app.py после создания dp:
  from middlewares.antiflood import AntiFloodMiddleware
  
  dp.message.middleware(AntiFloodMiddleware(rate_limit=0.5))
  ```

- [ ] **7.3. Добавить лимиты для разных действий**
  - Обычные команды: 1 в 0.5 секунды
  - Добавление товара: 1 в 5 секунд
  - Оформление заказа: 1 в 10 секунд

---

### ⚡ 8. Перенос хранения изображений

**Проблема**: Изображения хранятся в БД как BLOB.

#### Шаги исправления:

- [ ] **8.1. Создать директорию для изображений**
  ```bash
  mkdir -p data/images
  echo "data/images/*" >> .gitignore
  ```

- [ ] **8.2. Изменить сохранение изображений**
  ```python
  # utils/image_storage.py
  import os
  import uuid
  from pathlib import Path
  
  IMAGE_DIR = Path("data/images")
  IMAGE_DIR.mkdir(exist_ok=True)
  
  async def save_image(image_data: bytes) -> str:
      """Сохраняет изображение и возвращает путь"""
      filename = f"{uuid.uuid4().hex}.jpg"
      filepath = IMAGE_DIR / filename
      
      with open(filepath, 'wb') as f:
          f.write(image_data)
      
      return str(filepath)
  
  def get_image_path(filename: str) -> Path:
      """Возвращает полный путь к изображению"""
      return IMAGE_DIR / filename
  ```

- [ ] **8.3. Обновить схему БД**
  ```sql
  -- Изменить колонку photo с BLOB на TEXT
  ALTER TABLE products ADD COLUMN photo_path TEXT;
  -- Миграция существующих данных
  -- После миграции удалить старую колонку photo
  ```

- [ ] **8.4. Обновить код загрузки изображений**
  ```python
  # В handlers/admin/add.py
  from utils.image_storage import save_image
  
  # Вместо сохранения в БД:
  photo_path = await save_image(downloaded_file)
  # Сохраняем путь в БД
  ```

---

## 📋 Порядок выполнения

1. **Сначала**: Пункты 1 и 2 (безопасность)
2. **Затем**: Пункты 4 и 3 (окружение и документация)
3. **После**: Пункты 5, 6, 7 (валидация и защита)
4. **В конце**: Пункт 8 (оптимизация)

## ⏱️ Время выполнения

- **Критические исправления (1-2)**: 2-3 часа
- **Базовые улучшения (3-6)**: 4-6 часов
- **Дополнительные улучшения (7-8)**: 3-4 часа

**Общее время**: ~1-2 рабочих дня

## 🎯 Проверка результатов

После выполнения всех пунктов:

- [ ] Запустить бота и проверить, что нельзя стать админом через UI
- [ ] Проверить все SQL запросы на параметризацию
- [ ] Запустить тесты безопасности
- [ ] Проверить логи на наличие ошибок
- [ ] Протестировать защиту от флуда

## ⚠️ ВАЖНО

**НЕ ДЕПЛОИТЬ В PRODUCTION ДО ИСПРАВЛЕНИЯ ПУНКТОВ 1 и 2!**