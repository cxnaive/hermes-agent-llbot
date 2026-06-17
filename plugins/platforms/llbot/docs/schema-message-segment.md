# MessageSegment

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
    ShakeSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - shake
        data:
          type: object
          description: 窗口抖动（空对象）
          x-apifox-orders: []
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
    ContactSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - contact
        data:
          type: object
          required:
            - type
            - id
          properties:
            type:
              type: string
              enum:
                - qq
                - group
              description: 联系人类型
            id:
              type: string
              description: 联系人 ID
          x-apifox-orders:
            - type
            - id
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
    RpsSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - rps
        data:
          type: object
          required:
            - result
          properties:
            result:
              oneOf:
                - type: integer
                - type: string
              description: 猜拳结果（1=石头，2=剪刀，3=布）
          x-apifox-orders:
            - result
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
    DiceSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - dice
        data:
          type: object
          required:
            - result
          properties:
            result:
              oneOf:
                - type: integer
                - type: string
              description: 骰子结果（1-6）
          x-apifox-orders:
            - result
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
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
    MusicSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - music
        data:
          type: object
          properties:
            type:
              type: string
              enum:
                - qq
                - 163
                - xm
                - custom
              description: 音乐平台类型
            id:
              type: string
              description: 音乐 ID（平台音乐）
            url:
              type: string
              description: 音乐 URL（自定义音乐）
            audio:
              type: string
              description: 音频 URL（自定义音乐）
            title:
              type: string
              description: 音乐标题（自定义音乐）
            content:
              type: string
              description: 音乐描述（自定义音乐）
            image:
              type: string
              description: 封面图片 URL（自定义音乐）
          x-apifox-orders:
            - type
            - id
            - url
            - audio
            - title
            - content
            - image
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
    ForwardSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - forward
        data:
          type: object
          required:
            - id
          properties:
            id:
              type: string
              description: 转发消息 ID
          x-apifox-orders:
            - id
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
    NodeSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - node
        data:
          type: object
          properties:
            id:
              oneOf:
                - type: integer
                - type: string
              description: 转发的消息 ID
            content:
              oneOf:
                - type: string
                  description: 消息内容（字符串格式）
                - type: array
                  items:
                    type: object
                    description: 消息段（避免循环引用，使用通用对象）
                    x-apifox-orders: []
              description: 消息内容
            user_id:
              type: integer
              description: 用户 ID（OneBot11 格式）
            nickname:
              type: string
              description: 昵称（OneBot11 格式）
            name:
              type: string
              description: 名称（go-cqhttp 格式）
            uin:
              oneOf:
                - type: integer
                - type: string
              description: UIN（go-cqhttp 格式）
          x-apifox-orders:
            - id
            - content
            - user_id
            - nickname
            - name
            - uin
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
    MarkdownSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - markdown
        data:
          type: object
          required:
            - content
          properties:
            content:
              type: string
              description: Markdown 内容
          x-apifox-orders:
            - content
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
    MfaceSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - mface
        data:
          type: object
          required:
            - emoji_package_id
            - emoji_id
            - key
          properties:
            emoji_package_id:
              type: integer
              description: 表情包 ID
            emoji_id:
              type: string
              description: 表情 ID
            key:
              type: string
              description: 表情密钥
            summary:
              type: string
              description: 表情摘要/名称
            url:
              type: string
              description: 表情 URL
          x-apifox-orders:
            - emoji_package_id
            - emoji_id
            - key
            - summary
            - url
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
    FaceSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - face
        data:
          type: object
          required:
            - id
          properties:
            id:
              type: string
              description: 表情 ID
          x-apifox-orders:
            - id
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
    XmlSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - xml
        data:
          type: object
          required:
            - data
          properties:
            data:
              type: string
              description: XML 数据（字符串格式）
          x-apifox-orders:
            - data
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
    JsonSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - json
        data:
          type: object
          required:
            - data
          properties:
            data:
              type: string
              description: JSON 数据（字符串格式）
          x-apifox-orders:
            - data
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
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
    FlashFileSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - flash_file
        data:
          type: object
          required:
            - title
            - file_set_id
            - scene_type
          properties:
            title:
              type: string
              description: 闪传文件标题
            file_set_id:
              type: string
              description: 文件集 ID
            scene_type:
              type: integer
              description: 场景类型
          x-apifox-orders:
            - title
            - file_set_id
            - scene_type
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
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
    RecordSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - record
        data:
          type: object
          required:
            - file
          properties:
            file:
              type: string
              description: 音频文件名
            url:
              type: string
              description: 音频 URL
            path:
              type: string
              description: 本地文件路径
            file_size:
              type: string
              description: 文件大小（字节）
            thumb:
              type: string
              description: 缩略图 URL
            name:
              type: string
              description: 音频名称
          x-apifox-orders:
            - file
            - url
            - path
            - file_size
            - thumb
            - name
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
    VideoSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - video
        data:
          type: object
          required:
            - file
          properties:
            file:
              type: string
              description: 视频文件名
            url:
              type: string
              description: 视频 URL
            path:
              type: string
              description: 本地文件路径
            file_size:
              type: string
              description: 文件大小（字节）
            thumb:
              type: string
              description: 缩略图 URL
            name:
              type: string
              description: 视频名称
          x-apifox-orders:
            - file
            - url
            - path
            - file_size
            - thumb
            - name
      x-apifox-orders:
        - type
        - data
      x-apifox-folder: ''
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
    MessageSegment:
      type: object
      required:
        - type
        - data
      properties:
        type:
          type: string
          enum:
            - text
            - image
            - music
            - video
            - record
            - file
            - flash_file
            - at
            - reply
            - json
            - face
            - mface
            - markdown
            - node
            - forward
            - xml
            - poke
            - dice
            - rps
            - contact
            - shake
            - keyboard
        data:
          type: object
          properties: {}
          x-apifox-orders: []
      discriminator:
        propertyName: type
        mapping:
          text: '#/definitions/189483991'
          image: '#/definitions/189483992'
          music: '#/definitions/189484006'
          video: '#/definitions/189483993'
          record: '#/definitions/189483994'
          file: '#/definitions/189483995'
          flash_file: '#/definitions/189483996'
          at: '#/definitions/189483997'
          reply: '#/definitions/189483998'
          json: '#/definitions/189483999'
          face: '#/definitions/189484001'
          mface: '#/definitions/189484002'
          markdown: '#/definitions/189484003'
          node: '#/definitions/189484004'
          forward: '#/definitions/189484005'
          xml: '#/definitions/189484000'
          poke: '#/definitions/189484007'
          dice: '#/definitions/189484008'
          rps: '#/definitions/189484009'
          contact: '#/definitions/189484010'
          shake: '#/definitions/189484011'
          keyboard: '#/definitions/189484012'
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
