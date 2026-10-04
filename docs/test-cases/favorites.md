# Test Design & Checklist: Favorites Module

Спецификация: `favorites.yml`  
Эндпоинты: `/api/articles/{slug}/favorite`

---

## 1. Smoke Tests (Позитивные критические пути)

| ID | Сценарий | Предусловия | Шаги / Тестовые данные | Ожидаемый результат | Приоритет |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-FAV-SMK-01** | Постановка лайка статье (Favorite) | Пользователь авторизован, статья существует, `favorited: false` | `POST /api/articles/how-to-train-your-dragon/favorite`<br>Header: `Authorization: Token <jwt>` | `200 OK`. Возвращает обновленную статью: `favorited: true`, `favoritesCount` увеличился на 1. | **Critical** |
| **TC-FAV-SMK-02** | Снятие лайка со статьи (Unfavorite) | Пользователь авторизован, статья в избранном, `favorited: true` | `DELETE /api/articles/how-to-train-your-dragon/favorite`<br>Header: `Authorization: Token <jwt>` | `200 OK`. Возвращает обновленную статью: `favorited: false`, `favoritesCount` уменьшился на 1. | **Critical** |

---

## 2. Negative & Security Tests (Ошибки и безопасность)

| ID | Сценарий | Шаги / Payload | Ожидаемый результат | Приоритет |
| :--- | :--- | :--- | :--- | :--- |
| **TC-FAV-NEG-01** | Лайк/дизлайк без авторизации (нет токена) | `POST /api/articles/slug/favorite` без заголовка `Authorization` | `401 Unauthorized`. | **Critical** |
| **TC-FAV-NEG-02** | Лайк несуществующей статьи | `POST /api/articles/non-existent-slug-xyz/favorite` с валидным токеном | `404 Not Found` (или `422`). | **Major** |

---

## 3. Edge Cases (Крайние случаи и идемпотентность)

| ID | Сценарий проверки | Воздействие / Запрос | Ожидаемый результат для клиента |
| :--- | :--- | :--- | :--- |
| **TC-FAV-EDG-01** | **Идемпотентность повторного лайка** | Вызов `POST /.../favorite` два раза подряд для уже лайкнутой статьи | Сервер возвращает `200 OK`, счетчик `favoritesCount` не дублируется (не растет бесконечно). |
| **TC-FAV-EDG-02** | **Проверка счетчика лайков гостем** | Просмотр статьи неавторизованным пользователем (`GET /api/articles/{slug}`) | Поле `favoritesCount` отображает актуальное глобальное число лайков, а `favorited` всегда `false`. |
