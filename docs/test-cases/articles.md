# Test Design & Checklist: Articles Module

Спецификация: `articles.yml`  
Эндпоинты: `/api/articles`, `/api/articles/feed`, `/api/articles/{slug}`

---

## 1. Smoke Tests (Позитивные критические пути)

| ID | Сценарий | Предусловия | Шаги / Тестовые данные | Ожидаемый результат | Приоритет |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-ART-SMK-01** | Создание новой статьи | Пользователь авторизован | `POST /api/articles`<br>Header: `Authorization: Token <jwt>`<br>`{"article": {"title": "How to train your dragon", "description": "Ever wonder how?", "body": "It takes a lot of time.", "tagList": ["reactjs", "angularjs"]}}` | `201 Created`. Возвращает объект `article` с уникальным `slug`, `title`, `description`, `body`, `tagList` и данными автора. | **Blocker** |
| **TC-ART-SMK-02** | Получение статьи по slug | Статья с таким slug существует | `GET /api/articles/how-to-train-your-dragon` (без авторизации) | `200 OK`. Возвращает точную статью. | **Critical** |
| **TC-ART-SMK-03** | Получение глобальной ленты статей | Статьи существуют в системе | `GET /api/articles?limit=10&offset=0` | `200 OK`. Возвращает массив `articles` и число `articlesCount`. | **Critical** |
| **TC-ART-SMK-04** | Получение персональной ленты по подпискам (/feed) | Пользователь авторизован и подписан на авторов | `GET /api/articles/feed`<br>Header: `Authorization: Token <jwt>` | `200 OK`. Возвращает статьи только от авторов, на которых подписан текущий юзер. | **Critical** |
| **TC-ART-SMK-05** | Редактирование статьи | Пользователь авторизован и является автором статьи | `PUT /api/articles/how-to-train-your-dragon`<br>`{"article": {"title": "New dragon training guide"}}` | `200 OK`. Статья обновлена, изменен `title`, `slug` или `updatedAt`. | **Critical** |
| **TC-ART-SMK-06** | Удаление статьи | Пользователь авторизован и является автором статьи | `DELETE /api/articles/new-dragon-training-guide`<br>Header: `Authorization: Token <jwt>` | `200 OK` (EmptyOkResponse). Статья удалена из системы. | **Critical** |

---

## 2. Negative & Security Tests (Ошибки и безопасность)

| ID | Сценарий | Шаги / Payload | Ожидаемый результат | Приоритет |
| :--- | :--- | :--- | :--- | :--- |
| **TC-ART-NEG-01** | Создание статьи без обязательных полей (title/description/body) | `POST /api/articles` с пустым или отсутствующим `title` | `422 Unprocessable Entity`. Ошибки валидации (`can't be blank`). | **Critical** |
| **TC-ART-NEG-02** | Редактирование или удаление чужой статьи | `DELETE /api/articles/some-slug` с токеном другого юзера (не автора) | `403 Forbidden` / `401 Unauthorized` / `422`. Статья не удалена. | **Critical** |
| **TC-ART-NEG-03** | Запрос несуществующего slug | `GET /api/articles/non-existent-slug-12345` | `404 Not Found` (или `422`). | **Major** |
| **TC-ART-NEG-04** | Доступ к персональной ленте `/feed` без токена | `GET /api/articles/feed` без заголовка `Authorization` | `401 Unauthorized`. | **Critical** |
| **TC-ART-NEG-05** | Создание статьи неавторизованным пользователем | `POST /api/articles` без токена | `401 Unauthorized`. | **Critical** |

---

## 3. Filtering & Pagination (Фильтрация и пагинация)

| ID | Сценарий | Шаги / Query Params | Ожидаемый результат | Приоритет |
| :--- | :--- | :--- | :--- | :--- |
| **TC-ART-FIL-01** | Фильтрация статей по тегу | `GET /api/articles?tag=reactjs` | Возвращает только статьи, содержащие тег `reactjs` в `tagList`. | **Major** |
| **TC-ART-FIL-02** | Фильтрация статей по автору | `GET /api/articles?author=john_doe` | Возвращает только статьи, написанные автором `john_doe`. | **Major** |
| **TC-ART-FIL-03** | Фильтрация статей по избранному (favorited) | `GET /api/articles?favorited=jane_doe` | Возвращает статьи, добавленные в избранное пользователем `jane_doe`. | **Major** |
| **TC-ART-FIL-04** | Пагинация с limit и offset | `GET /api/articles?limit=5&offset=5` | Возвращает максимум 5 статей, пропуская первые 5 (offset=5). | **Major** |

---

## 4. Mobile & Contract Edge Cases (Специфика мобильного клиента)

| ID | Сценарий проверки | Воздействие / Запрос | Ожидаемый результат для клиента |
| :--- | :--- | :--- | :--- |
| **TC-ART-MOB-01** | **Null-safety для tagList** | Создание или получение статьи, у которой `tagList` пустой или `null` | Мобильный клиент (Android/iOS) корректно обрабатывает пустой массив/null без крэшей `NullPointerException`. |
| **TC-ART-MOB-02** | **Генерация уникального slug при одинаковых title** | Создание двух статей с одинаковым заголовком `"Hello World"` от одного автора | Бэкенд и клиент корректно обрабатывают уникальность (например, додают суффикс `hello-world-xyz`), предотвращая коллизии роутинга. |
| **TC-ART-MOB-03** | **Устойчивость UI к длинному тексту body** | Получение статьи с телом `body` длинной 50,000+ символов | Мобильный рендер (Markdown / ScrollView) отображает контент без зависания UI-потока (ANR / OOM). |
| **TC-ART-MOB-04** | **Обработка пустой ленты (`articlesCount: 0`)** | Запрос ленты `/articles?tag=nonexistent` | Клиент отображает заглушку "No articles are here... yet" вместо бесконечного лоадера. |
