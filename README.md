# 🍕 Pizza Order AI Assistant

**AI-powered conversational agent for pizza ordering, user memory and knowledge retrieval.**

Проект демонстрирует разработку полноценного **LLM-based AI Agent** с использованием LangChain и LangGraph. Агент умеет вести диалог с пользователем, определять необходимые действия, вызывать инструменты, работать с историей заказов, получать информацию из базы данных и выполнять операции, требующие подтверждения человека.

Проект построен с разделением AI-, business- и data-access слоёв и ориентирован на архитектуру, которую можно расширять для интеграции с внешними сервисами и enterprise-системами.

---

## 🚀 Основные возможности

- 🤖 LLM Agent на базе **LangChain / LangGraph**
- 🔧 Tool Calling для взаимодействия с backend-функциями
- 👤 Работа с профилем пользователя
- 🧠 Persistent conversation state
- 📦 История заказов пользователя
- 🍕 Получение списка пицц и актуальных цен
- 🧮 Автоматический расчёт стоимости заказа на backend
- 🛡️ Pydantic validation входных данных
- 👨‍💻 **Human-in-the-Loop** для подтверждения заказа
- 📚 RAG для поиска информации о составе и рецептах пиццы
- 💾 SQLite + SQLAlchemy для хранения бизнес-данных
- 🗂️ Repository / Service архитектура
- 🔄 Checkpointing состояния AI Agent
- 🧪 Unit-тестирование бизнес-логики и HITL
- 🧹 Разделение AI orchestration и business logic

---

# 🧠 Архитектура

Проект разделён на несколько логических уровней:

```text
                    ┌──────────────────────┐
                    │        User          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      AI Agent        │
                    │   LangChain/LangGraph│
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌───────────┐    ┌───────────┐   ┌────────────┐
        │   Tools   │    │    RAG    │   │    HITL    │
        └─────┬─────┘    └───────────┘   └──────┬─────┘
              │                                  │
              ▼                                  ▼
        ┌───────────┐                    Human Approval
        │ Services  │
        └─────┬─────┘
              │
              ▼
        ┌──────────────┐
        │ Repositories │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │  SQLAlchemy  │
        │    SQLite    │
        └──────────────┘
```

Главный принцип архитектуры:

> **LLM определяет намерение и предлагает действие, а application layer отвечает за валидацию, бизнес-правила и выполнение операции.**

Это позволяет не передавать критическую бизнес-логику непосредственно LLM.

---

# 🔄 Agent Flow

Типичный сценарий оформления заказа:

```text
User
 │
 │ "Хочу Песту и Пепперони"
 ▼
AI Agent
 │
 ├── get_pizza_names()
 │
 ├── get_pizza_price()
 │
 └── определяет необходимые параметры
          │
          ▼
     получает адрес
          │
          ▼
     формирует заказ
          │
          ▼
     save_order()
          │
          ▼
   ┌──────────────────┐
   │ Human-in-the-Loop│
   │    APPROVAL      │
   └────────┬─────────┘
            │
       ┌────┴────┐
       │         │
     APPROVE    REJECT
       │         │
       ▼         ▼
   save order   cancel
       │
       ▼
    Database
```

---

# 👨‍💻 Human-in-the-Loop

Одной из ключевых особенностей проекта является использование **Human-in-the-Loop middleware**.

Операции, изменяющие состояние системы, не должны выполняться агентом безусловно.

Для `save_order` агент создаёт interrupt:

```text
Tool execution requires approval

Tool: save_order

Args:
{
    "items": [...],
    "address": "...",
    "total": ...
}
```

Пользователь принимает решение:

```text
Подтвердить заказ? [да/нет]
```

После подтверждения execution продолжается через LangGraph `Command(resume=...)`.

### Почему это важно

LLM может ошибиться:

- выбрать неправильный товар;
- неправильно определить количество;
- интерпретировать адрес;
- вызвать tool в неподходящий момент.

Поэтому потенциально опасные операции проходят через дополнительный контроль человека.

Архитектурный принцип:

```text
Read operation
      │
      ▼
   Tool call
      │
      ▼
    Result


Write / side-effect operation
      │
      ▼
   Tool call
      │
      ▼
    HITL
      │
 ┌────┴────┐
 ▼         ▼
Approve   Reject
 │
 ▼
Execute
```

