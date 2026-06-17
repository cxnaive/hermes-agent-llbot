# NodeSegment

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
    NodeSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - node
        data:
          type: object
          properties:
            id:
              oneOf:
                - type: integer
                - type: string
              description: 转发的消息 ID
            content:
              oneOf:
                - type: string
                  description: 消息内容（字符串格式）
                - type: array
                  items:
                    type: object
                    description: 消息段（避免循环引用，使用通用对象）
                    x-apifox-orders: []
              description: 消息内容
            user_id:
              type: integer
              description: 用户 ID（OneBot11 格式）
            nickname:
              type: string
              description: 昵称（OneBot11 格式）
            name:
              type: string
              description: 名称（go-cqhttp 格式）
            uin:
              oneOf:
                - type: integer
                - type: string
              description: UIN（go-cqhttp 格式）
          x-apifox-orders:
            - id
            - content
            - user_id
            - nickname
            - name
            - uin
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
