# LLBot — 设计契约 / 升级流程 / 改动记录

> LLBot 是 Hermes 的 QQ 平台插件（OneBot v11 over forward WebSocket，LLOneBot 变体）。
> 本文件是 llbot 的**单一事实来源**：消息处理契约、配置、镜像/媒体处理、以及配套的
> memory provider 与 fork/升级工作流。改 llbot 前先读这里；改了行为就更新这里。

关联文件：`adapter.py`（I/O + 事件编排）、`onebot.py`（纯协议/序列化）、`plugin.yaml`、
`tests/gateway/test_llbot_adapter.py`（行为锁）、`docs/`（上游 OneBot v11 参考协议文档）。

---

## 1. 消息处理契约（inbound → event）

### 触发（dispatch）vs 观察（observe）
- 群聊 `require_mention`（默认 true）：`@bot` / `@全体成员` 触发；**唤醒词**（`wake_words`，
  默认 `Arona,阿罗娜`）等同 @ 触发；否则若该群在 `observe_allowed_chats` 且 `observe_unmentioned`
  则进**观察缓冲**，否则丢弃。
- 私聊：`dm_allow_from` 白名单放行。
- **戳一戳（poke）**：仅当 `target_id == self_id`（戳的是 bot）才触发；走与消息**相同**的上下文流程。

### 观察缓冲（background）
- 每条观察行：`[HH:MM:SS 时间戳] [昵称 (QQ N)] <内容>`，滚动缓冲上限 `observe_max_messages`（默认 50）。
- drain（触发时清空一次）渲染为 **【背景消息开始 …】…【背景消息结束】** 围栏块；末尾 **`[now: <触发时间>]`**
  在围栏**外**、紧贴 `[New message]`。无观察时只发 `[now:]`，不加围栏。
- 背景图片**不原生附着**：`[背景图N: <一句话中文caption>]`（receive 时异步 describe，走
  `async_call_llm(task="vision")` auto→主模型；失败/未就绪→`[背景图N]`）+ 末尾**路径图例**
  `背景图N: <缓存路径>`（agent 要细看时自行 `vision_analyze(image_url=<path>)`）。
  开关 `observe_describe_images`（默认 true）。

### 引用消息（reply-quote）
- 出站 `get_msg` 取被引用原文，按**原始顺序**渲染（text/图片交错）。**置 `reply_to_text=None`**
  让 gateway 跳过默认 `[Replying to:]` 包装，改由 adapter 把**【用户回复了这条消息 …】…【引用消息结束】**
  围栏块追加到 channel_context（`[now:]` 之后、紧贴 `[New message]`），使 agent 把它当上下文而非指令。
- `reply_to_message_id` 保留给出站回复用。
- **引用里的文件/语音**：因 quote 的 segments 来自触发时刻**新鲜的 `get_msg`**（URL 未过期），
  触发时 `_render_ordered(..., resolve_files=True)` **下载**并在 marker 内给出缓存路径——
  `[文件:name → <缓存路径>]`、`[语音: <音频已缓存…> <缓存路径>]`，agent 用 `read_file` 读内容。
  文件/语音**不原生附着**（不进 `media_urls`），只给路径；下载失败回退为裸 `[文件:name]`/`[语音]`。
  背景消息里的文件**不下载**（可能很大），仅 `[文件:name]`。

### 图片标记两个命名空间（关键，别混）
| 命名空间 | 含义 | 处理 |
|---|---|---|
| `[输入图片N]` | **输入图**：own 触发图（N=1..K，标注在 body）→ 引用图（K+1..，标注在引用围栏） | **原生附着** `media_urls`，agent 直接看到像素 |
| `[背景图N: <caption>]` | **背景图**：observe 里的图 | **不附着**，文字 caption + 路径图例（按需 `vision_analyze`） |

### 触发消息里的 @ 信号
`[昵称 (QQ N) @你]` / `[昵称 (QQ N) @全体成员]` / `[昵称 (QQ N) 提到了你]`（唤醒词）注入 body。
gateway 还会给共享群会话加发言者前缀 `[昵称]`（name-only，run.py:8820）——所以名字会出现两次，QQ 在 mention note 里。

