# 发送私聊合并转发消息

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /send_private_forward_msg:
    post:
      summary: 发送私聊合并转发消息
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
                user_id:
                  type: integer
                  description: 对方 QQ 号
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
                          content:
                            type: array
                            items:
                              type: object
                              properties: {}
                              x-apifox-orders: []
                            description: 具体消息
                          uin:
                            type: integer
                            description: 发送者 QQ 号
                          id:
                            type: integer
                            description: 转发消息 ID
                          name:
                            type: string
                            description: 发送者显示名字
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
                - user_id
                - messages
              x-apifox-orders:
                - user_id
                - messages
                - source
                - news
                - summary
                - prompt
            example:
              user_id: '379450326'
              messages:
                - type: node
                  data:
                    content:
                      - type: text
                        data:
                          text: hahahah
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
                  message_id: 1934956788
                message: ''
                wording: ''
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: OneBot 11/接口列表/消息/发送私聊消息
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-226189040-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
