# 发送群聊合并转发消息

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /send_group_forward_msg:
    post:
      summary: 发送群聊合并转发消息
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
                group_id:
                  type: integer
                  description: 群号
                messages:
                  type: array
                  items:
                    type: object
                    properties:
                      type:
                        type: string
                        const: node
                      data:
                        type: object
                        properties:
                          uin:
                            type: integer
                            description: 发送者 QQ 号
                          name:
                            type: string
                            description: 发送者显示名字
                          content:
                            type: array
                            items:
                              type: object
                              properties: {}
                              x-apifox-orders: []
                            description: 具体消息
                          id:
                            type: integer
                            description: 转发消息 ID
                        x-apifox-orders:
                          - id
                          - name
                          - uin
                          - content
                    x-apifox-orders:
                      - type
                      - data
                    required:
                      - type
                      - data
                  description: 要发送的内容
                source:
                  type: string
                  description: 合并转发标题
                news:
                  type: array
                  items:
                    type: object
                    properties:
                      text:
                        type: string
                    x-apifox-orders:
                      - text
                    required:
                      - text
                  description: 合并转发预览文本，若提供，至少 1 条，至多 4 条
                summary:
                  type: string
                  description: 合并转发摘要
                prompt:
                  type: string
                  description: 合并转发的预览外显文本，仅对移动端 QQ 有效
              required:
                - group_id
                - messages
              x-apifox-orders:
                - group_id
                - messages
                - source
                - news
                - summary
                - prompt
            example:
              group_id: 12345
              messages:
                - type: node
                  data:
                    uin: 379450326
                    name: 喵喵喵
                    content:
                      - type: text
                        data:
                          text: hahahah
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
                      forward_id:
                        type: string
                    required:
                      - message_id
                      - forward_id
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
              example:
                status: ok
                retcode: 0
                data:
                  message_id: 2026505362
                  forward_id: >-
                    zUfJpEhzJgXxJID2cIwUoiRk7dMLSgnbhwb8yPrPz8iK6IsBn2uUQArcosp4WrNH
                message: ''
                wording: ''
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: OneBot 11/接口列表/消息/发送群聊消息
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-226189162-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
