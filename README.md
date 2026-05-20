# Personal AI Secretary

## English Version

### Overview

Personal AI Secretary is a mobile-first AI productivity assistant.

The goal is to let the user talk to an AI secretary in natural language. The app extracts tasks, fixed events, schedule changes, and review information from the conversation, then helps arrange the user's daily plan.

This project is currently an MVP. It is designed for personal and family use, especially for students who need help managing study tasks, technical projects, exams, appointments, routines, and daily reviews.

### Main Features

- Chat-first daily planning
- Natural language schedule adjustment
- Today's plan view
- Future plan support
- Plan item editing and deletion
- Plan item status management
- Daily review workflow
- Local memory and plan storage
- English and Chinese interface
- User-configurable model provider, model name, API key, and base URL
- PWA foundation with manifest, icons, and service worker

### Current Architecture

```text
React / Vite frontend
        |
        v
FastAPI backend
        |
        v
LLM provider API
        |
        v
Local JSON storage
```

The current version still needs the backend to be running. If the backend is running on your computer, the app will stop working when the computer is turned off.

### Tech Stack

Frontend:

- React
- Vite
- JavaScript
- CSS
- PWA manifest and service worker

Backend:

- Python
- FastAPI
- Uvicorn
- Pydantic
- OpenAI-compatible SDK usage
- JSON file storage

### Project Structure

```text
Secretary/
├── backend/
│   ├── main.py
│   ├── planner.py
│   ├── prompts.py
│   ├── schemas.py
│   ├── memory.py
│   ├── model_settings.py
│   ├── llm_client.py
│   ├── config.py
│   ├── requirements.txt
│   └── data/
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   │   ├── manifest.webmanifest
│   │   ├── sw.js
│   │   └── icons/
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       ├── i18n.js
│       ├── pwa.js
│       ├── styles.css
│       └── components/
│
├── docs/
│   ├── chat_first_design.md
│   ├── memory_design.md
│   ├── model_settings_design.md
│   └── pwa_phone_install.md
│
└── README.md
```

### Run the Backend

Using the project's conda environment:

```powershell
cd D:\university\Robot\Secretary\backend
D:\Anaconda3\envs\Secretary\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then test:

```text
http://localhost:8000/
```

Expected response:

```json
{
  "message": "Personal AI Secretary backend is running."
}
```

### Run the Frontend

```powershell
cd D:\university\Robot\Secretary\frontend
npm install
npm run dev -- --host 0.0.0.0
```

On the same computer:

```text
http://localhost:5173
```

On a phone in the same local network:

```text
http://YOUR_COMPUTER_IP:5173
```

Example:

```text
http://192.168.1.107:5173
```

### Environment Variables

Backend `.env` example:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

The app also supports model settings inside the UI. Users can set their own provider, model, API key, and base URL.

Do not commit real API keys to GitHub.

### GitHub Safety Notes

The following files are intentionally ignored:

```text
.env
backend/data/settings.json
backend/data/history.json
backend/data/memory.json
node_modules/
dist/
__pycache__/
```

This helps prevent private keys, local settings, dependencies, and build output from being uploaded.

### PWA Notes

The project includes PWA files:

- `frontend/public/manifest.webmanifest`
- `frontend/public/sw.js`
- `frontend/public/icons/`
- `frontend/src/pwa.js`

However, a fully installable PWA usually requires HTTPS. A local LAN URL such as `http://192.168.1.107:5173` may only support "Add to Home screen" as a shortcut.

### Future Roadmap

- Improve mobile UI polish
- Improve Chinese experience for family users
- Add stronger local-first storage
- Convert the app into a local-first mobile app
- Package the frontend with Capacitor
- Move backend logic to the mobile side where possible
- Build an Android APK
- Let each user store their own API key on their own device
- Reduce or remove the need for a personal server

---

## 中文版本

### 项目简介

Personal AI Secretary 是一个手机优先的个人 AI 秘书应用。

