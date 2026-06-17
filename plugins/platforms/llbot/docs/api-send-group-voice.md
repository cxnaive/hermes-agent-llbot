# 发送群聊语音消息

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
      summary: 发送群聊语音消息
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
                        const: record
                      data:
                        type: object
                        properties:
                          file:
                            type: string
                            description: |-
                              支持三种形式:

                              * file://d:/1.mp3

                              * http://baidu.com/xxxx/1.mp3

                              * base64://xxxxxxxx
                        required:
                          - file
                        x-apifox-orders:
                          - file
                    x-apifox-orders:
                      - type
                      - data
                    required:
                      - type
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
            example: "{\r\n    \"group_id\": 379450326,\r\n    \"message\": [\r\n        {\r\n            \"type\": \"record\",\r\n            \"data\": {\r\n                // 本地路径\r\n                \"file\": \"file://d:/11.mp3\"\r\n                \r\n                // 网络路径\r\n                // \"file\": \"http://i0.hdslb.com/1.mp3\"\r\n                \r\n                //base64编码\r\n                // \"file:\": \"base64://xxxxxxxx\"\r\n            }\r\n        }\r\n    ]\r\n}"
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
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-226392170-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
