# Yandex Tracker MCP Server

![PyPI - Version](https://img.shields.io/pypi/v/yandex-tracker-mcp)
![Test Workflow](https://github.com/aikts/yandex-tracker-mcp/actions/workflows/test.yml/badge.svg?branch=main)
![Release Workflow](https://github.com/aikts/yandex-tracker-mcp/actions/workflows/release.yml/badge.svg?branch=main)

mcp-name: io.github.aikts/yandex-tracker-mcp

Комплексный MCP (Model Context Protocol) сервер, который позволяет ИИ-ассистентам взаимодействовать с API Яндекс.Трекера. Этот сервер обеспечивает безопасный, аутентифицированный доступ к задачам, очередям, комментариям, трудозатратам и функциям поиска Яндекс.Трекера с опциональным Redis-кешированием для улучшения производительности.

<a href="https://glama.ai/mcp/servers/@aikts/yandex-tracker-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@aikts/yandex-tracker-mcp/badge" />
</a>

## Возможности

- **Полное управление очередями**: Список и доступ ко всем доступным очередям Яндекс.Трекера с поддержкой пагинации, получением тегов и подробными метаданными
- **Проекты, портфели и цели**: Отдельные инструменты чтения и записи с явными схемами для каждого типа сущности API "entities" Трекера (включаются через `TRACKER_ENTITIES_ENABLED`)
- **Управление пользователями**: Получение информации об учетных записях пользователей, включая данные для входа, адреса электронной почты, статус лицензии и данные организации
- **Полный жизненный цикл задач**: Создание, чтение, обновление и управление задачами с поддержкой пользовательских полей, вложений и переходов по рабочему процессу
- **Управление рабочим процессом**: Выполнение переходов статусов, закрытие задач с резолюциями и навигация по сложным рабочим процессам
- **Управление полями**: Доступ к глобальным полям, локальным полям очереди, статусам, типам задач, приоритетам и резолюциям
- **Доски и спринты**: Получение списка Agile-досок и их спринтов для поиска идентификаторов спринтов при планировании задач
- **Расширенный язык запросов**: Полная поддержка языка запросов Яндекс.Трекера со сложной фильтрацией, сортировкой
- **Кеширование производительности**: Опциональный слой кеширования Redis для улучшения времени отклика
- **Контроль безопасности**: Настраиваемые ограничения доступа к очередям и безопасная обработка токенов
- **Несколько вариантов транспорта**: Поддержка stdio, SSE (устаревший) и HTTP транспортов для гибкой интеграции
- **OAuth 2.0 аутентификация**: Динамическая аутентификация на основе токенов с автоматическим обновлением в качестве альтернативы статическим API-токенам
- **Поддержка организаций**: Совместимость как со стандартными, так и с облачными идентификаторами организаций

### Конфигурация идентификатора организации

Выберите один из следующих вариантов в зависимости от типа вашей организации Яндекса:

- **Организация Yandex Cloud**: Используйте переменную окружения `TRACKER_CLOUD_ORG_ID` для организаций, управляемых Yandex Cloud
- **Организация Яндекс 360**: Используйте переменную окружения `TRACKER_ORG_ID` для организаций Яндекс 360

Вы можете найти идентификатор вашей организации в URL Яндекс.Трекера или в настройках организации.

## Конфигурация MCP клиента

### Установка расширения в Claude Desktop

Yandex Tracker MCP Server можно установить в один клик в Claude Desktop как [расширение](https://www.anthropic.com/engineering/desktop-extensions).

#### Установка

1. Скачайте файл `*.mcpb` из [GitHub Releases](https://github.com/aikts/yandex-tracker-mcp/releases/latest).
2. Откройте скачанный файл, чтобы установить его в Claude Desktop. ![img.png](images/claude-desktop-install.png)
3. Введите ваш OAuth токен Яндекс.Трекера при запросе. ![img.png](images/claude-desktop-config.png)
4. Убедитесь, что расширение включено - теперь вы можете использовать этот MCP сервер.

### Ручная установка

#### Предварительные требования

- [uv](https://docs.astral.sh/uv/getting-started/installation/) установлен глобально
- Действительный API токен Яндекс.Трекера с соответствующими разрешениями

Следующие разделы показывают, как настроить MCP сервер для различных MCP-клиентов. Вы можете использовать либо `uvx yandex-tracker-mcp@latest`, либо Docker-образ `ghcr.io/aikts/yandex-tracker-mcp:latest`. Оба требуют следующие переменные окружения:

- Аутентификация (один из следующих):
  - `TRACKER_TOKEN` - Ваш OAuth токен Яндекс.Трекера
  - `TRACKER_IAM_TOKEN` - Ваш IAM токен
  - `TRACKER_SA_KEY_ID`, `TRACKER_SA_SERVICE_ACCOUNT_ID`, `TRACKER_SA_PRIVATE_KEY` - Учетные данные сервисного аккаунта
- Организация - ровно одна из следующих переменных:
  - `TRACKER_CLOUD_ORG_ID` - Идентификатор вашей организации Yandex Cloud
  - `TRACKER_ORG_ID` - Идентификатор вашей организации Яндекс 360

> Задавайте **одну** из двух. Если заданы обе, любой вызов Трекера завершится ошибкой
> `Only one of org_id or cloud_org_id should be provided.` В примерах ниже используется
> `TRACKER_CLOUD_ORG_ID`; для Яндекс 360 замените этот ключ на `TRACKER_ORG_ID`.

<details>
<summary><strong>Claude Desktop</strong></summary>

**Путь к файлу конфигурации:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

**Используя uvx:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "ваш_токен_трекера",
        "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
      }
    }
  }
}
```

**Используя Docker:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "ваш_токен_трекера",
        "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Claude Code</strong></summary>

**Используя uvx:**
```bash
claude mcp add yandex-tracker uvx yandex-tracker-mcp@latest \
  -e TRACKER_TOKEN=ваш_токен_трекера \
  -e TRACKER_CLOUD_ORG_ID=ваш_cloud_org_id \
  -e TRANSPORT=stdio
```

**Используя Docker:**
```bash
claude mcp add yandex-tracker docker "run --rm -i -e TRACKER_TOKEN=ваш_токен_трекера -e TRACKER_CLOUD_ORG_ID=ваш_cloud_org_id -e TRANSPORT=stdio ghcr.io/aikts/yandex-tracker-mcp:latest"
```

</details>

<details>
<summary><strong>Cursor</strong></summary>

**Путь к файлу конфигурации:**
- Для проекта: `.cursor/mcp.json` в директории вашего проекта
- Глобальный: `~/.cursor/mcp.json`

**Используя uvx:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "ваш_токен_трекера",
        "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
      }
    }
  }
}
```

**Используя Docker:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "ваш_токен_трекера",
        "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Windsurf</strong></summary>

**Путь к файлу конфигурации:**
- `~/.codeium/windsurf/mcp_config.json`

Доступ через: Настройки Windsurf → вкладка Cascade → Model Context Protocol (MCP) Servers → "View raw config"

**Используя uvx:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "ваш_токен_трекера",
        "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
      }
    }
  }
}
```

**Используя Docker:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "ваш_токен_трекера",
        "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Zed</strong></summary>

**Путь к файлу конфигурации:**
- `~/.config/zed/settings.json`

Доступ через: `Cmd+,` (macOS) или `Ctrl+,` (Linux/Windows) или палитра команд: "zed: open settings"

**Примечание:** Требуется версия Zed Preview для поддержки MCP.

**Используя uvx:**
```json
{
  "context_servers": {
    "yandex-tracker": {
      "source": "custom",
      "command": {
        "path": "uvx",
        "args": ["yandex-tracker-mcp@latest"],
        "env": {
          "TRACKER_TOKEN": "ваш_токен_трекера",
          "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
        }
      }
    }
  }
}
```

**Используя Docker:**
```json
{
  "context_servers": {
    "yandex-tracker": {
      "source": "custom",
      "command": {
        "path": "docker",
        "args": [
          "run", "--rm", "-i",
          "-e", "TRACKER_TOKEN",
          "-e", "TRACKER_CLOUD_ORG_ID",
          "ghcr.io/aikts/yandex-tracker-mcp:latest"
        ],
        "env": {
          "TRACKER_TOKEN": "ваш_токен_трекера",
          "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
        }
      }
    }
  }
}
```

</details>

<details>
<summary><strong>GitHub Copilot (VS Code)</strong></summary>

**Путь к файлу конфигурации:**
- Рабочее пространство: `.vscode/mcp.json` в директории вашего проекта
- Глобальный: VS Code `settings.json`

**Вариант 1: Конфигурация рабочего пространства (рекомендуется для безопасности)**

Создайте `.vscode/mcp.json`:

**Используя uvx:**
```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "tracker-token",
      "description": "Токен Яндекс.Трекера",
      "password": true
    },
    {
      "type": "promptString",
      "id": "cloud-org-id",
      "description": "Идентификатор организации Yandex Cloud"
    }
  ],
  "servers": {
    "yandex-tracker": {
      "type": "stdio",
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "${input:tracker-token}",
        "TRACKER_CLOUD_ORG_ID": "${input:cloud-org-id}",
        "TRANSPORT": "stdio"
      }
    }
  }
}
```

**Используя Docker:**
```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "tracker-token",
      "description": "Токен Яндекс.Трекера",
      "password": true
    },
    {
      "type": "promptString",
      "id": "cloud-org-id",
      "description": "Идентификатор организации Yandex Cloud"
    }
  ],
  "servers": {
    "yandex-tracker": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "${input:tracker-token}",
        "TRACKER_CLOUD_ORG_ID": "${input:cloud-org-id}",
        "TRANSPORT": "stdio"
      }
    }
  }
}
```

**Вариант 2: Глобальная конфигурация**

Добавьте в VS Code `settings.json`:

**Используя uvx:**
```json
{
  "github.copilot.chat.mcp.servers": {
    "yandex-tracker": {
      "type": "stdio",
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "ваш_токен_трекера",
        "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
      }
    }
  }
}
```

**Используя Docker:**
```json
{
  "github.copilot.chat.mcp.servers": {
    "yandex-tracker": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "ваш_токен_трекера",
        "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Другие MCP-совместимые клиенты</strong></summary>

Для других MCP-совместимых клиентов используйте стандартный формат конфигурации MCP сервера:

**Используя uvx:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "uvx",
      "args": ["yandex-tracker-mcp@latest"],
      "env": {
        "TRACKER_TOKEN": "ваш_токен_трекера",
        "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
      }
    }
  }
}
```

**Используя Docker:**
```json
{
  "mcpServers": {
    "yandex-tracker": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "TRACKER_TOKEN",
        "-e", "TRACKER_CLOUD_ORG_ID",
        "ghcr.io/aikts/yandex-tracker-mcp:latest"
      ],
      "env": {
        "TRACKER_TOKEN": "ваш_токен_трекера",
        "TRACKER_CLOUD_ORG_ID": "ваш_cloud_org_id"
      }
    }
  }
}
```

</details>

**Важные замечания:**
- Замените значения на ваши реальные учетные данные
- Перезапустите ваш MCP-клиент после изменения конфигурации
- При использовании `uvx` убедитесь, что `uvx` установлен и доступен в вашем системном PATH
- Для production использования рассмотрите использование переменных окружения вместо жесткого кодирования токенов

## Доступные MCP инструменты

Сервер предоставляет следующие инструменты через протокол MCP:

<details>
<summary><strong>Управление очередями</strong></summary>

| Инструмент | Что делает | Ключевые аргументы |
| --- | --- | --- |
| `queues_get_all` | Все очереди, доступные токену; возвращает `{values, hits, pages}` | `fields`, `page` (не указывать — обойти все страницы), `per_page` |
| `queue_get_tags` | Теги, заведённые в очереди | `queue_id` (ключ вида `"SOMEPROJECT"`) |
| `queue_get_versions` | Версии очереди с датами и статусом | `queue_id` |
| `queue_create_version` | Создать версию в очереди | `queue_id`, `name`, `description`, `start_date`, `due_date` (`YYYY-MM-DD`) |
| `queue_get_fields` | Поля, настроенные в очереди, включая локальные; `schema.required` отмечает обязательные | `queue_id`, `include_local_fields` |
| `queue_get_metadata` | Название, описание, тип и приоритет по умолчанию плюс то, что запрошено в `expand` | `queue_id`, `expand` (`all`, `projects`, `components`, `versions`, `types`, `team`, `workflows`, `fields`, `issueTypesConfig`) |

- Читайте `queue_get_fields` перед `issue_create`, но это не полный реестр: системные поля вроде `parent` или `estimation` можно задавать, хотя в нём их нет, а `get_global_fields` перечисляет все поля организации.
- `queue_get_metadata` с `expand: ["issueTypesConfig"]` — источник резолюций, допустимых для каждого типа задачи; одна из них нужна `issue_close`.
- Все они учитывают `TRACKER_LIMIT_QUEUES`. `hits` / `pages` у `queues_get_all` возвращаются только для явно запрошенной страницы на сервере без allow-list: иначе итог считает и те очереди, которые allow-list затем скрывает.

</details>

<details>
<summary><strong>Проекты, портфели и цели</strong></summary>

Проекты, портфели и цели — это отдельные сущности Яндекс Трекера (отличные от очередей), доступные через API "entities" Трекера. Пользовательские (кастомные) атрибуты не моделируются и не возвращаются.

> **Эти инструменты включаются явно.** Они регистрируются только при `TRACKER_ENTITIES_ENABLED=true` (по умолчанию `false`), потому что заметно увеличивают манифест инструментов и не подчиняются ограничениям по очередям — см. [Управление доступом к очередям](#управление-доступом-к-очередям).

Все три типа сущностей используют один и тот же набор инструментов, поэтому он перечислен
один раз: строка говорит, что делает инструмент, а столбцы — как он называется:

| Что делает | Проекты | Портфели | Цели |
| --- | --- | --- | --- |
| Одна сущность по id или shortId | `project_get` | `portfolio_get` | `goal_get` |
| Поиск по подстроке в названии и/или фильтрам полей; возвращает `{values, hits, pages}` | `project_find` | `portfolio_find` | `goal_find` |
| Страница комментариев; возвращает `{comments, next_cursor}` | `project_get_comments` | `portfolio_get_comments` | `goal_get_comments` |
| Создать и вернуть сущность | `project_create` | `portfolio_create` | `goal_create` |
| Изменить любое поле из тех, что принимает создание | `project_update` | `portfolio_update` | `goal_update` |
| Удалить, а с `with_board` — и связанную доску (у целей доски нет) | `project_delete` | `portfolio_delete` | `goal_delete` |
| Добавить комментарий | `project_add_comment` | `portfolio_add_comment` | `goal_add_comment` |
| Изменить комментарий | `project_update_comment` | `portfolio_update_comment` | `goal_update_comment` |
| Удалить комментарий | `project_delete_comment` | `portfolio_delete_comment` | `goal_delete_comment` |
| Добавить пункт чек-листа | `project_add_checklist_item` | `portfolio_add_checklist_item` | - |
| Изменить один пункт, оставив непереданные поля как есть | `project_update_checklist_item` | `portfolio_update_checklist_item` | - |
| Переставить пункт перед другим | `project_move_checklist_item` | `portfolio_move_checklist_item` | - |
| Удалить один пункт | `project_delete_checklist_item` | `portfolio_delete_checklist_item` | - |
| Изменить несколько существующих пунктов по id | `project_update_checklist` | `portfolio_update_checklist` | - |
| Удалить весь чек-лист | `project_delete_checklist` | `portfolio_delete_checklist` | - |

- **Аргументы.** Чтение принимает `entity_id` и `fields`; инструменты `*_find` — `input`, `filter`, `order_by`, `order_asc`, `root_only`, `page`, `per_page`. Создание и изменение принимают `summary` (обязателен при создании), `description`, `lead`, `team_users`, `clients`, `followers`, `start` (у целей его нет), `end`, `tags`, `entity_status`, `parent_entity`, `team_access` и `links`, а изменение ещё `comment` и `version` (оптимистичная блокировка). Все инструменты принимают один и тот же селектор `fields` и возвращают сущность.
- **`links` только добавляются, а не заменяются**, и API их никогда не возвращает: прочитать или удалить существующую связь через этот сервер нельзя, а изменение, состоящее только из `links`, отклоняется — вместо того чтобы отчитаться об успехе, который Трекер молча проигнорировал.
- **Не входит в набор полей по умолчанию:** `checklistItems` (инструменты чек-листа возвращают сущность целиком, так что запрашивайте их, чтобы увидеть результат), `metricItems` и ключевые результаты цели `keyResultItems` — последние два доступны только на чтение. У целей свой набор значений `entityStatus` (`draft`, `according_to_plan`, `at_risk`, `blocked`, `achieved`, `partially_achieved`, `not_achieved`, `exceeded`, `cancelled`). Массовые изменения не поддерживаются.

</details>

<details>
<summary><strong>Управление пользователями</strong></summary>

| Инструмент | Что делает | Ключевые аргументы |
| --- | --- | --- |
| `users_get_all` | Страница пользователей организации; возвращает `{values, hits, pages}` | `page`, `per_page`, `fields` |
| `user_get` | Один пользователь по логину или uid | `user_id` (`"john.doe"` или `"12345"`) |
| `user_get_current` | Пользователь, которому принадлежит текущий токен | - |
| `users_search` | Поиск пользователей по логину, email или имени | `login_or_email_or_name` |

- `users_search` сначала ищет точное совпадение по логину и email, затем — нечёткое по имени (порог схожести 80%, не более трёх лучших совпадений).
- Страница `users_get_all` — последняя, когда `page` равен `pages`.

</details>

<details>
<summary><strong>Управление полями</strong></summary>

| Инструмент | Что делает | Ключевые аргументы |
| --- | --- | --- |
| `get_global_fields` | Все глобальные поля организации со схемой и типом | - |

Локальных полей очереди здесь нет — `queue_get_fields` возвращает их вместе с глобальными.

</details>

<details>
<summary><strong>Управление статусами и типами</strong></summary>

| Инструмент | Что делает | Ключевые аргументы |
| --- | --- | --- |
| `get_statuses` | Все статусы задач, заведённые в организации | - |
| `get_issue_types` | Все типы задач — для аргумента `type` у `issue_create` / `issue_update` | - |
| `get_priorities` | Все приоритеты с `id`, `key`, `name` и `order` | - |
| `get_resolutions` | Все резолюции — для `resolution_id` у `issue_close` | - |

Все четыре списка общие для организации. Очередь может принимать лишь часть этих значений, и на неподходящее Трекер отвечает 422: какие резолюции допустимы для каждого типа задачи, показывает `queue_get_metadata` с `expand: ["issueTypesConfig"]`.

</details>

<details>
<summary><strong>Шаблоны</strong></summary>

| Инструмент | Что делает | Ключевые аргументы |
| --- | --- | --- |
| `issue_templates_get_all` | Шаблоны задач вместе со значениями `fieldTemplates`, которые они подставляют; возвращает `{values, hits, pages}` | `queue`, `page` (не указывать — обойти все страницы), `per_page` |
| `issue_template_get` | Один шаблон задачи по id | `template_id` |
| `comment_templates_get_all` | Шаблоны комментариев с текстом `template` и его `summonees` / `maillistSummonees` | `queue`, `page`, `per_page` |
| `comment_template_get` | Один шаблон комментария по id | `template_id` |

- **Шаблоны доступны только на чтение.** API не умеет создавать задачу или комментарий *из* шаблона, поэтому у `issue_create` и `issue_add_comment` нет `template_id`: прочитайте шаблон и передайте его значения аргументами самого инструмента записи. Макросы вроде `{{today}}` приходят как есть.
- Текст задачи, который подставляет шаблон, лежит в `fieldTemplates.description`; собственный `description` шаблона описывает сам шаблон.
- `queue` возвращает шаблоны этой очереди плюс те, что не привязаны ни к одной и годятся везде. `TRACKER_LIMIT_QUEUES` учитывается: шаблоны закрытой очереди не попадают в списки и отклоняются при прямом обращении, а шаблоны без очереди остаются видимыми.

</details>

<details>
<summary><strong>Доски и спринты</strong></summary>

| Инструмент | Что делает | Ключевые аргументы |
| --- | --- | --- |
| `boards_get_all` | Agile-доски организации; возвращает `{boards, next_cursor}` | `queue`, `fields`, `cursor` (предыдущий `next_cursor`), `per_page` |
| `board_get` | Одна доска с `autoFilterSettings` (что она собирает), `estimateBy`, `useRanking` и рабочим `calendar` | `board_id`, `fields` |
| `board_get_columns` | Колонки доски со статусами задач, которые в них попадают | `board_id` |
| `board_get_sprints` | Спринты доски со статусом (`draft`, `in_progress`, `released`, `archived`) и плановыми/фактическими датами | `board_id`, `fields` |

- У доски нет собственной очереди, поэтому `queue` сопоставляется с фильтром самой доски и не находит доски, которые фильтруют по чему-то другому — например, персональные по исполнителю. Чтобы найти и их, прочитайте несколько задач очереди через `issues_find` и посмотрите их поле `boards`.
- Доски принадлежат организации, а не очереди, поэтому `TRACKER_LIMIT_QUEUES` их не фильтрует: проверяется только аргумент `queue` у `boards_get_all`, а в ответах могут упоминаться закрытые очереди.
- У не-scrum доски спринтов нет, и `board_get_sprints` для неё отклоняется. Возвращённый `id` спринта — это то, что принимают `issue_create` / `issue_update`.

</details>

<details>
<summary><strong>Операции с задачами</strong></summary>

| Инструмент | Что делает | Ключевые аргументы |
| --- | --- | --- |
| `issue_get` | Одна задача по ключу: полная запись, включая текущий `version` | `issue_id`, `include_description` |
| `issue_get_url` | Веб-адрес задачи | `issue_id` |
| `issue_get_comments` | Страница комментариев, от старых к новым; возвращает `{comments, next_cursor}` | `issue_id`, `cursor`, `per_page`, `fields` |
| `issue_add_comment` | Добавить комментарий; уведомляет именно `summonees`, а `@login` в тексте не уведомляет никого | `issue_id`, `text`, `summonees`, `maillist_summonees`, `markup_type`, `is_add_to_followers` |
| `issue_update_comment` | Изменить комментарий | `issue_id`, `comment_id`, `text`, `summonees`, `maillist_summonees` |
| `issue_delete_comment` | Удалить комментарий | `issue_id`, `comment_id` |
| `issue_get_links` | Связи со связанными, блокирующими и дублирующими задачами | `issue_id` |
| `issue_add_link` | Связать две задачи | `issue_id`, `relationship`, `issue` |
| `issue_delete_link` | Удалить связь | `issue_id`, `link_id` (из `issue_get_links`) |
| `issue_get_worklogs` | Списанное время по одной или нескольким задачам | `issue_ids`, `fields` |
| `issue_add_worklog` | Списать время | `issue_id`, `duration` (ISO-8601, `PT1H30M`), `comment`, `start` |
| `issue_update_worklog` | Изменить запись о времени | `issue_id`, `worklog_id`, `duration`, `comment`, `start` |
| `issue_delete_worklog` | Удалить запись о времени | `issue_id`, `worklog_id` |
| `issue_get_attachments` | Метаданные вложений | `issue_id`, `fields` |
| `issue_get_checklist` | Чек-лист вместе с id пунктов, которые нужны инструментам записи | `issue_id` |
| `issue_add_checklist_items` | Добавить пункты по порядку, создав чек-лист, если его не было | `issue_id`, `items` (`text`, `checked`, `assignee`, `deadline`) |
| `issue_update_checklist_item` | Изменить один пункт; непереданные поля сохраняют значение | `issue_id`, `checklist_item_id`, `text`, `checked`, `assignee`, `deadline`, `clear_assignee`, `clear_deadline` |
| `issue_delete_checklist_item` | Удалить один пункт | `issue_id`, `checklist_item_id` |
| `issue_get_transitions` | Переходы по статусам, доступные сейчас, с их id | `issue_id` |
| `issue_execute_transition` | Выполнить переход; возвращает переходы, доступные после него | `issue_id`, `transition_id`, `comment`, `fields` |
| `issue_close` | Найти переход в статус «готово» и выполнить его с резолюцией | `issue_id`, `resolution_id`, `comment`, `fields` |
| `issue_get_changelog` | Изменения полей, переходы по статусам, правки комментариев и сработавшие триггеры; возвращает `{entries, next_cursor}` | `issue_id`, `cursor`, `per_page`, `field`, `type` |
| `issue_create` | Создать задачу и вернуть её | `queue`, `summary`, `type`, `description`, `markup_type`, `assignee`, `priority`, `parent`, `sprint`, `followers`, `components`, `tags`, `project`, `fields` |
| `issue_update` | Изменить любое из этих полей; непереданные остаются как были | `issue_id`, `version` и аргументы `issue_create` |
| `issue_move` | Перенести задачу в другую очередь, что меняет её ключ (`TASKS-1` → `NEWQUEUE-42`) | `issue_id`, `queue`, `notify`, `notify_author`, `move_all_fields`, `initial_status` |

- **`version` протухает сам по себе.** Триггеры очереди и автоматизации срабатывают сразу после `issue_create` и увеличивают его, так что возвращённая версия обычно уже устарела. Перечитайте её через `issue_get` прямо перед `issue_update` или не передавайте вовсе, чтобы изменить последнюю версию безусловно: на устаревшей вызов падает с конфликтом редактирования.
- **Ссылочные поля принимают одни и те же значения и при создании, и при изменении:** объект с `id` и/или `key`, а для `type`, `priority` и `parent` — ещё и голый ключ или id. `components` принимают `{"id": ...}` или `{"name": ...}`, причём `components` / `followers` заменяют текущий список, а не дополняют его. Всё, для чего нет отдельного аргумента, передаётся в карте `fields` по `id` поля из `queue_get_fields`; запись там перекрывает отдельный аргумент, а явный `null` очищает поле.
- **Переходы не угадываются.** `issue_execute_transition` принимает только id из `issue_get_transitions`, а перед `issue_close` прочитайте `type` задачи через `issue_get` и допустимые для этого типа резолюции через `queue_get_metadata` с `expand: ["issueTypesConfig"]` — у каждого типа свой набор. Если клиент поддерживает elicitation, `issue_move` сначала просит подтвердить свои флаги, и отказ отменяет перенос.

Все инструменты этого раздела учитывают `TRACKER_LIMIT_QUEUES` и `TRACKER_READ_ONLY_QUEUES`; те, что пишут, регистрируются, только если не задан `TRACKER_READ_ONLY`.

</details>

<details>
<summary><strong>Поиск и обнаружение</strong></summary>

| Инструмент | Что делает | Ключевые аргументы |
| --- | --- | --- |
| `issues_find` | Поиск задач на [языке запросов Яндекс Трекера](https://yandex.ru/support/tracker/ru/user/query-filter); возвращает `{values, hits, pages}` | `query`, `fields`, `include_description`, `page`, `per_page` |
| `issues_count` | Сколько задач подходит под запрос; возвращает `{"count": N}` | `query` |

- `fields` использует написание самого Трекера (`storyPoints`, а не `story_points`) и принимает любое имя поля, включая локальные поля очереди и пользовательские поля организации — передавайте `id` поля из `queue_get_fields`. Неизвестное Трекеру имя молча отбрасывается.
- `include_description` игнорируется, если `description` перечислен в `fields`: указание его там и есть явный запрос.
- `per_page` по умолчанию 100 и может быть уменьшен, если страница не влезает в контекст.

</details>

## Транспорт http

MCP сервер также может работать в режиме streamable-http для веб-интеграций или когда транспорт stdio не подходит.

### Переменные окружения режима streamable-http

```env
# Обязательно - Установить транспорт в режим streamable-http
TRANSPORT=streamable-http

