# PokeEvent

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
    PokeEvent:
      type: object
      required:
        - time
        - self_id
        - post_type
        - notice_type
        - sub_type
        - user_id
        - target_id
      properties:
        time:
          type: integer
          description: 事件时间戳（Unix 时间戳，秒）
          examples:
            - 1640995200
        self_id:
          type: integer
          description: 机器人的 QQ 号
          examples:
            - 123456789
        post_type:
          type: string
          enum:
            - notice
          description: 事件类型
        notice_type:
          type: string
          enum:
            - notify
        sub_type:
          type: string
          enum:
            - poke
        user_id:
          type: integer
          description: 发送戳一戳的用户
        target_id:
          type: integer
          description: 被戳的目标用户
        group_id:
          type: integer
          description: 群号（仅群聊戳一戳存在）
        raw_info:
          type: string
          description: 原始戳一戳信息
          examples:
            - >-
              <gtip align="center"> <qq uin="u_l029ehNpnNjaQrZUhwv5uQ" col="1"
              nm="" /> <img
              src="http://tianquan.gtimg.cn/nudgeaction/item/8/expression.jpg"
              jp="https://zb.vip.qq.com/v2/pages/nudgeMall?_wv=2&amp;actionId=8"
              /> <nor txt="揉了揉"/> <qq uin="u_snYxnEfja-Po_cdFcyccRQ" col="1"
              nm="" tp="0"/> <nor txt="的干脆面，居然全碎啦！"/> </gtip>
      x-apifox-orders:
        - time
        - self_id
        - post_type
        - notice_type
        - sub_type
        - user_id
        - target_id
        - group_id
        - raw_info
      title: 戳一戳
      x-apifox-folder: ''
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
