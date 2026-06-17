# 获取消息图片详情

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /get_image:
    post:
      summary: 获取消息图片详情
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
                  description: 收到的图片文件名
              x-apifox-orders:
                - file
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
                      url:
                        type: string
                      file_size:
                        type: string
                      file_name:
                        type: string
                    required:
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
              example:
                status: ok
                retcode: 0
                data:
                  file: >-
                    E:\SystemDocuments\QQ\721011692\nt_qq\nt_data\Pic\2024-10\Ori\982eac0e63f48aa524afeaab4a0454fb.gif
                  url: >-
                    https://multimedia.nt.qq.com.cn/download?appid=1407&fileid=EhQUF44jzJ2UpXQ5wgCbzSDrXE6fwBiq1Qog_woozb_H76qkiQMyBHByb2RQgL2jAVoQ-4KUwjXwnPw5XThLD-tL1w&spec=0&rkey=CAESKBkcro_MGujo_-Kh0dsVOliftm4gzNtIFmtigHMTCIkVQRLhdZqOhp8
                  file_size: '174762'
                  file_name: 982EAC0E63F48AA524AFEAAB4A0454FB.gif
                message: ''
                wording: ''
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: OneBot 11/接口列表/消息
      x-apifox-status: released
      x-run-in-apifox: https://app.apifox.com/web/project/3495033/apis/api-151567554-run
components:
  schemas: {}
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
