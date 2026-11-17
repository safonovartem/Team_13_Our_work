# Tank Safety Platform — backend

Бэкенд системы «Tank Safety Platform» (ООО «АралИнжиниринг», команда 13):
API на FastAPI, валидация пользователей и исходных данных, SQLite, расчёты
и графики, тесты на pytest.

> **Совместимость.** Вычислительное ядро взято из ветки
> `feature/backend-calculations` (`app/core/`, код не переписан, а перенесён
> без изменений). Форматы ответов расчётов и графиков соответствуют типам
> ветки `feature/main-page`: `CalculationResult = { variants, charts }`,
> `ChartBlock = { title, datasets }`, `ChartDataset = { label, data: [[x, y], ...] }`.
> Подробности — в разделе [«Совместимость с ветками команды»](#совместимость-с-ветками-команды).

## Стек

- Python 3.11+
- FastAPI + Pydantic v2
- SQLite (стандартный модуль `sqlite3`, без ORM)
- JWT (PyJWT), пароли — PBKDF2-HMAC-SHA256 (стандартная библиотека)
- pytest + httpx / httpx2 (тесты; `httpx2` используется новым `starlette.testclient`)

## Структура проекта

```
app/
├── config.py            # настройки из переменных окружения
├── database.py          # подключение к SQLite и DDL-схема
├── factory.py           # сборка FastAPI-приложения
├── main.py              # точка входа: uvicorn app.main:app
├── deps.py              # зависимости: БД, текущий пользователь, права
├── errors.py            # доменные ошибки (404/409/400)
├── security.py          # хеширование паролей и JWT
├── validators.py        # правила валидации email/username/пароля
├── core/                # вычислительное ядро из feature/backend-calculations
│   ├── engine.py        # фасад run_engine (единственная точка входа)
│   ├── catalog.py       # типоразмеры РВС по ГОСТ
│   ├── contracts.py     # InputData / ResultData / WallResult / WaveData
│   └── barriers/        # стратегии PlainWall и GWKWall
├── schemas/             # Pydantic-схемы запросов и ответов
│   ├── auth.py
│   ├── users.py
│   ├── inputs.py        # исходные данные (объект, жидкость, среда)
│   ├── projects.py
│   ├── calculations.py  # параметры ядра, блоки интерфейса, графики
│   ├── catalog.py
│   └── common.py
├── repositories/        # SQL-запросы (пользователи, проекты, расчёты)
├── services/            # адаптация ядра, графики, проверка доступа
├── routers/             # HTTP-эндпоинты
└── ...
tests/                   # pytest: auth, пользователи, проекты, расчёты, графики, БД
```

## Быстрый старт

```powershell
# из корня проекта
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt

# запуск API
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- Health-check: `GET /health`

База данных создаётся автоматически при первом запуске
(`data/tank_safety.db`, путь настраивается).

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `TSP_DATABASE_PATH` | `data/tank_safety.db` | путь к файлу SQLite |
| `TSP_SECRET_KEY` | dev-значение | ключ подписи JWT — **обязательно задать в production** (≥ 32 байт) |
| `TSP_ACCESS_TOKEN_TTL_MINUTES` | `720` | время жизни access-токена, минуты |
| `TSP_JWT_ALGORITHM` | `HS256` | алгоритм подписи JWT |
| `TSP_CORS_ORIGINS` | localhost:5173/3000 | разрешённые Origin через запятую |
| `TSP_ADMIN_EMAIL` | — | email администратора, создаётся при старте |
| `TSP_ADMIN_PASSWORD` | — | пароль администратора (вместе с email) |

Пример: `.env.example`.

## Модель данных

```
users               пользователи (роли user/admin, флаг активности)
  └─ projects       проекты пользователя (название, статус, текущие данные)
       ├─ project_versions   история версий исходных данных (JSON-снимки)
       └─ calculations       история расчётов (параметры, результат, графики)
```

- Email и username уникальны **без учёта регистра** (`COLLATE NOCASE`).
- Удаление пользователя каскадно удаляет его проекты, удаление проекта —
  его версии и расчёты (`ON DELETE CASCADE`).
- Расчёт сохраняется отдельно от версии исходных данных: одинаковые данные
  можно считать с разными значениями `l`, `b` и сценариями.
- Пользователь не удаляется физически: `DELETE /api/users/{id}` деактивирует
  его, чтобы сохранить историю проектов.
- Исходные данные хранятся как JSON и всегда проходят Pydantic-валидацию
  перед записью.

## API

Базовый префикс — `/api`. Авторизация (`Authorization: Bearer <token>`)
требуется для всех эндпоинтов пользователей, проектов и истории расчётов.
Публичные (без токена): `/auth/register`, `/auth/login`, `/health`,
`/api/calculations`, `/api/charts`, `/api/catalog`.

### Аутентификация

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/auth/register` | создать пользователя (роль `user`) |
| `POST` | `/api/auth/login` | вход по email или username, возвращает JWT |
| `GET` | `/api/auth/me` | текущий пользователь |

### Пользователи

| Метод | Путь | Доступ | Описание |
|---|---|---|---|
| `GET` | `/api/users/me` | пользователь | профиль |
| `PATCH` | `/api/users/me` | пользователь | изменить email/username/ФИО/организацию/пароль |
| `GET` | `/api/users` | администратор | список с пагинацией |
| `GET` | `/api/users/{id}` | администратор | пользователь по id |
| `PATCH` | `/api/users/{id}` | администратор | роль, активность, данные, сброс пароля |
| `DELETE` | `/api/users/{id}` | администратор | деактивировать |

### Проекты и история

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/projects` | создать проект (опционально с исходными данными) |
| `GET` | `/api/projects` | история проектов пользователя: пагинация, `status`, `search` |
| `GET` | `/api/projects/{id}` | проект с актуальными исходными данными |
| `PATCH` | `/api/projects/{id}` | изменить метаданные и/или сохранить новую версию данных |
| `DELETE` | `/api/projects/{id}` | удалить проект вместе с историей |
| `GET` | `/api/projects/{id}/history` | версии исходных данных (новые сверху) |
| `GET` | `/api/projects/{id}/history/{version}` | конкретная версия |
| `POST` | `/api/projects/{id}/history` | сохранить снимок (текущий или переданный) |
| `POST` | `/api/projects/{id}/history/{version}/restore` | восстановить версию (создаёт новую) |

Проекты других пользователей недоступны и возвращают `404`, чтобы не
раскрывать их существование.

### Расчёты (вычислительное ядро)

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/calculations` | расчёт по параметрам ядра (объём РВС, `l`, `b`, сценарии) |
| `POST` | `/api/calculations/from-form` | расчёт по `FormValues` главной страницы (camelCase) |
| `GET` | `/api/catalog` | типоразмеры РВС и границы применимости формул |

Входные параметры:

| Поле | По умолчанию | Описание |
|---|---|---|
| `tank_volume` | — | объём РВС по каталогу: 700 / 2000 / 5000 / 10000 / 20000 / 30000 м³ |
| `clearance_l` | `3.0` | межстенное расстояние, м (1.5…3.0) |
| `crest_width_b` | `1.0` | вылет козырька, м (0.5…1.5) |
| `plain_wall_height` | `null` | высота стенки без козырька, м; `null` → 1.1·h0 |
| `scenarios` | `["plain", "gwk"]` | сценарии: без козырька / с ГВК |

Ответ `CalculationResponse`:

```json
{
  "input": {"tank_volume": 5000, "clearance_l": 3.0, "crest_width_b": 1.0},
  "result": {"tank_volume": 5000, "tank_diameter_m": 20.92, "variants": [], "wave": {}},
  "variants": [
    {
      "id": "no-canopy",
      "title": "Без козырька",
      "scenario": "plain",
      "isImportant": false,
      "items": [{"title": "Доля перелива", "value": "0 %"}]
    }
  ],
  "charts": [{"title": "...", "datasets": [{"label": "l = 3.0 м", "data": [[0.7, 10.03]]}]}],
  "recommended_variant": "gwk"
}
```

`variants` и `charts` можно передавать фронтенду как `CalculationResult` без
преобразований: лишние поля (`input`, `result`, `scenario`, оси графика)
игнорируются типами TypeScript.

В `/api/calculations/from-form` объём РВС извлекается из `objectType`
(«РВС-5000 · 5 000 м³») или из `objectVolume`; отсутствующие `clearanceL` и
`crestWidthB` принимают значения по умолчанию.

### Графики

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/charts/overflow` | `Q(h_зс/h0)` — по одной кривой на каждый `l` |
| `POST` | `/api/charts/wave` | траектория фронта волны и высота потока |
| `POST` | `/api/charts` | перелив + траектория волны одним набором |

Пример запроса и ответа:

```json
POST /api/charts/overflow
{"tank_volume": 5000, "clearance_values": [3.0], "height_ratios": [0.7, 0.97, 1.1]}
```

```json
{
  "title": "Доля перелива от высоты стенки",
  "datasets": [
    {"label": "l = 3.0 м", "data": [[0.7, 10.03], [0.97, 0.0], [1.1, 0.0]]}
  ]
}
```

Значения рассчитаны по формуле (4.1) Швыркова с коэффициентами из
`app/core/constants.py` — теми же, что использует стратегия `PlainWall`.

### История расчётов проекта

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/projects/{id}/calculations` | выполнить и сохранить расчёт |
| `POST` | `/api/projects/{id}/calculations/from-form` | расчёт по форме и сохранение |
| `GET` | `/api/projects/{id}/calculations` | список с пагинацией |
| `GET` | `/api/projects/{id}/calculations/{calc_id}` | сохранённый расчёт |
| `GET` | `/api/projects/{id}/calculations/{calc_id}/charts` | его графики |
| `DELETE` | `/api/projects/{id}/calculations/{calc_id}` | удалить расчёт |

Доступ — только владельцу проекта; чужие проекты и расчёты возвращают `404`.

### Формат ошибок

- `422` — ошибка валидации Pydantic (`detail` — список с путём до поля) или
  выход параметра за границы применимости формул (`code: "domain_range_error"`);
- `400` — бизнес-правило (например, неверный текущий пароль);
- `401` — нет/просрочен токен или неверные учётные данные;
- `403` — нет прав или учётная запись деактивирована;
- `404` — объект не найден;
- `409` — конфликт уникальности (`field` указывает поле).

```json
{"detail": "Пользователь с таким email уже зарегистрирован", "code": "conflict", "field": "email"}
```

## Валидация

### Пользователь

- **email** — синтаксис RFC-подобный, нормализуется к нижнему регистру,
  уникален без учёта регистра;
- **username** — 3–32 символа, латиница/цифры/`.`/`-`/`_`,
  начинается и заканчивается буквой или цифрой, уникален без учёта регистра;
- **пароль** — 8–128 символов, минимум одна буква и одна цифра, не входит в
  список частых паролей, не содержит username или локальную часть email;
- роль и `is_active` при самостоятельной регистрации недоступны (лишние поля
  отклоняются с `422`) — их меняет только администратор;
- смена пароля требует `current_password`;
- деактивированный пользователь не может войти, а его токен отклоняется.

### Исходные данные проекта

Для каждого параметра заданы тип, единица измерения, диапазон и обязательность
(раздел 4.2 ТЗ). Проверяются заполнение обязательных полей, типы, диапазоны,
отсутствие недопустимых отрицательных значений и логическая совместимость
(раздел 5 ТЗ).

**Объект (`object`)**

| Поле | Единица | Правило |
|---|---|---|
| `name` | — | обязательно, 1–120 символов |
| `object_type` | — | `vertical_cylinder`, `horizontal_cylinder`, `rectangular` |
| `material` | — | обязательно, 1–120 символов |
| `wall_thickness_mm` | мм | обязательно, `> 0`, `≤ 500` |
| `height_m` | м | обязательно, `> 0`, `≤ 200` |
| `diameter_m` | м | обязательно для цилиндров, `> 0` |
| `length_m`, `width_m` | м | обязательны для прямоугольного объекта, `> 0` |
| `volume_m3` | м³ | необязательно, `> 0` |

**Жидкость (`liquid`)**

| Поле | Единица | Правило |
|---|---|---|
| `liquid_type` | — | `water`, `oil`, `petroleum`, `diesel`, `gasoline`, `acid`, `alkali`, `other` |
| `density_kg_m3` | кг/м³ | 500–2000 |
| `viscosity_cst` | сСт | 0–1 000 000 |
| `temperature_c` | °C | −60…200 |
| `fill_level_percent` | % | 0–100 |
| `volume_m3` | м³ | необязательно, `≥ 0` |

**Окружающая среда (`environment`)**

| Поле | Единица | Правило |
|---|---|---|
| `ambient_temperature_c` | °C | −60…60 |
| `terrain_type` | — | `flat`, `slope`, `rough`, `urban`, `industrial` |
| `surface_type` | — | `asphalt`, `concrete`, `soil`, `sand`, `grass`, `water` |
| `slope_degrees` | ° | 0–90; для `flat` — не более 5 |
| `has_obstacles` | — | `bool` |
| `obstacles_description` | — | ≤ 500 символов, только при `has_obstacles=true` |
| `containment` | — | `bool`, наличие обвалования |
| `additional_params` | — | словарь (≤ 20 пар, значения — строка/число/`bool`) |

**Логическая совместимость**

- объём жидкости не может превышать объём объекта;
- при нулевом уровне заполнения объём жидкости должен быть равен 0;
- если заданы и объём объекта, и уровень заполнения, и объём жидкости, они
  должны быть согласованы (допуск 15 %);
- для ровной территории уклон ≤ 5°;
- описание препятствий допустимо только при `has_obstacles=true`;
- лишние/неизвестные поля запрещены (`extra="forbid"`) — это защищает от
  опечаток в названиях параметров.

## Примеры запросов

```powershell
# 1. Регистрация
curl -X POST http://127.0.0.1:8000/api/auth/register `
  -H "Content-Type: application/json" `
  -d '{"email":"engineer@example.com","username":"engineer","password":"Tank12345","full_name":"Иван Петров"}'

# 2. Вход (получите access_token)
curl -X POST http://127.0.0.1:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{"login":"engineer@example.com","password":"Tank12345"}'

# 3. Создание проекта с исходными данными
curl -X POST http://127.0.0.1:8000/api/projects `
  -H "Content-Type: application/json" -H "Authorization: Bearer <TOKEN>" `
  -d '{"name":"Резервуарный парк №1","input_data":{"schema_version":1,
       "object":{"name":"РВС-1000","object_type":"vertical_cylinder","material":"Сталь 09Г2С",
                 "wall_thickness_mm":8,"height_m":12,"diameter_m":10.4,"volume_m3":1000},
       "liquid":{"liquid_type":"oil","density_kg_m3":870,"viscosity_cst":25,
                 "temperature_c":20,"fill_level_percent":50,"volume_m3":500},
       "environment":{"ambient_temperature_c":15,"terrain_type":"flat",
                      "surface_type":"soil","slope_degrees":0,"containment":true}}}'

# 4. История версий проекта
curl http://127.0.0.1:8000/api/projects/1/history -H "Authorization: Bearer <TOKEN>"

# 5. Расчёт (без авторизации)
curl -X POST http://127.0.0.1:8000/api/calculations `
  -H "Content-Type: application/json" `
  -d '{"tank_volume":5000,"clearance_l":3.0,"crest_width_b":1.0}'

# 6. График перелива с нужными точками
curl -X POST http://127.0.0.1:8000/api/charts/overflow `
  -H "Content-Type: application/json" `
  -d '{"tank_volume":5000,"clearance_values":[3.0],"height_ratios":[0.7,0.97,1.1]}'

# 7. Расчёт по форме главной страницы
curl -X POST http://127.0.0.1:8000/api/calculations/from-form `
  -H "Content-Type: application/json" `
  -d '{"objectType":"РВС-5000 · 5 000 м³","fillLevel":100}'
```

## Тесты

```powershell
.venv\Scripts\python.exe -m pytest
```

Если при запуске появляется `StarletteDeprecationWarning: Using httpx with
starlette.testclient is deprecated`, доустановите `httpx2` (уже есть в
`requirements-dev.txt`):

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Покрыто: регистрация и вход, валидация пользователя, уникальность email и
username, JWT (в том числе просроченный и подписанный чужим ключом), роли и
деактивация, CRUD проектов, изоляция проектов разных пользователей, история
версий, восстановление версии, каскадное удаление, диапазоны и логические
проверки исходных данных, расчёты и точные значения кривой перелива, адаптер
формы главной страницы, все эндпоинты графиков, справочник, сохранение и
изоляция истории расчётов.

Тесты самого вычислительного ядра (ветка `feature/backend-calculations`)
запускаются отдельно и тоже проходят: 578 тестов.

## Совместимость с ветками команды

### `feature/backend-calculations`

- Код ядра перенесён в `app/core/` **без изменений**: `run_engine(InputData)`
  остаётся единственной точкой входа, все формулы и константы находятся в
  `app/core/constants.py`.
- API не дублирует расчётную логику: `app/services/calculations.py` только
  преобразует Pydantic-схемы в `InputData` и сериализует `ResultData`.
- Ошибки ядра `DomainRangeError` прозрачно преобразуются в HTTP `422` с
  `code: "domain_range_error"` и понятным русским сообщением.
- Исходные данные проекта (`app/schemas/inputs.py`) остаются отдельным
  контрактом: это данные ТЗ (объект, жидкость, среда), а не параметры ядра
  (`tank_volume`, `clearance_l`, `crest_width_b`).

### `feature/main-page`

- `variants` — это `ResultBlock[]`: `id`, `title`, `isImportant`, `items`
  (`ResultItem[]`: `title`, `value`). Рекомендуемый ядром вариант отмечен
  `isImportant: true` (как «Рекомендуемый» в интерфейсе).
- `charts` — это `ChartBlock[]`: `title` и `datasets` из `ChartDataset`, где
  каждая точка — массив `[x, y]` чисел, как ожидает `chart.js`.
- Адаптер `/api/calculations/from-form` принимает поля `FormValues` в
  camelCase (`objectType`, `objectVolume`, `fillLevel` и т.д.), поэтому
  фронтенд может заменить вызов `calculate()` из `mock-api.ts` на запрос
  к API без изменения типов.

Дополнительные поля ответа (`input`, `result`, `scenario`, `xAxis`, `yAxis`)
не конфликтуют с интерфейсными типами — TypeScript их просто проигнорирует.
```
