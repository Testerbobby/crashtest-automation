# Test Design & Checklist: User & Authentication

Спецификация: `user-and-authentication.yml`  
Эндпоинты: `/api/users`, `/api/users/login`, `/api/user`

---

## 1. Smoke Tests (Позитивные критические пути)

| ID | Сценарий | Предусловия | Шаги / Тестовые данные | Ожидаемый результат | Приоритет |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-SMK-01** | Успешная регистрация нового пользователя | Пользователь с таким email/username не существует | `POST /api/users`<br>`{"user": {"username": "john_doe", "email": "john.doe@example.com", "password": "SecretPassword123!"}}` | `201 Created`. Возвращается объект `user`: корректные `email`, `username`, непустой JWT `token`, поля `bio` и `image` (null или пустые строки) | **Blocker** |
| **TC-SMK-02** | Успешный логин существующего пользователя | Пользователь зарегистрирован (TC-SMK-01) | `POST /api/users/login`<br>`{"user": {"email": "john.doe@example.com", "password": "SecretPassword123!"}}` | `200 OK`. Возвращается объект `user` с валидным JWT-токеном и актуальными данными профиля | **Blocker** |
| **TC-SMK-03** | Получение профиля текущего пользователя | Пользователь залогинен, получен `token` | `GET /api/user`<br>Header: `Authorization: Token <valid_jwt>` | `200 OK`. Возвращается объект `user` текущего авторизованного пользователя | **Critical** |
| **TC-SMK-04** | Обновление данных текущего пользователя | Пользователь залогинен | `PUT /api/user`<br>Header: `Authorization: Token <valid_jwt>`<br>`{"user": {"bio": "Mobile QA Engineer", "image": "https://i.imgur.com/Qr71crq.jpg"}}` | `200 OK`. Поля `bio` и `image` успешно обновлены и возвращаются в теле ответа | **Critical** |

---

## 2. Boundary & Negative Tests (Валидация и граничные значения)

| ID | Сценарий | Шаги / Payload | Ожидаемый результат | Приоритет |
| :--- | :--- | :--- | :--- | :--- |
| **TC-NEG-01** | Регистрация с уже занятым email | `POST /api/users` с email существующего юзера | `422 Unprocessable Entity`. В теле: `{"errors": {"email": ["has already been taken"]}}` | **Critical** |
| **TC-NEG-02** | Регистрация с уже занятым username | `POST /api/users` с username существующего юзера | `422 Unprocessable Entity`. В теле: `{"errors": {"username": ["has already been taken"]}}` | **Critical** |
| **TC-NEG-03** | Невалидный формат email | `POST /api/users` с email `"plainaddress"`, `"@missingusername.com"` | `422 Unprocessable Entity`. Сообщение об ошибке формата email | **Major** |
| **TC-NEG-04** | Пустые обязательные поля при регистрации | `POST /api/users`<br>`{"user": {"username": "", "email": "", "password": ""}}` | `422 Unprocessable Entity`. Ошибки валидации: поля не могут быть пустыми (`can't be blank`) | **Critical** |
| **TC-NEG-05** | Спецсимволы и пробелы в username | `POST /api/users` с username `"user name"`, `"user/slug"`, `"😎"` | `422 Unprocessable Entity` (проверка защиты роутинга профилей `/profiles/{username}`) | **Major** |
| **TC-NEG-06** | Логин с неверным паролем | `POST /api/users/login` с валидным email и неверным паролем | `422 Unprocessable Entity` (или `401 Unauthorized`). Ошибка авторизации | **Critical** |
| **TC-NEG-07** | Логин несуществующего пользователя | `POST /api/users/login` с несуществующим email | `422 Unprocessable Entity` (или `404/401`) | **Major** |
| **TC-NEG-08** | Запрос к защищенному эндпоинту без токена | `GET /api/user` без заголовка `Authorization` | `401 Unauthorized` | **Critical** |
| **TC-NEG-09** | Запрос с невалидным или протухшим токеном | `GET /api/user` с заголовком `Authorization: Token invalid.token.payload` | `401 Unauthorized` | **Critical** |

---

## 3. Android & Contract Edge Cases (Специфика мобильного клиента)

| ID | Сценарий проверки | Воздействие / Запрос | Ожидаемый результат для клиента |
| :--- | :--- | :--- | :--- |
| **TC-MOB-01** | **Null-safety полей bio и image** | Сразу после регистрации дергаем `GET /api/user`. Проверяем формат полей `bio` и `image` (бэк отдает `null` или `""`) | Android-клиент не крашится с `NullPointerException` / `JsonDataException` при парсинге через Kotlinx.Serialization / Moshi / Gson |
| **TC-MOB-02** | **Формат заголовка авторизации (Token vs Bearer)** | Отправка `Authorization: Bearer <jwt>` вместо `Token <jwt>` на `GET /api/user` | Проверка поведения бэкенда: возвращает `401` или поддерживает стандартный `Bearer` |
| **TC-MOB-03** | **Парсинг схемы ошибок 422** | Провоцируем ошибку валидации и проверяем структуру: `{"errors": {"body": [...]}}` | Формат строго соответствует `GenericErrorModel`, мобильный UI отображает ошибку пользователю, а не уходит в бесконечный лоадер |
| **TC-MOB-04** | **Слишком длинный bio (UI Overflow)** | `PUT /api/user` с текстом bio > 5000 символов | Бэкенд валидирует лимит длины либо возвращает 422; клиент не падает при отрисовке экрана профиля |