这个项目的目标是：用户不需要填写复杂表单，只需要像和真人秘书聊天一样，用自然语言告诉 AI 自己要做什么。AI 会从对话中提取任务、固定事项、时间变化和复盘信息，然后帮助用户安排每天的计划。

目前这个项目还是 MVP 版本，主要用于个人和家人测试。它特别适合学生管理学习任务、技术项目、考试、约会、日常安排和每日复盘。

### 主要功能

- 聊天式每日计划
- 自然语言调整日程
- 今日计划展示
- 支持未来日期计划
- 支持编辑和删除单个计划项
- 支持标记计划项状态
- 每日复盘
- 本地记忆和计划存储
- 中英文界面切换
- 用户可以配置自己的模型服务商、模型名、API key 和 Base URL
- 已加入 PWA 基础文件，包括 manifest、图标和 service worker

### 当前架构

```text
React / Vite 前端
        |
        v
FastAPI 后端
        |
        v
大模型 API
        |
        v
本地 JSON 存储
```

当前版本仍然需要后端运行。如果后端运行在你的电脑上，那么电脑关机后，手机上的应用就无法继续正常使用。

### 技术栈

前端：

- React
- Vite
- JavaScript
- CSS
- PWA manifest 和 service worker

后端：

- Python
- FastAPI
- Uvicorn
- Pydantic
- OpenAI-compatible API 调用方式
- JSON 文件存储

### 项目结构

```text
Secretary/
├── backend/
│   ├── main.py
│   ├── planner.py
│   ├── prompts.py
│   ├── schemas.py
│   ├── memory.py
│   ├── model_settings.py
│   ├── llm_client.py
│   ├── config.py
│   ├── requirements.txt
│   └── data/
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── public/
│   │   ├── manifest.webmanifest
│   │   ├── sw.js
│   │   └── icons/
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       ├── i18n.js
│       ├── pwa.js
│       ├── styles.css
│       └── components/
│
├── docs/
│   ├── chat_first_design.md
│   ├── memory_design.md
│   ├── model_settings_design.md
│   └── pwa_phone_install.md
│
└── README.md
```

### 启动后端

使用项目的 conda 环境：

```powershell
cd D:\university\Robot\Secretary\backend
D:\Anaconda3\envs\Secretary\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

测试后端：

```text
http://localhost:8000/
```

正常结果：

```json
{
  "message": "Personal AI Secretary backend is running."
}
```

### 启动前端

```powershell
cd D:\university\Robot\Secretary\frontend
npm install
npm run dev -- --host 0.0.0.0
```

电脑上访问：

```text
http://localhost:5173
```

同一局域网下，手机访问：

```text
http://你的电脑IP:5173
```

例如：

```text
http://192.168.1.107:5173
```

### 环境变量

后端 `.env` 示例：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

应用里也支持在界面中配置模型。用户可以设置自己的服务商、模型、API key 和 Base URL。

不要把真实 API key 上传到 GitHub。

### GitHub 备份注意事项

以下文件已经被忽略，不建议上传：

```text
.env
backend/data/settings.json
backend/data/history.json
backend/data/memory.json
node_modules/
dist/
__pycache__/
```

这样可以避免把密钥、本地模型设置、依赖文件和构建产物上传到 GitHub。

### PWA 说明

项目已经加入 PWA 基础文件：

- `frontend/public/manifest.webmanifest`
- `frontend/public/sw.js`
- `frontend/public/icons/`
- `frontend/src/pwa.js`

但是，一个完整可安装的 PWA 通常需要 HTTPS。像 `http://192.168.1.107:5173` 这样的局域网地址，可能只能添加为桌面快捷方式，不一定能作为完整 PWA 安装。

### 后续路线

- 继续优化手机端 UI
- 继续优化中文体验，方便父母使用
- 强化本地优先存储
- 逐步改造成本地优先的手机 App
- 使用 Capacitor 打包前端
- 尽量把后端逻辑迁移到手机本地
- 生成 Android APK
- 让每个用户在自己手机上保存自己的 API key
- 减少甚至取消对个人服务器的依赖
