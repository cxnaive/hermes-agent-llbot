# 获取消息文件详情

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /get_file:
    post:
      summary: 获取消息文件详情
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
                file:
                  type: string
                  description: 收到的文件名
                download:
                  type: boolean
                  description: 是否下载文件到 QQ 目录
                  default: true
              x-apifox-orders:
                - file
                - download
              required:
                - file
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
                      file:
                        type: string
                        description: 文件路径
                      url:
                        type: string
                        description: 文件网址
                      file_size:
                        type: string
                        description: 文件大小
                      file_name:
                        type: string
                        description: 文件名
                    required:
                      - file
                      - url
                      - file_size
                      - file_name
                    x-apifox-orders:
                      - file
                      - url
                      - file_size
                      - file_name
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
              example: |-
                {
                    "status": "ok",
                    "retcode": 0,
                    "data": {
                        "file": "C:\\Users\\linyuchen\\Documents\\Downloads\\~.jpg",
                        "url": "http://xxxx",
                        "file_size": "59635",
                        "file_name": "~.jpg",
                        "base64": "/9j/4AAQSkZJRgABAQEASxxxx" // 文件的 base64 编码, 需要在 LLOneBot 的配置文件中开启 文件转base64
                    },
                    "message": "",
                    "wording": ""
                }
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: OneBot 11/接口列表/消息
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-156061303-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