### poke
`[戳一戳] {name} 戳了戳你`，上下文与消息触发一致（drain 观察 + `[now:]` + 背景图），仅文本不同。

---

## 2. 出站（send / send_message）

- 短回复：`send_group_msg` / `send_private_msg`（`truncate_message` 分块，4000 字上限）。
- **合并转发（forward）**：群聊 + `forward_enabled` + 文本 > `forward_limit`（默认 800）→
  `send_group_forward_msg`，按句号（中`。`/英`.`+空白）贪心切 ≤limit 节点。
  DM 不转发；转发失败回退普通分块发送。
- **outbound [CQ:at]**：出站文本里的 `[CQ:at,qq=N]`（或 `qq=all`）经 `parse_cq_outbound`
  切成**结构化 at 段**（QQ 群里才是真 @）。非 at 的 `[CQ:...]` 保持字面文本（模型控制不了媒体）。
  platform_hint 教模型 `@mention someone with [CQ:at,qq=<number>]` —— 现已兑现。
- **媒体**：`send_image_file` / `send_voice` / `send_document`；`send_message` 里 `MEDIA:<path>` 经
  `_send_llbot_via_adapter` 走同一 adapter。
- **运维状态改道**：adapter 实现 `send_or_update_status`——gateway 的状态类消息（`⚠` 压缩失败等 warn/info/progress）
  被改道到 `status_channel`（`private:<qq>` 或 `group:<id>`，前缀 `[运维告警·<来源群>]`）；未配置/格式错则吞掉
  （群聊干净，告警仍在 gateway 日志）。**真实回复走 `send()`，不受影响**。

---

## 3. 配置 knobs（`gateway.platforms.llbot.extra` 或 `LLBOT_*` env）

| key | env | 默认 | 说明 |
|---|---|---|---|
| `ws_url` | `LLBOT_WS_URL` | — | LLBot forward WS，如 `ws://127.0.0.1:3001` |
| `access_token` | `LLBOT_ACCESS_TOKEN` | — | 仅当 llbot 设了 token |
| `require_mention` | `LLBOT_REQUIRE_MENTION` | true | 群需 @ 才触发 |
| `group_allow_from` / `allow_from` | `LLBOT_ALLOWED_GROUPS` / `LLBOT_ALLOWED_DMS` | 空 | 群/私聊白名单（纯 id） |
| `wake_words` | `LLBOT_WAKE_WORDS` | `Arona,阿罗娜` | 唤醒词 regex 列表 |
| `observe_unmentioned` | `LLBOT_OBSERVE_UNMENTIONED` | false | 开启 observe |
| `observe_allowed_chats` | `LLBOT_OBSERVE_ALLOWED_CHATS` | 空 | observe 白名单（bare 群号或 `group:<id>`） |
| `observe_max_messages` | `LLBOT_OBSERVE_MAX_MESSAGES` | 50 | observe 缓冲上限 |
| `observe_describe_images` | `LLBOT_OBSERVE_DESCRIBE_IMAGES` | true | 背景图 describe 开关 |
| `forward_enabled` / `forward_limit` / `forward_sender_name` | `LLBOT_FORWARD_*` | true / 800 / Hermes | 合并转发 |
| `status_channel` | `LLBOT_STATUS_CHANNEL` | 空 | 运维告警改道目标（`private:<qq>`/`group:<id>`） |
| `shared_media_host_dir` / `shared_media_container_dir` | `LLBOT_SHARED_MEDIA_*` | 空 | Docker 共享卷路径映射 |

**别动**：trigger/quote 原生附着与 `[输入图片N]` 编号、合并转发、poke target guard、timestamps/`[now:]`、
`channel_prompt`/`platform_hint` 其余部分、eager-cache 时机、`onebot.py` 纯协议、core。

---

## 4. 配套 memory provider（session-key 隔离）

`plugins/memory/session-key-{hindsight,mem0,supermemory}` —— 把 memory 的 **bank_id/scope 绑定到
gateway session_key**，实现**按 chat 隔离**：群共享 session 时整群一个记忆域（跨群隔离）；
per-user-per-group 时按人隔离。均 subclass 内置 provider，仅覆盖 bank 解析。

