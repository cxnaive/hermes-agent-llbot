# GroupRecallNoticeEvent

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths: {}
components:
  schemas:
    GroupRecallNoticeEvent:
      type: object
      required:
        - time
        - self_id
        - post_type
        - notice_type
        - group_id
        - user_id
        - operator_id
        - message_id
      properties:
        time:
          type: integer
          description: 事件时间戳（Unix 时间戳，秒）
          examples:
            - 1640995200
        self_id:
          type: integer
          description: 机器人的 QQ 号
          examples:
            - 123456789
        post_type:
          type: string
          enum:
            - notice
          description: 事件类型
        notice_type:
          type: string
          enum:
            - group_recall
        group_id:
          type: integer
          description: 群号
        user_id:
          type: integer
          description: 原消息发送者
        operator_id:
          type: integer
          description: 撤回消息的人
        message_id:
          type: integer
          description: 被撤回的消息 ID
      x-apifox-orders:
        - time
        - self_id
        - post_type
        - notice_type
        - group_id
        - user_id
        - operator_id
        - message_id
      title: 群消息撤回
      x-apifox-folder: ''
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
