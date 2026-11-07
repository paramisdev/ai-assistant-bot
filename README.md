# ai-assistant-bot

Telegram-бот с ИИ-ассистентом на aiogram 3.x. Отправляет текст в LLM через
OpenAI-совместимый API, умеет делать краткую выжимку длинных текстов и
корректно обрабатывает ошибки внешнего API.

## Возможности

- обычный текст отправляется в LLM, ответ возвращается в чат;
- `/summarize` просит длинный текст и делает краткую выжимку;
- длинный текст автоматически разбивается на чанки и суммируется по частям;
- обрабатываются таймауты, недоступность API, лимиты запросов и токенов;
- API-ключи хранятся через `SecretStr` и не попадают в логи;
- тесты замокают HTTP-запросы к LLM и не тратят токены.

## Получение ключа API

1. Зарегистрируйтесь у провайдера, совместимого с OpenAI Chat Completions API
   (например, OpenAI или другой совместимый сервис).
2. Создайте API-ключ в личном кабинете провайдера.
3. Уточните базовый URL для chat completions. Для OpenAI это
   `https://api.openai.com/v1/chat/completions`.
4. Скопируйте ключ и URL в `.env` — не коммитьте этот файл.

## Запуск

```bash
uv sync
cp .env.example .env
# заполните BOT_TOKEN и LLM_API_KEY
uv run python -m bot
```

Для Windows PowerShell копирование файла:

```powershell
Copy-Item .env.example .env
```

Токен Telegram-бота выдаёт [@BotFather](https://t.me/BotFather).

## Переменные окружения

| Переменная | Назначение | Значение по умолчанию |
|---|---|---|
| `BOT_TOKEN` | токен Telegram-бота | обязательна |
| `LLM_API_KEY` | ключ LLM-провайдера | обязательна |
| `LLM_API_URL` | URL chat completions | `https://api.openai.com/v1/chat/completions` |
| `LLM_MODEL` | имя модели | `gpt-4o-mini` |
| `LLM_TIMEOUT_SECONDS` | таймаут HTTP-запроса | `60` |
| `LLM_MAX_INPUT_CHARS` | максимум символов в запросе | `60000` |
| `LLM_MAX_CHUNK_CHARS` | размер чанка для суммаризации | `6000` |
| `LLM_TEMPERATURE` | температура генерации | `0.2` |

## Команды бота

- `/start` — приветствие и краткая инструкция;
- `/help` — список команд;
- `/summarize` — запросить длинный текст и получить выжимку;
- `/cancel` — отменить ожидание текста.

## Проверка качества

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy src/bot
uv run pytest -q
```

## Структура

```text
src/bot/
  __main__.py      # точка входа
  main.py          # Bot, Dispatcher, запуск polling
  config.py        # настройки и SecretStr
  handlers/        # команды и обработка сообщений
  services/        # LLM-клиент, промпты, чанкинг
  states/          # FSM-состояния
tests/             # тесты с Mock/AsyncMock
```

## Лицензия

MIT. Автор: Nachtrieb Tressel.