# Конфигурация сервера
HOST=0.0.0.0  # По умолчанию: 0.0.0.0 (все интерфейсы)
PORT=8000     # По умолчанию: 8000
```

### Запуск streamable-http сервера

```bash
# Базовый запуск streamable-http сервера
TRANSPORT=streamable-http uvx yandex-tracker-mcp@latest

# С пользовательским хостом и портом
TRANSPORT=streamable-http \
HOST=localhost \
PORT=9000 \
uvx yandex-tracker-mcp@latest

# Со всеми переменными окружения
TRANSPORT=streamable-http \
HOST=0.0.0.0 \
PORT=8000 \
TRACKER_TOKEN=ваш_токен \
TRACKER_CLOUD_ORG_ID=ваш_org_id \
uvx yandex-tracker-mcp@latest
```

Вы можете пропустить настройку `TRACKER_CLOUD_ORG_ID` или `TRACKER_ORG_ID`, если используете следующий формат при подключении к MCP серверу (пример для Claude Code):

```bash
claude mcp add --transport http yandex-tracker "http://localhost:8000/mcp/?cloudOrgId=ваш_cloud_org_id&"
```

или

```bash
claude mcp add --transport http yandex-tracker "http://localhost:8000/mcp/?orgId=org_id&"
```

Вы также можете пропустить настройку глобальной переменной окружения `TRACKER_TOKEN`, если выберете использование OAuth 2.0 аутентификации (см. ниже).

### OAuth 2.0 аутентификация

Yandex Tracker MCP Server поддерживает OAuth 2.0 аутентификацию как безопасную альтернативу статическим API токенам. При настройке сервер выступает в качестве OAuth провайдера, облегчая аутентификацию между вашим MCP клиентом и сервисами Яндекс OAuth.

#### Как работает OAuth

MCP сервер реализует стандартный поток кода авторизации OAuth 2.0:

1. **Регистрация клиента**: Ваш MCP клиент регистрируется на сервере для получения учетных данных клиента
2. **Авторизация**: Пользователи перенаправляются в Яндекс OAuth для аутентификации
3. **Обмен токенами**: Сервер обменивает коды авторизации на токены доступа
4. **Доступ к API**: Клиенты используют bearer токены для всех запросов API
5. **Обновление токенов**: Истекшие токены можно обновить без повторной аутентификации

```
MCP Клиент → MCP Сервер → Яндекс OAuth → Аутентификация пользователя
    ↑                                           ↓
    └────────── Токен доступа ←─────────────────┘
