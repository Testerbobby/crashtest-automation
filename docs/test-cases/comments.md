# Test Design & Checklist: Comments Module

Спецификация: `comments.yml`  
Эндпоинты: `/api/articles/{slug}/comments`, `/api/articles/{slug}/comments/{id}`

---

## 1. Smoke Tests (Позитивные критические пути)

| ID | Сценарий | Предусловия | Шаги / Тестовые данные | Ожидаемый результат | Приоритет |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-COMM-SMK-01** | Создание комментария к статье | Пользователь авторизован, статья существует | `POST /api/articles/how-to-train-your-dragon/comments`<br>Header: `Authorization: Token <jwt>`<br>`{"comment": {"body": "This is a wonderful article!"}}` | `200 OK` (или `201`). Возвращает объект `comment` с уникальным `id`, `body`, `createdAt` и объектом автора. | **Blocker** |
| **TC-COMM-SMK-02** | Получение списка комментариев к статье | Статья существует, есть комментарии | `GET /api/articles/how-to-train-your-dragon/comments` (без авторизации) | `200 OK`. Возвращает массив `comments` со всеми комментариями к статье. | **Critical** |
| **TC-COMM-SMK-03** | Удаление своего комментария автором | Пользователь авторизован, является автором комментария | `DELETE /api/articles/how-to-train-your-dragon/comments/123`<br>Header: `Authorization: Token <jwt>` | `200 OK` (EmptyOkResponse). Комментарий успешно удален. | **Critical** |

---

## 2. Negative & Security Tests (Ошибки и безопасность)

| ID | Сценарий | Шаги / Payload | Ожидаемый результат | Приоритет |
| :--- | :--- | :--- | :--- | :--- |
| **TC-COMM-NEG-01** | Удаление чужого комментария другим пользователем | `DELETE /api/articles/slug/comments/123` с токеном другого юзера (не автора комментария) | `403 Forbidden` / `401 Unauthorized` / `422`. Комментарий не удален. | **Critical** |
| **TC-COMM-NEG-02** | Создание комментария без авторизации (нет токена) | `POST /api/articles/slug/comments` без заголовка `Authorization` | `401 Unauthorized`. | **Critical** |
| **TC-COMM-NEG-03** | Создание комментария с пустым телом body | `POST /api/articles/slug/comments`<br>`{"comment": {"body": ""}}` | `422 Unprocessable Entity`. Ошибка валидации (`can't be blank`). | **Major** |
| **TC-COMM-NEG-04** | Комментирование несуществующей статьи | `POST /api/articles/non-existent-slug-xyz/comments` | `404 Not Found` (или `422`). | **Major** |
| **TC-COMM-NEG-05** | Удаление несуществующего комментария | `DELETE /api/articles/slug/comments/999999` с валидным токеном | `404 Not Found` (или `422`). | **Major** |

---

## 3. Mobile & Contract Edge Cases (Специфика мобильного клиента)

| ID | Сценарий проверки | Воздействие / Запрос | Ожидаемый результат для клиента |
| :--- | :--- | :--- | :--- |
| **TC-COMM-MOB-01** | **Формат пустого массива comments: []** | Запрос списка комментариев для статьи без комментариев `GET /api/articles/slug/comments` | Клиент получает корректный JSON `{ "comments": [] }` и отображает пустой state вместо падения десериализации. |
| **TC-COMM-MOB-02** | **Null-safety для профиля автора комментария** | Получение комментария, у которого поля автора (`bio`, `image`) равны `null` | Мобильное приложение корректно парсит объект `Author` без `NullPointerException`. |
| **TC-COMM-MOB-03** | **Спецсимволы, эмодзи и переносы строк в комментарии** | Отправка комментария с многострочным текстом, HTML-тегами и эмодзи: `🔥 Line 1\nLine 2` | Сервер сохраняет текст, а клиент корректно рендерит многострочный комментарий и эмодзи без искажения кодировки (UTF-8). |
| **TC-COMM-MOB-04** | **Оптимистичное обновление UI (Optimistic Update)** | Добавление комментария пользователем в офлайн/медленной сети | UI мгновенно добавляет комментарий в список с временным статусом/ID, а при подтверждении ответа сервера синхронизирует реальный `id`. |
