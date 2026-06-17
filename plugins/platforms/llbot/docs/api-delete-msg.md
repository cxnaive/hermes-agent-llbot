# 撤回消息

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /delete_msg:
    post:
      summary: 撤回消息
      deprecated: false
      description: ''
      tags:
        - OneBot 11/接口列表/消息
      parameters: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                message_id:
                  type: integer
                  description: 消息 ID
              x-apifox-orders:
                - message_id
              required:
                - message_id
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
                  message:
                    type: string
                  wording:
                    type: string
                required:
                  - status
                  - retcode
                  - message
                  - wording
              examples:
                '1':
                  summary: 成功示例
                  value:
                    status: ok
                    retcode: 0
                    message: ''
                    wording: ''
                '2':
                  summary: 异常示例
                  value:
                    status: failed
                    retcode: 200
                    data: null
                    message: 'Error: 消息-966671988不存在'
                    wording: 'Error: 消息-966671988不存在'
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: OneBot 11/接口列表/消息
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-124033506-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
