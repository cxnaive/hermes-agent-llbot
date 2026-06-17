# 发送群聊回复消息

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /send_group_msg:
    post:
      summary: 发送群聊回复消息
      deprecated: false
      description: ''
      tags:
        - OneBot 11/接口列表/消息/发送群聊消息
      parameters: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: array
                  items:
                    type: object
                    properties:
                      type:
                        type: string
                        const: reply
                      data:
                        type: object
                        properties:
                          id:
                            type: integer
                            title: 要回复的消息id
                          text:
                            type: string
                        required:
                          - text
                        x-apifox-orders:
                          - id
                          - text
                    required:
                      - type
                      - data
                    x-apifox-orders:
                      - type
                      - data
                  description: 要发送的内容
                group_id:
                  type: integer
                  description: 群号
              required:
                - group_id
                - message
              x-apifox-orders:
                - group_id
                - message
            example:
              group_id: 379450326
              message:
                - type: reply
                  data:
                    id: 1263753202
                - type: text
                  data:
                    text: 回复你了
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
                    type: object
                    properties:
                      message_id:
                        type: integer
                    required:
                      - message_id
                    x-apifox-orders:
                      - message_id
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
                data:
                  message_id: 696124706
                message: ''
                wording: ''
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: OneBot 11/接口列表/消息/发送群聊消息
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-226300082-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
