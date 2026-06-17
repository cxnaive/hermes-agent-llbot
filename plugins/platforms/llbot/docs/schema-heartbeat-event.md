# HeartbeatEvent

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
    HeartbeatEvent:
      type: object
      required:
        - time
        - self_id
        - post_type
        - meta_event_type
        - status
        - interval
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
            - meta_event
          description: 事件类型
        meta_event_type:
          type: string
          enum:
            - heartbeat
        status:
          type: object
          required:
            - online
            - good
          properties:
            online:
              type: boolean
              description: 机器人是否在线
              nullable: true
            good:
              type: boolean
              description: 机器人状态是否良好
          x-apifox-orders:
            - online
            - good
        interval:
          type: integer
          description: 心跳间隔（毫秒）
          examples:
            - 5000
      x-apifox-orders:
        - time
        - self_id
        - post_type
        - meta_event_type
        - status
        - interval
      title: 心跳
      x-apifox-folder: ''
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
