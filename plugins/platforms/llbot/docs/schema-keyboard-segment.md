# KeyboardSegment

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
    KeyboardButton:
      type: object
      required:
        - id
        - render_data
        - action
      properties:
        id:
          type: string
          description: 按钮 ID
        render_data:
          type: object
          required:
            - label
            - visited_label
            - style
          properties:
            label:
              type: string
              description: 按钮标签
            visited_label:
              type: string
              description: 点击后的标签
            style:
              type: integer
              description: 按钮样式
          x-apifox-orders:
            - label
            - visited_label
            - style
        action:
          type: object
          required:
            - type
            - permission
            - unsupport_tips
            - data
            - reply
            - enter
          properties:
            type:
              type: integer
              description: 动作类型
            permission:
              type: object
              required:
                - type
                - specify_role_ids
                - specify_user_ids
              properties:
                type:
                  type: integer
                  description: 权限类型
                specify_role_ids:
                  type: array
                  items:
                    type: string
                  description: 指定角色 ID
                specify_user_ids:
                  type: array
                  items:
                    type: string
                  description: 指定用户 ID
              x-apifox-orders:
                - type
                - specify_role_ids
                - specify_user_ids
            unsupport_tips:
              type: string
              description: 不支持时的提示
            data:
              type: string
              description: 动作数据
            reply:
              type: boolean
              description: 是否回复
            enter:
              type: boolean
              description: 是否进入
          x-apifox-orders:
            - type
            - permission
            - unsupport_tips
            - data
            - reply
            - enter
      x-apifox-orders:
        - id
        - render_data
        - action
      x-apifox-folder: ''
    KeyboardSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - keyboard
        data:
          type: object
          required:
            - rows
          properties:
            rows:
              type: array
              items:
                type: object
                required:
                  - buttons
                properties:
                  buttons:
                    type: array
                    items:
                      $ref: '#/components/schemas/KeyboardButton'
                x-apifox-orders:
                  - buttons
          x-apifox-orders:
            - rows
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
