# ReplySegment

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
    ReplySegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - reply
        data:
          type: object
          required:
            - id
          properties:
            id:
              type: string
              description: 要回复的消息 ID
          x-apifox-orders:
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
