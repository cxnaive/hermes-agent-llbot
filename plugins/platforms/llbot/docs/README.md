# LLBot API 文档归档

本目录归档了 LLBot(LuckyLilliaBot,实现为 **LLOneBot**)的 OneBot v11 协议文档,作为
`plugins/platforms/llbot/adapter.py` 实现的协议参考。文档为只读归档,不参与运行时。

- **来源**:`https://api.luckylillia.com/llms.txt`(索引)+ 其链接的 `doc-` / `api-` / `schema-` 子页
- **抓取日期**:2026-06-14
- **格式**:原始 `.md`(多数为 OpenAPI 3.0.1 YAML 片段)
- **协议变体**:LLBot 的 OneBot v11 是 LLOneBot 实现,在标准 OneBot v11 之上有自定义扩展
  (见下方「LLBot 相对标准 OneBot v11 的差异」)

## 文档清单

### 索引
- `llms.txt` — 完整文档索引(原文)

### 概念
- `overview.md` — OneBot 11 接口总览(`doc-7202281`)
- `http.md` — HTTP 调用 / 接收消息(`doc-5416163`)
- `websocket.md` — WebSocket 发送 / 接收消息(`doc-5416167`)← 本适配器所用传输
- `token.md` — Token 鉴权(`doc-7948595`,`Authorization: Bearer`)

### 发送 API(对应 `adapter.send` / `send_image` / `send_voice` / `send_document`)
- 群聊:`api-send-group-{text,reply,at,image,text-image,voice,video,forward}.md`
- 私聊:`api-send-private-{text,reply,image,voice,video,forward}.md`

### 获取 / 系统 API(对应 `_resolve_*` / `get_chat_info`)
- `api-get-msg.md` — 获取消息详情(`get_msg`)
- `api-delete-msg.md` — 撤回消息(`delete_msg`)
- `api-get-image.md` / `api-get-record.md` / `api-get-file.md` — 媒体解析
- `api-get-version.md` — 版本信息(用于版本门控 API 探测)
- `api-sse-receive.md` — 长连接接收消息(HTTP SSE)
- `api-send-poke.md` — 发送戳一戳(LLBot 7.11.3+)
- `api-set-input-status.md` — 设置输入状态(LLBot 7.12.3+,打字指示)

### 事件 schema(对应 `_dispatch_event` / `_handle_inbound_message`)
- `schema-message-event.md` — MessageEvent(`post_type=message`)⭐ 核心
- `schema-poke-event.md` — PokeEvent(`post_type=notice, sub_type=poke`)⭐
- `schema-heartbeat-event.md` — 心跳(`meta_event_type=heartbeat`)
- `schema-lifecycle-event.md` — 生命周期(`meta_event_type=lifecycle, sub_type=connect`)
- `schema-message-sender.md` — MessageSender(`sender` 对象)
- `schema-group-recall-notice.md` — 群消息撤回通知

### 消息段 schema(对应 `onebot.parse_message` / segment 构造)
- `schema-message-segment.md` — 所有 segment 类型的判别联合 ⭐
- `schema-text-segment.md` / `schema-image-segment.md` / `schema-record-segment.md` /
  `schema-file-segment.md` / `schema-at-segment.md` / `schema-reply-segment.md` — v1 支持
- `schema-video-segment.md` / `schema-poke-segment.md` / `schema-node-segment.md` /
  `schema-forward-segment.md` / `schema-keyboard-segment.md` — 参考(二期/未实现)

## LLBot 相对标准 OneBot v11 的差异(实现要点)

1. **`post_type: "message_sent"`** — LLBot 会上报 bot 自己发出的消息;适配器必须按 `post_type`
   过滤,否则会形成回环。见 `adapter._dispatch_event`。
2. **额外 MessageEvent 字段** — `message_seq`、`real_id`(`get_msg` 返回)、`message_format`
   (`"array"` 为主,`"string"` 为 CQ 码)、`temp_source`、`target_id`、`font`。
3. **额外 segment 类型** — `markdown`、`keyboard`(按钮板)、`mface`(商城表情)、`poke`、`dice`、
   `rps`、`contact`、`shake`、`flash_file`(闪传文件),以及 `node` 同时兼容 OneBot11
   (`user_id`/`nickname`)与 go-cqhttp(`name`/`uin`)字段。
4. **额外事件** — `GroupDismissEvent`、`ProfileLikeEvent`、`EssenceEvent`、
   `GroupMsgEmojiLikeEvent`、`GroupUploadNoticeEvent`、`FlashFileEvent`、`PokeRecallEvent`。
5. **响应包** — 在 `status/retcode/data/message` 之外多一个 `wording`(人类可读错误)字段。
6. **`app_name`** — 上报为 `"LLOneBot"`(非 `"llbot"`),`protocol_version: "v11"`。
7. **版本门控 API** — `send_poke`(7.11.3+)、`set_input_status`(7.12.3+)、群相册/批量踢出等;
   可用 `get_version_info`(`api-get-version.md`)探测 `app_version`。
8. **`Milky` / `Satori`** — 文档中另有两套独立协议,**与本 OneBot v11 适配器无关**,已从归档中排除。

## 重新抓取

```bash
# 索引
curl -sSL https://api.luckylillia.com/llms.txt -o docs/llms.txt
# 子页 URL 见 docs/llms.txt(形如 doc-XXXX.md / api-XXXX.md / schema-XXXX.md)
```

文档站若改版导致 `doc-` / `api-` / `schema-` 编号变化,以 `llms.txt` 索引为准重新映射。
