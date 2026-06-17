# TextSegment

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
    TextSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - text
        data:
          type: object
          required:
            - text
          properties:
            text:
              type: string
              description: 文本内容
          x-apifox-orders:
            - text
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