```

#### Конфигурация OAuth

Для включения OAuth аутентификации установите следующие переменные окружения:

```env
# Включить режим OAuth
OAUTH_ENABLED=true

# Учетные данные приложения Яндекс OAuth (обязательно для OAuth)
OAUTH_CLIENT_ID=ваш_id_приложения_яндекс_oauth
OAUTH_CLIENT_SECRET=ваш_секрет_яндекс_oauth

# Публичный URL вашего MCP сервера (обязательно для OAuth обратных вызовов)
MCP_SERVER_PUBLIC_URL=https://ваш-mcp-сервер.example.com

# Опциональные настройки OAuth
OAUTH_SERVER_URL=https://oauth.yandex.ru  # OAuth сервер Яндекса по умолчанию

# Когда OAuth включен, TRACKER_TOKEN становится опциональным
```

##### OAuth scopes

При `OAUTH_USE_SCOPES=true` (по умолчанию) сервер запрашивает, публикует и требует scope'ы Яндекс
Трекера `tracker:read` и `tracker:write` - либо только `tracker:read`, если задан
`TRACKER_READ_ONLY=true`, чтобы read-only инстанс никогда не просил у пользователя доступ на запись.
`OAUTH_USE_SCOPES=false` полностью убирает scope'ы из потока - это требуется для федерации
Yandex Cloud.

#### Настройка приложения Яндекс OAuth

1. Перейдите на [Яндекс OAuth](https://oauth.yandex.ru/) и создайте новое приложение
2. Установите callback URL: `{MCP_SERVER_PUBLIC_URL}/oauth/yandex/callback`
3. Запросите следующие разрешения:
   - `tracker:read` - Разрешения на чтение для Трекера
   - `tracker:write` - Разрешения на запись для Трекера
4. Сохраните ваш Client ID и Client Secret

#### OAuth против аутентификации статическим токеном

| Функция               | OAuth                                   | Статический токен               |
|-----------------------|-----------------------------------------|---------------------------------|
| Безопасность          | Динамические токены с истечением        | Долгоживущие статические токены |
| Пользовательский опыт | Интерактивный поток входа               | Однократная настройка           |
| Управление токенами   | Автоматическое обновление               | Ручная ротация                  |
| Контроль доступа      | Аутентификация для каждого пользователя | Общий токен                     |
| Сложность настройки   | Требует настройки OAuth приложения      | Простая настройка токена        |

#### Ограничения режима OAuth

- В настоящее время режим OAuth требует, чтобы MCP сервер был публично доступен для URL обратных вызовов
- Режим OAuth лучше всего подходит для интерактивных клиентов, которые поддерживают веб-потоки аутентификации

#### Использование OAuth с MCP клиентами

Когда OAuth включен, MCP клиентам необходимо:
1. Поддерживать поток кода авторизации OAuth 2.0
2. Обрабатывать обновление токенов при истечении срока действия токенов доступа
3. Безопасно хранить токены обновления для постоянной аутентификации

**Примечание**: Не все MCP клиенты в настоящее время поддерживают OAuth аутентификацию. Проверьте документацию вашего клиента на совместимость с OAuth.

Пример конфигурации для Claude Code:

```bash
claude mcp add --transport http yandex-tracker https://ваш-mcp-сервер.example.com/mcp/ -s user
```

#### Хранилище данных OAuth

MCP сервер поддерживает два различных бэкенда хранения для данных OAuth (регистрации клиентов, токены доступа, токены обновления и состояния авторизации):

##### InMemory хранилище (по умолчанию)

Хранилище в памяти хранит все данные OAuth в памяти сервера. Это опция по умолчанию и не требует дополнительной настройки.

**Характеристики:**
- **Постоянство**: Данные теряются при перезапуске сервера
- **Производительность**: Очень быстрый доступ, так как данные хранятся в памяти
- **Масштабируемость**: Ограничено одним экземпляром сервера
- **Настройка**: Не требуются дополнительные зависимости
- **Лучше всего для**: Разработки, тестирования или развертываний с одним экземпляром, где потеря OAuth сессий при перезапуске приемлема

**Конфигурация:**
```env
OAUTH_STORE=memory  # Значение по умолчанию, можно опустить
```

##### Redis хранилище

Redis хранилище обеспечивает постоянное хранение данных OAuth с использованием базы данных Redis. Это гарантирует, что OAuth сессии переживут перезапуски сервера и позволяет развертывание с несколькими экземплярами.

**Характеристики:**
- **Постоянство**: Данные сохраняются при перезапусках сервера
- **Производительность**: Быстрый доступ с сетевыми накладными расходами
- **Масштабируемость**: Поддерживает несколько экземпляров сервера, использующих одну и ту же базу данных Redis
- **Настройка**: Требует установки и настройки сервера Redis
- **Лучше всего для**: Производственных развертываний, настроек высокой доступности или когда OAuth сессии должны сохраняться

**Конфигурация:**
```env
# Включить Redis хранилище для данных OAuth
OAUTH_STORE=redis

