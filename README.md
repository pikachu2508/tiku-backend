# 招标代理题库 · 后端版 (tiku-backend)

> 把一个「单文件 HTML 题库」升级为「带数据库 + API 的多端同步产品」，
> 同时支持 **GitHub Pages 离线单文件版**（打开外链即用）。
>
> 原项目收录于《2025-2026 AI 年度报告 · 得到 AI 学习圈出品》第 252-261 页。

---

## 🌐 在线体验（GitHub Pages 静态版）

**打开链接即可刷题，无需注册、无需安装。**

> 外链地址（启用 GitHub Pages 后会显示在仓库首页 About 栏）：
> `https://<你的用户名>.github.io/tiku-backend/`

- ✅ 2262 道真题（单选 795 / 多选 466 / 判断 1001）
- ✅ 进度保存在本机浏览器（localStorage）
- ✅ 4 种练习模式：浏览刷题 / 闪卡 / 模拟考试 / 错题本
- ✅ 4 种主题：深色 / 浅色 / 米黄 / 护眼绿
- ✅ 单选/多选/判断题型筛选、随机顺序、只刷未做、关键词搜索

> 顶部会出现 "📦 静态模式" 提示：这是因为 GitHub Pages 跑不了 Python 后端。
> 如果你想要 **多端同步进度**（手机刷了一半、电脑继续），需要部署后端（见下）。

---

## 🚀 本地全栈版（带多端同步）

需要 Python 3.9+。

```bash
# 1. 装依赖
pip install -r requirements.txt

# 2. 导入题库
python -m backend.import_xlsx --reset

# 3. 启动后端
python -m uvicorn backend.main:app --port 8000
```

或 Windows 用户直接**双击 `start.bat`**，自动装依赖 + 导入 + 启动 + 打开浏览器。

打开后访问：
- 前端：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/docs
- 顶部会显示 "☁️ 后端已连接 · 进度云端同步"

> 后端启动后，无论你在自己电脑哪个浏览器、哪个设备打开，只要带同一 device_id（首次自动生成，存 localStorage），进度都能同步。

---

## 🏗️ 架构

```
浏览器 (frontend/index.html + questions.json, 36 KB + 1 MB)
   ↕  HTTP / JSON  (有后端时)
FastAPI 后端 (backend/, Python)
   ↕  SQLAlchemy
SQLite 数据库 (backend/quiz.db, 2262 题)

GitHub Pages 部署时:
   ↕  不连后端,仅用 frontend/ 静态资源
   ↕  进度走 localStorage(单机模式)
```

**两种使用模式自动切换**：浏览器启动时先试 `/api/all/legacy`，2.5 秒内连不上就降级到本地 `frontend/questions.json`。

---

## 📁 项目结构

```
tiku-backend/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── database.py          # SQLite 连接
│   ├── models.py            # 4 张表(Question/User/Attempt/Progress)
│   ├── schemas.py           # Pydantic 数据契约
│   ├── import_xlsx.py       # Excel → SQLite 导入
│   ├── quiz.db              # SQLite 数据库(运行后生成,gitignore)
│   └── routers/
│       ├── users.py         # device_id 免登录
│       ├── questions.py     # 题库(含 legacy 格式适配)
│       ├── progress.py      # 答题 / 进度 / 错题本
│       └── explanations.py  # AI 解析(预留)
├── frontend/
│   ├── index.html           # 改造后的前端(36 KB,自动降级离线模式)
│   └── questions.json       # 2262 题题库(1 MB,GitHub Pages 用)
├── data/
│   └── 招标代理2025考试题库.xlsx   # 数据源(原始,gitignore,导入用)
├── requirements.txt
├── start.bat                # Windows 一键启动
├── .gitignore
└── README.md
```

---

## 🔌 API 速览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| GET | `/api/questions/stats/overview` | 题库总览 |
| GET | `/api/questions/all/legacy` | 一次性全量题(前端首屏用) |
| GET | `/api/questions` | 分页/筛选/随机 |
| GET | `/api/questions/{id}` | 单题 |
| POST | `/api` | 注册/取用户(device_id) |
| POST | `/api/progress/submit` | 提交作答(写流水+更新汇总) |
| GET | `/api/progress/summary` | 进度概览 |
| GET | `/api/progress/wrong` | 错题本 |
| GET/POST | `/api/explanations/{id}` | AI 解析(当前为占位) |

完整 Swagger 文档：启动后端后访问 `/docs`。

---

## 🛣️ 迭代路线图

### 本次完成(v4.2 → 后端版)
- ✅ 题库数据从 HTML 抽离到数据库(HTML 1 MB → 36 KB + SQLite)
- ✅ 后端 API 全栈
- ✅ 多端同步内核(device_id 体系)
- ✅ GitHub Pages 离线降级模式(打开外链即用)
- ✅ 浅色主题配色优化(对比度、可读性、tag/答案区视觉)

### 下一步(对应原报道第 259 页)
- 🔴 **AI 智能解析**:数据库 `explanation` 字段已预留,接口就位,接 / API 即可
- 🔴 **真后端部署上云**:Cloudflare Workers + D1(零成本),SQLite → D1 几乎零改动
- 🟡 **屏幕阅读优化**
- 🟡 **大学场景迁移**:把模板复用到大学课程题库

---

## 📰 项目背景

2025 年 9 月,作者(范翔宇,福建师范大学物理学 2025 级)用 ChatGPT 把朋友备考
「省级招标代理考试」的 2200+ 道 Excel 题库,做成了单文件 HTML 交互刷题工具——
3-4 小时交付,朋友备考周期从 2 周缩到 1 周,成绩 A+。

这个仓库是**第一次大迭代**:
- 把题库搬进数据库,加上后端 API
- 进度可以在手机/电脑/平板之间同步(多端同步)
- 同时也支持纯静态部署(GitHub Pages),让作品集分享有外链

原项目收录:《2025-2026 AI 年度报告 · 得到 AI 学习圈出品》第 252-261 页
(范翔宇 / 案例 No.21)。

---

## 🧑‍💻 关于本仓库

- **作者**:范翔宇(微信公众号「AI实干家咚咚嗒」,得到知识城邦 @皮卡丘咚咚嗒)
- **协议**:MIT(题库数据来源除外——见 `data/` 下的 .xlsx 源)
- **致谢**:慕云(@慕云灬,题库需求方与协作者)
