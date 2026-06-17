# FileSegment

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
    FileSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - file
        data:
          type: object
          required:
            - file
          properties:
            file:
              type: string
              description: 文件名
            url:
              type: string
              description: 文件 URL
            path:
              type: string
              description: 本地文件路径
            file_size:
              type: string
              description: 文件大小（字节）
            file_id:
              type: string
              description: 文件 UUID
            thumb:
              type: string
              description: 缩略图 URL
            name:
              type: string
              description: 文件名
          x-apifox-orders:
            - file
            - url
            - path
            - file_size
            - file_id
            - thumb
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
