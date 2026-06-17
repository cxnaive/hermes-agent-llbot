# 设置输入状态

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /set_input_status:
    post:
      summary: 设置输入状态
      deprecated: false
      description: 此 API 需要 LLBot 7.12.3 及以上版本
      tags:
        - OneBot 11/接口列表/用户
      parameters: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: integer
                  description: 对方 QQ 号
                event_type:
                  type: integer
                  description: 事件类型（为 `0` 时表示「对方正在说话...」，为 `1` 时表示「对方正在输入...」）
              x-apifox-orders:
                - user_id
                - event_type
              required:
                - user_id
                - event_type
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
                required:
                  - status
                  - retcode
                  - data
                  - message
                  - wording
                x-apifox-orders:
                  - status
                  - retcode
                  - data
                  - message
                  - wording
              example:
                status: ok
                retcode: 0
                data: null
                message: ''
                wording: ''
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: OneBot 11/接口列表/用户
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-449484306-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
