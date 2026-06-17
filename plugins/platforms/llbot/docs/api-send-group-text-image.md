# 发送群聊文字+图片

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
      summary: 发送群聊文字+图片
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
                    allOf:
                      - type: object
                        properties:
                          type:
                            type: string
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
                      - type: object
                        properties:
                          type:
                            type: string
                            const: image
                          data:
                            type: object
                            properties:
                              file:
                                type: string
                            x-apifox-orders:
                              - file
                            required:
                              - file
                        x-apifox-orders:
                          - type
                          - data
                        required:
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
                - type: text
                  data:
                    text: HelloKitty
                - type: image
                  data:
                    file: >-
                      http://i0.hdslb.com/bfs/archive/c8fd97a40bf79f03e7b76cbc87236f612caef7b2.png
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
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-226300086-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
