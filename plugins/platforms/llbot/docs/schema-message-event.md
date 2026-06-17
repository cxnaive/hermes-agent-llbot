# MessageEvent

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
    MessageSender:
      type: object
      required:
        - user_id
        - nickname
      properties:
        user_id:
          type: integer
          description: 发送者的 QQ 号
        nickname:
          type: string
          description: 发送者的昵称
        card:
          type: string
          description: 群名片/昵称（群消息）
        sex:
          type: string
          enum:
            - male
            - female
            - unknown
          description: 发送者的性别
        age:
          type: integer
          description: 发送者的年龄
        level:
          type: string
          description: 群等级（群消息）
        role:
          type: string
          enum:
            - owner
            - admin
            - member
          description: 群角色（群消息）
        title:
          type: string
          description: 专属头衔（群消息）
        group_id:
          type: integer
          description: 群号（来自群的临时聊天）
      x-apifox-orders:
        - user_id
        - nickname
        - card
        - sex
        - age
        - level
        - role
        - title
        - group_id
      title: 消息发送者
      x-apifox-folder: ''
    MessageEvent:
      type: object
      required:
        - time
        - self_id
        - post_type
        - message_id
        - message_seq
        - user_id
        - message_type
        - sender
        - message
        - message_format
        - raw_message
        - font
      properties:
        time:
          type: integer
          description: 事件时间戳（Unix 时间戳，秒）
          examples:
            - 1640995200
        self_id:
          type: integer
          description: 机器人的 QQ 号
          examples:
            - 123456789
        post_type:
          type: string
          enum:
            - message
            - message_sent
          description: 事件类型
        message_id:
          type: integer
          description: 消息 ID（短 ID）
        message_seq:
          type: integer
          description: 消息序列号
        real_id:
          type: integer
          description: 真实消息 ID（仅在 get_msg 接口存在）
        user_id:
          type: integer
          description: 发送者的 QQ 号
        group_id:
          type: integer
          description: 群号（仅群消息）
        message_type:
          type: string
          enum:
            - private
            - group
          description: 消息类型
        sub_type:
          type: string
          enum:
            - friend
            - group
            - normal
          description: 消息子类型
        sender:
          $ref: '#/components/schemas/MessageSender'
        message:
          type: array
          items:
            anyOf:
              - description: 文本
                $ref: '#/components/schemas/TextSegment'
              - $ref: '#/components/schemas/VideoSegment'
                description: 视频
              - $ref: '#/components/schemas/RecordSegment'
                description: 语音
              - $ref: '#/components/schemas/FileSegment'
                description: 文件
              - $ref: '#/components/schemas/AtSegment'
                description: '@'
              - $ref: '#/components/schemas/ReplySegment'
                description: 回复
              - $ref: '#/components/schemas/JsonSegment'
                description: Json
              - $ref: '#/components/schemas/FaceSegment'
                description: 表情
              - $ref: '#/components/schemas/MfaceSegment'
                description: 商城表情
              - $ref: '#/components/schemas/MarkdownSegment'
                description: Markdown
              - $ref: '#/components/schemas/ForwardSegment'
                description: 转发
              - $ref: '#/components/schemas/DiceSegment'
                description: 骰子
              - $ref: '#/components/schemas/RpsSegment'
                description: 石头剪刀布
              - $ref: '#/components/schemas/KeyboardSegment'
                description: 按钮
          description: 消息内容（消息段数组格式）
        message_format:
          type: string
          enum:
            - array
            - string
          description: 消息格式类型
        raw_message:
          type: string
          description: 原始消息内容（CQ 码格式）
        font:
          type: integer
          description: 字体 ID
          default: 14
        target_id:
          type: integer
          description: 目标 ID（仅发送的消息）
        temp_source:
          type: integer
          enum:
            - 0
            - 1
            - 2
            - 3
            - 4
            - 6
            - 7
            - 8
            - 9
          description: 临时聊天来源（0 = 群聊）
      x-apifox-orders:
        - time
        - self_id
        - post_type
        - message_id
        - message_seq
        - real_id
        - user_id
        - group_id
        - message_type
        - sub_type
        - sender
        - message
        - message_format
        - raw_message
        - font
        - target_id
        - temp_source
      title: 消息
      x-apifox-folder: ''
  securitySchemes: {}
servers:
  - url: http://127.0.0.1:3000
    description: 开发环境
security: []

```