---

# 🔧 Tools

Agent взаимодействует с приложением через специализированные tools.

Основные категории:

### Product tools

Получение информации о доступных пиццах:

```text
get_pizza_names()
get_pizza_price()
```

### Order tools

Работа с заказами:

```text
save_order()
```

### User tools

Работа с пользовательским контекстом и историей заказов.

### RAG tool

Получение информации из базы знаний:

```text
retriever(query)
```

Например:

```text
User:
Из чего состоит пицца Песта?

Agent:
→ retriever("состав пиццы Песта")
→ получает релевантные документы
→ формирует ответ
```

---

# 📚 RAG

Проект содержит отдельный retrieval layer для получения информации о продуктах.

Основная идея:

```text
User Question
      │
      ▼
    Agent
      │
      ▼
 Retriever
      │
      ▼
Vector Store
      │
      ▼
Relevant Documents
      │
      ▼
     LLM
      │
      ▼
    Answer
```

RAG используется для информации, которую нецелесообразно хранить непосредственно в system prompt.

Например:

- состав пиццы;
- ингредиенты;
- описание рецепта;
- дополнительная информация о продукте.

Это позволяет обновлять knowledge base независимо от prompt'а агента.

---

# 💾 Persistence & Memory

Проект использует два типа состояния.

### Agent state

Для сохранения состояния выполнения агента используется LangGraph checkpointing.

```text
Conversation
     │
     ▼
LangGraph State
     │
     ▼
Checkpoint
     │
     ▼
SQLite
```

Это позволяет продолжать работу с существующим conversation thread.

### User memory

Пользовательский контекст хранится отдельно и может использоваться агентом для персонализации.

Например:

```text
User:
Какие заказы я делал?

Agent:
Вы делали:
- Пепперони — 3 шт.
- Песта — 5 шт.
```

Таким образом, agent работает не только с текущим сообщением, но и с сохранённым контекстом пользователя.

---

# 🗄️ Database Architecture

Для работы с бизнес-данными используется:

- SQLAlchemy 2.x
- SQLite

Data access разделён через Repository pattern.

```text
AI Tool
   │
   ▼
Service
   │
   ▼
Repository
   │
   ▼
SQLAlchemy
   │
   ▼
Database
```

Например:

```text
save_order()
      │
      ▼
OrderService
      │
      ▼
OrderRepository
      │
      ▼
OrderDB
```

Такой подход позволяет не связывать LLM tools непосредственно с SQLAlchemy.

---

# 🧩 Service Layer

Business logic находится в services.

Например, `OrderService` отвечает за:

- получение товаров;
- проверку существования продукта;
- расчёт стоимости;
- подготовку данных заказа;
- создание заказа.

Важный принцип проекта:

> **Финальная стоимость заказа рассчитывается application layer на основании данных из базы, а не доверяется LLM.**

Например:

```text
LLM:
Пользователь заказал 3 Пепперони

        ↓

ProductRepository:
Пепперони = 350 ₽

        ↓

OrderService:
350 × 3 = 1050 ₽

        ↓

Database:
total = 1050
```

Это защищает бизнес-логику от ошибок генеративной модели.

---

# 🛡️ Data Validation

Для валидации входных данных используется **Pydantic**.

Пример модели заказа:

```python
class OrderItem(BaseModel):
    name: str
    quantity: int = Field(ge=1)
```

Таким образом, некорректные данные не должны бесконтрольно попадать в business layer.

Общий pipeline:

```text
LLM
 │
 ▼
Structured data
 │
 ▼
Pydantic
 │
 ▼
Business validation
 │
 ▼
Service
 │
 ▼
Repository
```

---

# 🏗️ Project Structure