# Настройки подключения Redis (те же, что используются для кеширования инструментов)
REDIS_ENDPOINT=localhost                  # По умолчанию: localhost
REDIS_PORT=6379                           # По умолчанию: 6379
REDIS_DB=0                                # По умолчанию: 0
REDIS_PASSWORD=ваш_пароль_redis          # Опционально: пароль Redis
REDIS_POOL_MAX_SIZE=10                    # По умолчанию: 10
```

**Поведение хранилища:**
- **Информация о клиенте**: Хранится постоянно
- **Состояния OAuth**: Хранятся с TTL (временем жизни) для безопасности
- **Коды авторизации**: Хранятся с TTL и автоматически очищаются после использования
- **Токены доступа**: Хранятся с автоматическим истечением на основе времени жизни токена
- **Токены обновления**: Хранятся постоянно до отзыва
- **Пространство имен ключей**: Использует префиксы `oauth:*` для избежания конфликтов с другими данными Redis

**Важные замечания:**
- Оба хранилища используют те же настройки подключения Redis, что и система кеширования инструментов
- При использовании Redis хранилища убедитесь, что ваш экземпляр Redis правильно защищен и доступен
- Настройка `OAUTH_STORE` влияет только на хранение данных OAuth; кеширование инструментов использует `TOOLS_CACHE_ENABLED`
- Redis хранилище использует JSON сериализацию для лучшей совместимости между языками и отладки

##### Шифрование токенов (обязательно для Redis хранилища)

При использовании Redis хранилища необходимо настроить шифрование для защиты OAuth токенов в состоянии покоя. Значения токенов шифруются с помощью Fernet (AES-128), а ключи Redis используют хеши SHA-256 вместо сырых токенов, что предотвращает раскрытие токенов в случае компрометации Redis.

**Генерация ключа шифрования:**
```bash
python3 -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"
```

**Конфигурация:**
```env
# Один ключ шифрования
OAUTH_ENCRYPTION_KEYS=<base64-закодированный-32-байтовый-ключ>

