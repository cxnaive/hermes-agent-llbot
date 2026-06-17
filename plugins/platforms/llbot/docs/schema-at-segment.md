# AtSegment

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
    AtSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - at
        data:
          type: object
          required:
            - qq
          properties:
            qq:
              oneOf:
                - type: string
                  enum:
                    - all
                - type: string
                  pattern: ^[0-9]+$
              description: QQ 号或 'all' 表示 @全体成员
            name:
              type: string
              description: 显示名称
          x-apifox-orders:
            - qq
            - name
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
