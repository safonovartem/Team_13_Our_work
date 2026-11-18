# Tank Safety Platform — backend

Прототип системы «Tank Safety Platform» (ООО «АралИнжиниринг», команда 13, KAIZEN.AI):
Backend:

- API на FastAPI, валидация пользователей и исходных данных, SQLite, тесты на pytest.
- API на FastAPI, валидация пользователей и исходных данных, SQLite, расчёты и графики, тесты на pytest.

Frontend:

- React 19 + TypeScript
- Vite
- Chart.js + react-chartjs-2

## Быстрый старт

### 1. Запустить бэкенд

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
