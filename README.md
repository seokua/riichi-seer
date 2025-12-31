# 🀄 Riichi Seer - 雀魂 AI 复盘助手

一个高性能的 Discord 机器人，专为雀魂（Mahjong Soul）玩家提供 AI 复盘分析服务。支持热重载、多模型切换及自动统计恶手。

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/seokua/riichi-seer)
[![Discord](https://img.shields.io/badge/Discord-Join%20Server-7289da?logo=discord)](https://discord.gg/T55uJDw3)

## ✨ 功能特性

- **核心复盘**：提交雀魂牌谱链接，AI 自动下载并生成 Rating、一致率及恶手统计报告。
- **混合命令**：完美支持传统前缀命令 `!` 和现代斜杠命令 `/`。
- **热重载系统**：监听 `cogs/` 和 `.env` 文件，无需重启机器人即可更新逻辑和配置。
- **多模型切换**：根据对局类型（三麻/四麻）自由选择后端支持的 AI 模型。
- **多级缓存**：牌谱数据与分析结果本地持久化，秒级响应重复查询。

## 🎮 在线试用

我们在 Discord 部署了该服务的演示实例，欢迎加入体验：
👉 [Riichi Seer 官方服务器](https://discord.gg/T55uJDw3)

## 🚀 快速开始 (Docker 部署)

这是最推荐的部署方式，能够确保环境一致性并支持持久化存储。

### 1. 克隆项目

```bash
git clone https://github.com/seokua/riichi-seer.git
cd riichi-seer
```

### 2. 配置环境变量

从模板创建 .env 文件并填入你的配置：

```
cp .env.example .env
```

关键配置说明：

- DISCORD_TOKEN: 你的机器人 Token。

- TENSOUL_URL: 牌谱解析服务地址（需包含 ?id=）。

- REVIEW_BASE_URL: AI 复盘分析后端地址。

- PAIPU_CACHE_DIR: 牌谱数据本地缓存目录。

### 3. 使用 Docker Compose 启动

```
docker compose up --build -d
```

## 📖 命令手册

| 命令 | 参数 | 描述 |
|------|------|------|
| `!review` | `<URL> [Actor] [Model]` | 提交复盘。Actor 为座位号(0-3)。 |
| `!models` | 无 | 列出当前后端支持的所有 AI 模型。 |

## 系统功能 (General)

| 命令 | 参数 | 描述 |
|------|------|------|
| `!ping` | 无 | 查看机器人延迟。 |
| `!help` | `[Plugin]` | 动态生成的交互式帮助文档。 |


## 📂 项目结构

```
riichi-seer/
├── main.py           # 入口程序：包含机器人初始化与文件监听逻辑
├── cogs/             # 插件目录
│   ├── general.py    # 基础命令
│   └── review.py     # 雀魂 AI 分析核心逻辑
├── cache/            # 挂载卷：持久化存储缓存数据
├── Dockerfile        # 镜像定义
├── docker-compose.yml # 容器编排
└── requirements.txt  # Python 依赖
└── usage.sh          # docker commands
```

## 🛠️ 技术栈

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API 封装

- [aiohttp](https://github.com/aio-libs/aiohttp) - 异步 HTTP 请求处理

- [watchdog](https://github.com/gorakhargosh/watchdog) - 文件系统实时监听

## ⚠️ 注意事项

1. 权限设置：请确保 Bot 拥有 Send Messages 和 Embed Links 权限。

2. 斜杠命令：首次部署后，斜杠命令可能需要一定时间进行全局同步。

3. API 地址：请确保 .env 中的 API 地址是可直接访问的。

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request！如果有任何使用上的问题，欢迎在 GitHub 或 Discord 服务器中提出。