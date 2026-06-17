# PokeSegment

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
    PokeSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - poke
        data:
          type: object
          properties:
            qq:
              type: integer
              description: 目标 QQ 号
            id:
              type: integer
              description: 戳一戳类型 ID
          x-apifox-orders:
            - qq
            - id
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
