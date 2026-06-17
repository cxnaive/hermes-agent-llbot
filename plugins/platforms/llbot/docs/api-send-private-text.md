# 发送私聊文本消息

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /send_private_msg:
    post:
      summary: 发送私聊文本消息
      deprecated: false
      description: ''
      tags:
        - OneBot 11/接口列表/消息/发送私聊消息
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
                        x-apifox-mock: text
                        const: text
                      data:
                        type: object
                        properties:
                          text:
                            type: string
                        x-apifox-orders:
                          - text
                        required:
                          - text
                    x-apifox-orders:
                      - type
                      - data
                    required:
                      - type
                      - data
                  description: 要发送的内容
                01HGM9PBZTA7WE3M4PDY10VJ4H:
                  type: string
                user_id:
                  type: integer
                  description: 对方 QQ 号
                  x-apifox-mock: '149443938'
              x-apifox-orders:
                - user_id
                - message
                - 01HGM9PBZTA7WE3M4PDY10VJ4H
              required:
                - user_id
                - message
                - 01HGM9PBZTA7WE3M4PDY10VJ4H
            example:
              user_id: 370450326
              message:
                - type: text
                  data:
                    text: HelloKitty
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
      x-apifox-folder: OneBot 11/接口列表/消息/发送私聊消息
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-226194727-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