# Несколько ключей для ротации (первый шифрует, все расшифровывают)
OAUTH_ENCRYPTION_KEYS=<новый-ключ>,<старый-ключ>
```

Ротация ключей позволяет беспрепятственно обновлять ключи: сначала добавьте новый ключ, дождитесь истечения срока действия старых токенов, затем удалите старый ключ.

## Аутентификация

Yandex Tracker MCP Server поддерживает несколько методов аутентификации с четким порядком приоритета. Сервер будет использовать первый доступный метод аутентификации на основе этой иерархии:

### Порядок приоритета аутентификации

1. **Динамический OAuth токен** (наивысший приоритет)
   - Когда OAuth включен и пользователь аутентифицируется через OAuth поток
   - Токены динамически получаются и обновляются для каждой сессии пользователя
   - Поддерживает как стандартный Яндекс OAuth, так и федеративный OAuth Yandex Cloud
   - Необходимые переменные окружения: `OAUTH_ENABLED=true`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `MCP_SERVER_PUBLIC_URL`
   - Дополнительные переменные для федеративного OAuth: `OAUTH_SERVER_URL=https://auth.yandex.cloud/oauth`, `OAUTH_TOKEN_TYPE=Bearer`, `OAUTH_USE_SCOPES=false`

2. **Проброс OAuth токена через Bearer**
   - Когда OAuth middleware MCP не предоставил токен, сервер может прочитать OAuth токен Яндекса из входящего заголовка `Authorization: Bearer <token>`
   - Полезно за доверенным reverse proxy или gateway, который аутентифицирует пользователей, получает их сохраненный OAuth токен Яндекса и добавляет его в каждый запрос
   - Токен из MCP OAuth сохраняет приоритет, когда OAuth режим включен и активен