---

## 5. Fork / 升级工作流（防止 hermes update 丢提交）

llbot 提交在本地 `main`，origin = `NousResearch/hermes-agent`（无写权限），fork =
`cxnaive/hermes-agent-llbot`（备份）。

**为什么不用 `hermes update`**（conda 环境下）：
- 内部 `git pull --ff-only`；本地有提交与 origin 分叉时必然失败 → 直接 `git reset --hard origin/main`
  **丢弃本地 llbot 提交**（main.py:8819-8831）。
- 依赖安装强制 `VIRTUAL_ENV=<项目>/venv`（main.py:8949），conda 环境会装错地方。

**推荐流程（手动 rebase，已验证多次）**：
```bash
git fetch origin
git rebase origin/main                      # 重放 llbot 提交；冲突仅可能在 tools/send_message_tool.py
/home/bot/miniconda3/envs/hermes/bin/pip install -e .   # conda 装依赖（跳过 update 的 venv 误装）
find . -name __pycache__ -type d -prune -exec rm -rf {} +
/home/bot/miniconda3/envs/hermes/bin/python -m pytest tests/gateway/test_llbot_adapter.py -q
hermes config migrate                        # 若有版本迁移（启动时也会自动提示）
hermes gateway restart
```
**冲突提示**：llbot 提交几乎只碰 `plugins/platforms/llbot/*` + `plugins/memory/session-key-*`（上游不碰），
唯一反复冲突点是 `tools/send_message_tool.py`——上游会加别的平台（slack/whatsapp…）媒体分支，
和 llbot 媒体分支相邻。**解法：两个独立 `if platform == X:` 分支都保留**，各带自己的 chunk 循环 + return。
**推送**：rebase 改写 SHA → 推 fork 需 `git push --force-with-lease=main:<fork当前SHA> <fork-url> main`。

### 推 fork（脚本化，推荐）
PAT 存于 **`.env.fork-push`**（已 gitignore，**永不提交**）：
```bash
FORK_PUSH_TOKEN=ghp_xxx
FORK_PUSH_USER=cxnaive
```
推送一律跑脚本（自动 force-with-lease 对准 fork 当前 main，防误覆盖；rebase 改写 SHA 后也安全）：
```bash
./scripts/push-fork.sh          # main → fork
./scripts/push-fork.sh <分支>   # 指定分支
```
**别把 PAT 粘到命令行**（会留在 shell history）；脚本从文件读，不落 history。PAT 泄露 → 立即在
GitHub → Settings → Developer settings → Tokens 撤销并换新的。

---

## 6. 改动记录（llbot 提交链，最新在前）

| 提交 | 改动 |
|---|---|
| `474393266` | 出站 `[CQ:at,qq=N]` → 结构化 at 段（真 @） |
| `2a52ddda7` | 引用围栏移入 channel_context（置空 reply_to_text，去掉 `[Replying to:]` 壳） |
| `11268e9f7` | 引用消息 `【】` 围栏（上下文非指令） |
| `b64122458` | `connect()` 接受 `is_reconnect`（对齐上游 base） |
| `be92dea7d` | mention note 带 QQ（`昵称 (QQ id)`）+ 运维状态改道 `status_channel`（`send_or_update_status`） |
| `a370c6ad4` | observe 背景图 describe 成文字 + 路径图例 + 背景围栏（不再原生附着） |
| `1a958d4e0` | llbot 平台（OneBot v11）+ session-key memory + 群聊增强（observe/quote/poke/forward） |

---

## 7. 测试 / 验证

- 单测：`/home/bot/miniconda3/envs/hermes/bin/python -m pytest tests/gateway/test_llbot_adapter.py -q`（当前 121 全绿）。
- 导入：`python -c "import plugins.platforms.llbot.adapter"`。
- 端到端：QQ 群触发观察/引用/@、长回复合并转发、`[CQ:at]` 真 @、运维告警改道 `status_channel`。
