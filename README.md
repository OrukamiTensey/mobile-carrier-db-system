# Mobile Operator Management System (Polyglot Persistence)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0+-008CC1.svg?logo=neo4j&logoColor=white)](https://neo4j.com/)
[![CouchDB](https://img.shields.io/badge/CouchDB-3.0+-E0234E.svg?logo=apachecouchdb&logoColor=white)](https://couchdb.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)

Повнофункціональна веб-система для автоматизації обліку абонентів, контролю платежів, аналізу мережевих зв'язків та обробки сервісних заявок мобільного оператора. 

Головна архітектурна особливість проєкту — застосування **Polyglot Persistence** (полімодельного підходу до зберігання даних), де кожна із трьох баз даних відповідає за свій тип бізнес-сутностей.

---

## Архітектура та Полімодельне зберігання (Polyglot Persistence)

Замість спроби вмістити всі різнотипні дані в одну БД, система розподіляє навантаження між трьома СУБД:

| СУБД | Тип БД | Призначення в системі |
| :--- | :--- | :--- |
| **PostgreSQL** | Реляційна | Зберігання критично важливих структурованих даних: абоненти, контракти, історія платежів. Забезпечує ACID-транзакційність. |
| **Neo4j** | Графова | Моделювання та аналіз мережевих зв'язків між абонентами та їх тарифними планами через мову запитів Cypher. |
| **CouchDB** | Документна | Обробка та зберігання сервісних заявок на обслуговування (JSON-документи). Забезпечує гнучкість схеми без жорсткої прив'язки. |

---

## Основні можливості

* **Облік абонентів та контрактів:** Повний CRUD-інтерфейс для керування персональними даними, RIC-номерами, моделями пристроїв та видами обслуговування.
* **Автоматичний аналіз заборгованостей:** Фіксація прострочених платежів, розрахунок днів затримки та автоматичне прогнозування дати відключення послуг.
* **Сервісні заявки (NoSQL):** Створення та трекінг статусу заявок (ремонт, заміна, підключення/відключення) у CouchDB.
* **Аналітика зв'язків (Graph DB):** Візуалізація та аналіз графів мережі абонентів та тарифних планів у Neo4j.
* **Інтерактивна API Документація:** Автоматична генерація Swagger/OpenAPI специфікації завдяки FastAPI.

---

## Стек технологій

* **Backend:** Python, FastAPI, SQLAlchemy (Async), Psycopg3, Pydantic, Uvicorn.
* **Databases:** PostgreSQL, Neo4j, CouchDB.
* **Frontend:** HTML5, CSS3, JS (Fetch API, Bootstrap/Custom Dark UI, FontAwesome).
* **DevOps & Infrastructure:** Docker, Docker Compose, Health-checks.

---

## Структура проєкту

```text
CW_MobileOperator/
├── app/
│   ├── database/        # Модулі підключення до PostgreSQL, Neo4j, CouchDB
│   ├── models/          # SQLAlchemy та Pydantic схеми
│   ├── routes/          # REST API ендпоінти
│   ├── services/        # Бізнес-логіка та сервісні класи
│   ├── config.py        # Конфігурація середовища
│   └── main.py          # Точка входу FastAPI
├── frontend/            # Веб-інтерфейс (HTML/CSS/JS)
├── init_scripts/        # Скрипти ініціалізації баз даних
├── docker-compose.yml   # Оркестрація всіх 4 контейнерів
├── Dockerfile           # Збірка FastAPI додатка
└── requirements.txt     # Залежності Python
