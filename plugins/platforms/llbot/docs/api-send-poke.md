# 发送戳一戳（双击头像）

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /send_poke:
    post:
      summary: 发送戳一戳（双击头像）
      deprecated: false
      description: 此 API 需要 LLBot 7.11.3 及以上版本
      tags:
        - OneBot 11/接口列表/消息
      parameters: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                group_id:
                  type: integer
                  description: 群号，不填则为私聊戳一戳
                user_id:
                  type: integer
                  description: 用户 QQ 号
                target_id:
                  type: integer
                  description: 目标 QQ 号，仅在私聊生效
              x-apifox-orders:
                - group_id
                - user_id
                - target_id
              required:
                - user_id
            examples: {}
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  retcode:
                    type: integer
                  data:
                    type: 'null'
                  message:
                    type: string
                  wording:
                    type: string
                x-apifox-orders:
                  - status
                  - retcode
                  - data
                  - message
                  - wording
                required:
                  - status
                  - retcode
                  - data
                  - message
                  - wording
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: OneBot 11/接口列表/消息
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-440902553-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