3. **Статический OAuth токен**
   - Традиционный OAuth токен, предоставленный через переменную окружения
   - Один токен используется для всех запросов
   - Необходимая переменная окружения: `TRACKER_TOKEN` (ваш OAuth токен)

4. **Статический IAM токен**
   - IAM (Identity and Access Management) токен для межсервисной аутентификации
   - Подходит для автоматизированных систем и CI/CD конвейеров
   - Необходимая переменная окружения: `TRACKER_IAM_TOKEN` (ваш IAM токен)

5. **Динамический IAM токен** (низший приоритет)
   - Автоматически получается с использованием учетных данных сервисного аккаунта
   - Токен извлекается и обновляется автоматически
   - Необходимые переменные: `TRACKER_SA_KEY_ID`, `TRACKER_SA_SERVICE_ACCOUNT_ID`, `TRACKER_SA_PRIVATE_KEY`

### Сценарии аутентификации

#### Сценарий 1: OAuth с динамическими токенами (рекомендуется для интерактивного использования)
```env
# Включить режим OAuth
OAUTH_ENABLED=true
OAUTH_CLIENT_ID=ваш_oauth_app_id
OAUTH_CLIENT_SECRET=ваш_oauth_app_secret
MCP_SERVER_PUBLIC_URL=https://ваш-сервер.com

# ID организации (выберите один)
TRACKER_CLOUD_ORG_ID=ваш_cloud_org_id  # или TRACKER_ORG_ID
```

