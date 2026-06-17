# 获取消息语音详情

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /get_record:
    post:
      summary: 获取消息语音详情
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
                  description: 收到的语音文件名
                out_format:
                  type: string
                  description: 要转换到的格式
                  enum:
                    - mp3
                    - amr
                    - wma
                    - m4a
                    - spx
                    - ogg
                    - wav
                    - flac
                  x-apifox-enum:
                    - value: mp3
                      name: ''
                      description: ''
                    - value: amr
                      name: ''
                      description: ''
                    - value: wma
                      name: ''
                      description: ''
                    - value: m4a
                      name: ''
                      description: ''
                    - value: spx
                      name: ''
                      description: ''
                    - value: ogg
                      name: ''
                      description: ''
                    - value: wav
                      name: ''
                      description: ''
                    - value: flac
                      name: ''
                      description: ''
                  default: mp3
              x-apifox-orders:
                - file
                - out_format
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
                        description: 转换后的语音文件路径
                      file_size:
                        type: string
                        description: 转换后的语音文件大小
                      file_name:
                        type: string
                        description: 转换后的语音文件名称
                      base64:
                        type: string
                        description: 转换后的语音文件 Base64
                    required:
                      - file
                      - file_size
                      - file_name
                    x-apifox-orders:
                      - file
                      - file_size
                      - file_name
                      - base64
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
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: OneBot 11/接口列表/消息
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-151571424-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
