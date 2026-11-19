# Tank Safety Platform — backend integration

Прототип системы «Tank Safety Platform» (ООО «АралИнжиниринг», команда 13, KAIZEN.AI):
Backend:

- Python 3.11+
- FastAPI + Pydantic v2
- SQLite (стандартный модуль `sqlite3`, без ORM)
- JWT (PyJWT), пароли — PBKDF2-HMAC-SHA256 (стандартная библиотека)
- pytest + httpx / httpx2 (тесты; `httpx2` используется новым `starlette.testclient`)

Frontend:

- React 19 + TypeScript
- Vite
- Chart.js + react-chartjs-2

## Быстрый старт

### 1. Клонировать репозиторий

```powershell
git clone -b feature/backend-integration-for-prototype https://github.com/safonovartem/Team_13_Our_work.git
```

### 2. Запустить бэкенд

#### 2.1. Создать виртуальное окружение

```powershell
python -m venv .venv
```

#### 2.2. Запустить 

```powershell
cd backend
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### 2. Запустить фронтенд

```powershell
cd frontend
npm install
npm run dev
```
