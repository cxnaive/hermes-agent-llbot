# ImageSegment

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
    ImageSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - image
        data:
          type: object
          required:
            - file
          properties:
            file:
              type: string
              description: 图片文件名或路径
            url:
              type: string
              description: 图片 URL
            file_size:
              type: string
              description: 文件大小（字节）
            summary:
              type: string
              description: 图片摘要
            subType:
              type: integer
              description: 图片子类型
            type:
              type: string
              enum:
                - flash
                - show
              description: 图片显示类型
            thumb:
              type: string
              description: 缩略图 URL
            name:
              type: string
              description: 图片名称
          x-apifox-orders:
            - file
            - url
            - file_size
            - summary
            - subType
            - type
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