#### Сценарий 2: Статический OAuth токен (простая настройка)
```env
# OAuth токен
TRACKER_TOKEN=ваш_oauth_токен

# ID организации (выберите один)
TRACKER_CLOUD_ORG_ID=ваш_cloud_org_id  # или TRACKER_ORG_ID
```

#### Сценарий 3: Проброс Bearer токена за reverse proxy
Используйте этот режим, когда доверенный gateway выполняет аутентификацию пользователя, получает его OAuth токен Яндекса и проксирует запрос к MCP серверу с этим токеном в заголовке:

```http
Authorization: Bearer <oauth_токен_пользователя_в_яндексе>
```

```env
# ID организации (выберите один)
TRACKER_CLOUD_ORG_ID=ваш_cloud_org_id  # или TRACKER_ORG_ID
```

Проброшенный токен используется только если OAuth middleware MCP не предоставил access token для запроса. В deployments с включенным OAuth и активной MCP OAuth сессией приоритет остается у токена MCP OAuth.

#### Сценарий 4: Статический IAM токен
```env
# IAM токен
TRACKER_IAM_TOKEN=ваш_iam_токен

# ID организации (выберите один)
TRACKER_CLOUD_ORG_ID=ваш_cloud_org_id  # или TRACKER_ORG_ID
```

#### Сценарий 5: Динамический IAM токен с сервисным аккаунтом
```env
# Учетные данные сервисного аккаунта
TRACKER_SA_KEY_ID=ваш_key_id
TRACKER_SA_SERVICE_ACCOUNT_ID=ваш_service_account_id
TRACKER_SA_PRIVATE_KEY=ваш_private_key

# ID организации (выберите один)
TRACKER_CLOUD_ORG_ID=ваш_cloud_org_id  # или TRACKER_ORG_ID
```

#### Сценарий 6: Федеративный OAuth для OIDC-приложений (расширенный)
```env
# Включить OAuth с федерацией Yandex Cloud
OAUTH_ENABLED=true
OAUTH_SERVER_URL=https://auth.yandex.cloud/oauth
OAUTH_TOKEN_TYPE=Bearer
OAUTH_USE_SCOPES=false
OAUTH_CLIENT_ID=ваш_oidc_client_id
OAUTH_CLIENT_SECRET=ваш_oidc_client_secret
MCP_SERVER_PUBLIC_URL=https://ваш-сервер.com

# ID организации (выберите один)
TRACKER_CLOUD_ORG_ID=ваш_cloud_org_id  # или TRACKER_ORG_ID
```

