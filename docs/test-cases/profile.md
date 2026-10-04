# Test Design & Checklist: Profile Module

Спецификация: `profile.yml`  
Эндпоинты: `/api/profiles/{username}`, `/api/profiles/{username}/follow`

---

## 1. Smoke Tests (Позитивные критические пути)

| ID | Сценарий | Предусловия | Шаги / Тестовые данные | Ожидаемый результат | Приоритет |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-PROF-SMK-01** | Получение публичного профиля пользователя (анонимно) | Пользователь `john_doe` зарегистрирован | `GET /api/profiles/john_doe` (без авторизации) | `200 OK`. Возвращает объект `profile` с полями: `username`, `bio`, `image`, `following: false`. | **Critical** |
| **TC-PROF-SMK-02** | Подписка на пользователя | Пользователь А авторизован, Пользователь Б существует | `POST /api/profiles/john_doe/follow`<br>Header: `Authorization: Token <jwt_token>` | `200 OK`. Возвращает профиль пользователя с `following: true`. | **Blocker** |
| **TC-PROF-SMK-03** | Отписка от пользователя | Пользователь А авторизован, подписан на Пользователя Б | `DELETE /api/profiles/john_doe/follow`<br>Header: `Authorization: Token <jwt_token>` | `200 OK`. Возвращает профиль пользователя с `following: false`. | **Critical** |

---

## 2. Boundary & Negative Tests (Валидация и ошибки)

| ID | Сценарий | Шаги / Payload | Ожидаемый результат | Приоритет |
| :--- | :--- | :--- | :--- | :--- |
| **TC-PROF-NEG-01** | Запрос профиля несуществующего пользователя | `GET /api/profiles/non_existent_user_9999` | `404 Not Found` (или `422`). Возвращает объект ошибки. | **Major** |
| **TC-PROF-NEG-02** | Подписка без авторизации (нет токена) | `POST /api/profiles/john_doe/follow` без заголовка `Authorization` | `401 Unauthorized`. | **Critical** |
| **TC-PROF-NEG-03** | Подписка с невалидным/просроченным токеном | `POST /api/profiles/john_doe/follow` с невалидным `Token` | `401 Unauthorized`. | **Critical** |
| **TC-PROF-NEG-04** | Самоподписка (пользователь подписывается сам на себя) | `POST /api/profiles/my_username/follow` с собственным токеном | `422 Unprocessable Entity` (или бизнес-ошибка). | **Minor** |
| **TC-PROF-NEG-05** | Некорректные спецсимволы/путь в username | `GET /api/profiles/user/with/slashes` или пустой username `GET /api/profiles/` | `404 Not Found` / `400 Bad Request`. | **Minor** |

---

## 3. Android & Contract Edge Cases (Специфика мобильного клиента)

| ID | Сценарий проверки | Воздействие / Запрос | Ожидаемый результат для клиента |
| :--- | :--- | :--- | :--- |
| **TC-PROF-MOB-01** | **Null-safety для флага following и bio/image** | Получение профиля пользователя, у которого `bio` или `image` равны `null` | Мобильное приложение корректно десериализует Boolean (`following`) и Strings (`bio`, `image`) без крэшей от `NullPointerException`. |
| **TC-PROF-MOB-02** | **Идемпотентность повторной подписки** | Вызов `POST /api/profiles/john_doe/follow` два раза подряд для уже подписанного юзера | Сервер и клиент корректно обрабатывают ответ `200 OK` с `following: true` без дублирования состояния в UI. |
| **TC-PROF-MOB-03** | **Идемпотентность повторной отписки** | Вызов `DELETE /api/profiles/john_doe/follow` два раза подряд для отписанного юзера | Корректный ответ `200 OK` с `following: false`. |
| **TC-PROF-MOB-04** | **Обработка сетевого таймаута при клике на кнопку Follow** | Медленное соединение (2G/3G) при отправке запроса `POST /.../follow` | Кнопка Follow переходит в состояние загрузки (spinner), предотвращая повторные тапы (debouncing), при ответе UI обновляется. |