```text
Pizza-Order-AI-Assistant2/
│
├── modules/
│   │
│   ├── agent.py
│   ├── model.py
│   ├── config.py
│   ├── system_prompt.py
│   │
│   ├── middleware/
│   │   ├── history_trimmer.py
│   │   └── order_confirmation.py
│   │
│   ├── tools/
│   │   ├── order.py
│   │   ├── user.py
│   │   └── retriever.py
│   │
│   ├── services/
│   │   ├── order.py
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── repositories/
│   │   ├── order.py
│   │   ├── product.py
│   │   └── user.py
│   │
│   ├── schemas/
│   │
│   └── database/
│       ├── models/
│       └── agent/
│
├── tests/
│
├── database/
│
├── start.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

# 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| **Python 3.12** | Main programming language |
| **LangChain** | LLM and tool integration |
| **LangGraph** | Agent orchestration and state |
| **GigaChat** | Large Language Model |
| **Pydantic** | Data validation |
| **SQLAlchemy** | ORM / database access |
| **SQLite** | Persistent storage |
| **Vector Store** | RAG / semantic retrieval |
| **Pytest** | Automated testing |
| **Pyright** | Static type checking |

---

# 🧪 Testing

Проект содержит тесты для критической бизнес-логики и Human-in-the-Loop сценариев.

Особое внимание уделено поведению подтверждения заказа:

```text
Approve
Reject
Short confirmation
Invalid confirmation
```

Пример тестируемого поведения:

```text
User → approve
       ↓
save_order executed

User → reject
       ↓
save_order not executed
```

Цель тестов — проверять не только отдельные функции, но и важные бизнес-сценарии.

---

# 🔐 Security & Reliability Principles

При разработке проекта используются следующие принципы.

### Secrets

API credentials не должны храниться в исходном коде.

Конфигурация загружается из environment variables:

```python
AUTH_KEY = os.environ.get("AUTH_KEY")
```

### LLM is not trusted

Модель не является источником истины для:

- цен;
- итоговой стоимости;
- статуса заказа;
- выполнения критических операций.

### Human approval

Операция создания заказа требует явного подтверждения пользователя.

### Backend validation

Данные проходят валидацию до попадания в database layer.

---

# ▶️ Local Setup

## 1. Clone repository

```bash
git clone https://github.com/newracer277-jpg/Pizza-Order-AI-Assistant2.git

cd Pizza-Order-AI-Assistant2
```

## 2. Create virtual environment

Windows:

```bash
python -m venv .venv

.venv\Scripts\activate
```

Linux / macOS:

```bash
python3 -m venv .venv

source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment

Create `.env` or configure the required environment variables.

Example:

```env
AUTH_KEY=your_api_key
```

Не добавляйте `.env` в Git repository.

## 5. Run

```bash
python start.py
```

---

# 💬 Example

```text
>>> Привет

Здравствуйте! Чем могу помочь?

>>> Хочу заказать пиццу

Доступные пиццы:
- Пепперони
- Четыре сыра
- Карбонара
- Песта
- Маргарита

>>> Песта 1 шт

Пожалуйста, укажите адрес доставки.

>>> Москва, Ленина 10

Стоимость заказа: 800 ₽.

Подтвердить заказ? [да/нет]

>>> да

Заказ успешно сохранён.
```

---

# 🎯 Engineering Goals

Главная цель проекта — продемонстрировать не только работу LLM, но и полный lifecycle AI Agent:

```text
Natural Language
       ↓
Intent understanding
       ↓
Tool selection
       ↓
Structured arguments
       ↓
Validation
       ↓
Business logic
       ↓
Human approval
       ↓
Database operation
       ↓
Persistent state
```

В отличие от простого LLM chatbot, проект разделяет ответственность между моделью и application layer.

---

# 🔮 Planned Improvements

Следующие направления развития проекта:

- [ ] FastAPI REST API
- [ ] PostgreSQL вместо SQLite для production deployment
- [ ] Docker / Docker Compose
- [ ] GitHub Actions CI
- [ ] Ruff + strict type checking
- [ ] Structured logging
- [ ] LangSmith / OpenTelemetry tracing
- [ ] Agent evaluation
- [ ] RAG evaluation
- [ ] Retrieval reranking
- [ ] Prompt injection protection
- [ ] Retry / error recovery strategy
- [ ] Token and cost monitoring
- [ ] MCP integration
- [ ] Integration with external enterprise systems such as 1C

---

# 📈 Why this project?

Проект создан как практическое исследование архитектуры современных AI Agent систем.

Основной фокус:

**LLM + Agents + Tools + Memory + RAG + Human-in-the-Loop + Backend Architecture**

Проект демонстрирует подход, при котором LLM является частью software system, а не всей системой целиком.

---

## 👨‍💻 Author

**Alexey Fedorov**

GitHub:  
https://github.com/AlekseyFedorov27

---

## 📄 License

This project is intended for educational and portfolio purposes.