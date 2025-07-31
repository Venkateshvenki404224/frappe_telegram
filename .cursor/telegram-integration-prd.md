# 📄 Product Requirements Document (PRD): Telegram Bot Integration for Frappe

## 🧩 Purpose

The goal is to integrate Telegram Bot functionality into a Frappe application that allows managing multiple bots (development and production), sending messages (one-way/broadcast) to Telegram users and groups, and logging all interaction metadata in a structured, scalable way.

---

## 🏗️ Modules Overview

### Existing Doctypes:

* **TelegramBot**: Defines Bot token, name, environment (dev/prod), webhook status, etc.
* **TelegramBotItems**: (Assumed) Related settings or resources per Bot.
* **TelegramChat**: Represents individual chat instances (user or group).
* **TelegramMessage**: Represents individual sent/received messages.
* **TelegramMessageTemplate**: Message templates with variables/placeholders.
* **TelegramUserDoctype**: Maps Telegram user with Frappe User/Doctype.
* **TelegramUserItem**: Sub-data for Telegram user (assumed preferences, tags, etc.).

---

## 🔍 Functional Requirements

### 1. **Bot Environment & Management**

| Feature              | Description                                                                                    |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| Multi-Bot Support    | Allow multiple bots to be registered (`TelegramBot`), tagged as `Development` or `Production`. |
| Token Validation     | Automatically validate bot token via Telegram API before saving.                               |
| Webhook Management   | Add buttons to `TelegramBot` to register/unregister webhooks.                                  |
| Active Bot Indicator | Only one bot per environment can be `active`.                                                  |

---

### 2. **Chat & User Sync**

| Feature       | Description                                                                               |
| ------------- | ----------------------------------------------------------------------------------------- |
| Chat Tracking | Automatically capture chat metadata (ID, type, title) when a message is received or sent. |
| User Mapping  | Link `TelegramChat` to a `TelegramUserDoctype` if matched.                                |
| Sync Fields   | Store basic user info: `first_name`, `last_name`, `username`, `language_code`.            |

---

### 3. **Messaging & Notification System**

| Feature                 | Description                                                     |
| ----------------------- | --------------------------------------------------------------- |
| Template-Based Messages | Use `TelegramMessageTemplate` with Jinja for dynamic rendering. |
| Group Messaging         | Ability to send broadcast messages to group chats from a bot.   |
| One-on-One Messages     | Allow sending messages to individual users.                     |
| Message Queue           | All outgoing messages go through a Frappe Queue/Background Job. |
| Message Logging         | Store full message object in `TelegramMessage` for auditing.    |
| Status Tracking         | Each message should track `status`: Queued, Sent, Failed.       |

---

### 4. **Webhook Message Receiver**

| Feature         | Description                                                                                        |
| --------------- | -------------------------------------------------------------------------------------------------- |
| Endpoint        | Auto-create webhook routes (e.g., `/api/method/telegram_bot.receive_message`) for each active bot. |
| Event Handling  | All received messages are saved in `TelegramMessage`.                                              |
| Command Parsing | If text starts with "/", classify as command and route internally via hookable dispatcher.         |

---

### 5. **Command Handler (Optional Feature)**

| Feature               | Description                                                                         |
| --------------------- | ----------------------------------------------------------------------------------- |
| Dynamic Command Map   | Define command-action mapping per bot via child table or JSON config.               |
| Trigger Frappe Method | Each command triggers a server-side method (e.g., `/start` → `start_user_session`). |

---

### 6. **Security & Permissions**

| Feature         | Description                                                  |
| --------------- | ------------------------------------------------------------ |
| RBAC            | Only permitted users can manage bots and view messages.      |
| Auth Validation | Ensure webhooks are only accessible via token-secured paths. |
| IP Restriction  | (Optional) Restrict webhook calls to Telegram IPs only.      |

---

## 🧰 Technical Components

| Component              | Description                                                           |
| ---------------------- | --------------------------------------------------------------------- |
| `telegram_bot.py`      | Class-based handler for sending/receiving messages, setting webhooks. |
| `WebhookController`    | REST controller to route Telegram API payloads.                       |
| `MessageDispatcher`    | Command parser that dynamically calls appropriate server method.      |
| `BackgroundJobManager` | Queue and retry failed messages via Redis/Worker.                     |

---

## 🧪 Development vs Production Bot Behavior

| Mode        | Behavior                                                                          |
| ----------- | --------------------------------------------------------------------------------- |
| Development | Console logging only, webhook logs, test message mode, limited user scope.        |
| Production  | Full messaging enabled, error notifications, retry mechanism for failed messages. |

---

## 🗂️ Doctype Relationships (Entity Map)

```
TelegramBot (1) → (N) TelegramBotItems  
TelegramBot (1) → (N) TelegramMessage  
TelegramChat (1) → (N) TelegramMessage  
TelegramChat (1) → (1) TelegramUserDoctype  
TelegramUserDoctype (1) → (N) TelegramUserItem  
TelegramMessageTemplate (1) → (N) TelegramMessage  
```

---

## ⏳ Future Enhancements

* Inline Button & Menu Support
* Media/Document Uploads
* Bi-directional Chat Dashboard in Frappe
* Group Role Mapping and Notifications
* Auto-reply flows (like bots for feedback collection, status queries)

