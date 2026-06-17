# 获取消息详情

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /get_msg:
    post:
      summary: 获取消息详情
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
                  data:
                    type: object
                    properties:
                      self_id:
                        type: integer
                      user_id:
                        type: integer
                      time:
                        type: integer
                      message_id:
                        type: integer
                      real_id:
                        type: integer
                      message_seq:
                        type: integer
                      message_type:
                        type: string
                      sender:
                        type: object
                        properties:
                          user_id:
                            type: integer
                          nickname:
                            type: string
                          card:
                            type: string
                          role:
                            type: string
                          title:
                            type: string
                        required:
                          - user_id
                          - nickname
                          - card
                          - role
                          - title
                        x-apifox-orders:
                          - user_id
                          - nickname
                          - card
                          - role
                          - title
                      raw_message:
                        type: string
                      font:
                        type: integer
                      sub_type:
                        type: string
                      message:
                        type: array
                        items:
                          type: object
                          properties:
                            type:
                              type: string
                            data:
                              type: object
                              properties:
                                text:
                                  type: string
                              required:
                                - text
                              x-apifox-orders:
                                - text
                          x-apifox-orders:
                            - type
                            - data
                      message_format:
                        type: string
                      post_type:
                        type: string
                      group_id:
                        type: integer
                      status:
                        type: string
                        enum:
                          - normal
                          - deleted
                        x-apifox-enum:
                          - value: normal
                            name: ''
                            description: ''
                          - value: deleted
                            name: ''
                            description: ''
                    required:
                      - self_id
                      - user_id
                      - time
                      - message_id
                      - real_id
                      - message_seq
                      - message_type
                      - sender
                      - raw_message
                      - font
                      - sub_type
                      - message
                      - message_format
                      - post_type
                      - group_id
                      - status
                    x-apifox-orders:
                      - self_id
                      - user_id
                      - time
                      - message_id
                      - real_id
                      - message_seq
                      - message_type
                      - sender
                      - raw_message
                      - font
                      - sub_type
                      - message
                      - message_format
                      - post_type
                      - group_id
                      - status
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
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: OneBot 11/接口列表/消息
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-147574979-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
