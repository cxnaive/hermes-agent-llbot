# MessageSender

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths: {}
components:
  schemas:
    MessageSender:
      type: object
      required:
        - user_id
        - nickname
      properties:
        user_id:
          type: integer
          description: 发送者的 QQ 号
        nickname:
          type: string
          description: 发送者的昵称
        card:
          type: string
          description: 群名片/昵称（群消息）
        sex:
          type: string
          enum:
            - male
            - female
            - unknown
          description: 发送者的性别
        age:
          type: integer
          description: 发送者的年龄
        level:
          type: string
          description: 群等级（群消息）
        role:
          type: string
          enum:
            - owner
            - admin
            - member
          description: 群角色（群消息）
        title:
          type: string
          description: 专属头衔（群消息）
        group_id:
          type: integer
          description: 群号（来自群的临时聊天）
      x-apifox-orders:
        - user_id
        - nickname
        - card
        - sex
        - age
        - level
        - role
        - title
        - group_id
      title: 消息发送者
      x-apifox-folder: ''
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