Эта конфигурация включает аутентификацию через [OIDC-приложения Yandex Cloud](https://yandex.cloud/ru/docs/organization/operations/applications/oidc-create), что требуется для [федеративных аккаунтов](https://yandex.cloud/ru/docs/organization/operations/manage-federations) в Yandex Cloud. Федеративные пользователи аутентифицируются через поставщика удостоверений (IdP) своей организации и используют этот OAuth поток для доступа к API Яндекс.Трекера.

### Важные замечания

- Сервер проверяет методы аутентификации в порядке, указанном выше
- За раз используется только один метод аутентификации
- Для production использования рекомендуются динамические токены (OAuth или IAM) для лучшей безопасности
- IAM токены имеют более короткое время жизни, чем OAuth токены, и могут требовать более частого обновления
- При использовании сервисных аккаунтов убедитесь, что аккаунт имеет соответствующие разрешения для Яндекс.Трекера

## Конфигурация

### Переменные окружения

```env
# Аутентификация (используйте один из следующих методов)
# Метод 1: OAuth токен
TRACKER_TOKEN=ваш_oauth_токен_яндекс_трекера

# Метод 2: IAM токен
TRACKER_IAM_TOKEN=ваш_iam_токен

# Метод 3: Сервисный аккаунт (для динамического IAM токена)
TRACKER_SA_KEY_ID=ваш_key_id                   # ID ключа сервисного аккаунта
TRACKER_SA_SERVICE_ACCOUNT_ID=ваш_sa_id        # ID сервисного аккаунта
TRACKER_SA_PRIVATE_KEY=ваш_private_key          # Приватный ключ сервисного аккаунта

# Конфигурация организации (задайте ровно одну - обе сразу задавать нельзя)
TRACKER_CLOUD_ORG_ID=ваш_cloud_org_id    # Для организаций Yandex Cloud
TRACKER_ORG_ID=ваш_org_id                # Для организаций Яндекс 360

# Конфигурация API (опционально)
TRACKER_API_BASE_URL=https://api.tracker.yandex.net  # По умолчанию: https://api.tracker.yandex.net
TRACKER_API_TIMEOUT=10                    # По умолчанию: 10 - Таймаут одного запроса к API Трекера, в секундах

# Безопасность - Ограничить доступ к конкретным очередям (опционально)
TRACKER_LIMIT_QUEUES=PROJ1,PROJ2,DEV      # Ключи очередей через запятую - список разрешённых очередей
TRACKER_READ_ONLY_QUEUES=PROJ2            # Ключи очередей через запятую - доступны для чтения, но запись отклоняется (режим только для чтения по очередям)
TRACKER_ENTITIES_ENABLED=true             # По умолчанию: false - регистрировать инструменты проектов/портфелей/целей (НЕ подчиняются ограничениям по очередям выше)

# Конфигурация сервера
HOST=0.0.0.0                              # По умолчанию: 0.0.0.0
PORT=8000                                 # По умолчанию: 8000
TRANSPORT=stdio                           # Опции: stdio, streamable-http, sse

# Настройки подключения Redis (используются для кеширования и OAuth хранилища)
REDIS_ENDPOINT=localhost                  # По умолчанию: localhost
REDIS_PORT=6379                           # По умолчанию: 6379
REDIS_DB=0                                # По умолчанию: 0
REDIS_PASSWORD=ваш_пароль_redis          # Опционально: пароль Redis
REDIS_POOL_MAX_SIZE=10                    # По умолчанию: 10

# Конфигурация кеширования инструментов (опционально)
TOOLS_CACHE_ENABLED=true                  # По умолчанию: false
TOOLS_CACHE_REDIS_TTL=3600                # По умолчанию: 3600 секунд (1 час)

# OAuth 2.0 аутентификация (опционально)
OAUTH_ENABLED=true                        # По умолчанию: false
OAUTH_STORE=redis                         # Опции: memory, redis (по умолчанию: memory)
OAUTH_SERVER_URL=https://oauth.yandex.ru  # По умолчанию: https://oauth.yandex.ru (используйте https://auth.yandex.cloud/oauth для федерации)
OAUTH_TOKEN_TYPE=<Bearer|OAuth|<empty>>   # По умолчанию: <empty> (обязательно должен быть указан Bearer для федерации Yandex Cloud)
OAUTH_USE_SCOPES=true                    # По умолчанию: true (установите false для федерации Yandex Cloud)
OAUTH_CLIENT_ID=ваш_oauth_client_id      # Обязательно когда OAuth включен
OAUTH_CLIENT_SECRET=ваш_oauth_secret     # Обязательно когда OAuth включен
MCP_SERVER_PUBLIC_URL=https://ваш.сервер.com  # Обязательно когда OAuth включен
TRACKER_READ_ONLY=true                    # По умолчанию: false - Отключить все инструменты записи для всего инстанса
```

### Управление доступом к очередям

Доступ к очередям можно ограничивать на трёх уровнях — от грубого к более точному:

- **`TRACKER_LIMIT_QUEUES`** — список разрешённых ключей очередей. Очереди вне
  списка считаются *не найденными / недоступными* как для чтения, так и для записи.
  Ключи сопоставляются без учёта регистра — и здесь, и в
  `TRACKER_READ_ONLY_QUEUES`, — поэтому `dev` и `DEV` означают одну очередь.
  Единственное исключение — инструменты досок: доска принадлежит организации, а не
  очереди, поэтому они не фильтруются и могут назвать запрещённую очередь в
  настройках доски.
- **`TRACKER_READ_ONLY`** — когда `true`, все инструменты записи не регистрируются,
  и весь инстанс работает только на чтение.
- **`TRACKER_READ_ONLY_QUEUES`** — список очередей только для чтения. Инструменты
  записи остаются зарегистрированными, но любой изменяющий вызов
  (создание/обновление/перемещение/комментарий/списание времени/связь, создание
  версии очереди) к указанной очереди отклоняется, а чтение продолжает работать.
  Очереди, не указанные здесь, остаются доступными для записи.

> **Инструменты проектов, портфелей и целей в эту модель не входят.** Проект,
> портфель или цель нельзя однозначно сопоставить с одной очередью, поэтому ни
> одна из трёх настроек выше их не ограничивает — ни инструменты чтения
> (`project_get`, `project_find`, `*_get_comments`, …), ни инструменты записи
> (включая комментарии и чек-листы). Их включение даёт доступ к этим сущностям
> в рамках всей организации всем, кто может обратиться к серверу. Поэтому они
> **включаются явно**: регистрируются только при `TRACKER_ENTITIES_ENABLED=true`
> (по умолчанию `false`), что заодно уменьшает манифест инструментов для тех, кому
> они не нужны. `TRACKER_READ_ONLY` при этом продолжает действовать: он снимает
> регистрацию инструментов записи сущностей вместе со всеми остальными.

Это позволяет одному инстансу одновременно быть **доступным для записи в одни
очереди и только для чтения — в другие**: например, `TRACKER_LIMIT_QUEUES=DEV,MGMT`
вместе с `TRACKER_READ_ONLY_QUEUES=MGMT` даёт полный доступ к `DEV` и доступ
только для чтения к `MGMT`. Это особенно полезно для общего MCP-шлюза, когда
пользователи обращаются к Трекеру только через сервер и не владеют токеном напрямую.

> Эти проверки — внутренние ограничители в рамках процесса. Для клиентов, которые
> держат токен Трекера напрямую, реальные ограничения следует дополнительно
> задавать на самом токене.

## Docker развертывание

### Использование готового образа (рекомендуется)

По умолчанию образ работает с `TRANSPORT=stdio` — общение идёт через stdin/stdout контейнера,
и никакой порт не слушается. Для примеров ниже, где сервер доступен по HTTP, задайте
`TRANSPORT=streamable-http`; для stdio-клиента запускайте контейнер с `-i` и без `-p`
(см. примеры в разделе [Конфигурация MCP клиента](#конфигурация-mcp-клиента)).

```bash
# Используя файл окружения (в нём должно быть TRANSPORT=streamable-http)
docker run --env-file .env -p 8000:8000 ghcr.io/aikts/yandex-tracker-mcp:latest

# С встроенными переменными окружения
docker run -e TRACKER_TOKEN=ваш_токен \
           -e TRACKER_CLOUD_ORG_ID=ваш_org_id \
           -e TRANSPORT=streamable-http \
           -p 8000:8000 \
           ghcr.io/aikts/yandex-tracker-mcp:latest
```

### Сборка образа локально

```bash
docker build -t yandex-tracker-mcp .
```

### Docker Compose

**Используя готовый образ:**
```yaml
services:
  mcp-tracker:
    image: ghcr.io/aikts/yandex-tracker-mcp:latest
    ports:
      - "8000:8000"
    environment:
      - TRACKER_TOKEN=${TRACKER_TOKEN}
      - TRACKER_CLOUD_ORG_ID=${TRACKER_CLOUD_ORG_ID}
      - TRANSPORT=streamable-http
```

**Сборка локально:**
```yaml
services:
  mcp-tracker:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TRACKER_TOKEN=${TRACKER_TOKEN}
      - TRACKER_CLOUD_ORG_ID=${TRACKER_CLOUD_ORG_ID}
      - TRANSPORT=streamable-http
```

### Настройка для разработки

```bash
# Клонирование и настройка
git clone https://github.com/aikts/yandex-tracker-mcp
cd yandex-tracker-mcp

# Установка зависимостей для разработки
uv sync --dev

# Форматирование и статическая проверка
task
```

## Лицензия

Этот проект лицензирован в соответствии с условиями, указанными в файле [LICENSE](LICENSE).

## Поддержка

По вопросам и проблемам:
- Ознакомьтесь с документацией API Яндекс.Трекера
- Отправляйте проблемы на https://github.com/aikts/yandex-tracker-mcp/issues
