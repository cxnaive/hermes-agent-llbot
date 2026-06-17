# Websocket 发送/接受消息

## Websocket 连接有正向和反向两种

正向的意思是 Bot 端为 Websocket 服务器，你的插件需要主动去连接它，

反向的意思是 Bot 端作为客户端，你的插件作为服务端，Bot 端会主动连接你的插件端。

## 调用接口的方式

和 Bot 建立 Websocket 链接后，发送一个 JSON
```json
{
    "action": "send_group_msg",
    "params": {
      "group_id": 545402644,
      "message": [
        {
          "type": "text",
          "data": {
            "text": "HelloKitty"
          }
        }
      ]
    },
    "echo": "唯一标识，如 uuid"
}

```

`action` 对应的接口名和 HTTP 的一致，具体有哪些接口名可以在左侧接口列表查看。

`params` 则和 HTTP 接口提交的 JSON 一致。

`echo` 发送和返回都会带有此字段，用于 Websocket 发送请求后返回的对应，由于 Websocket 是长连接，同一时间可能会有很多返回，因此需要一个唯一标识符，这样才能识别自己调用的接口后返回的数据。

同时这个 Websocket 连接也会接收到 Bot 的消息和事件上报。


## 下面是一个正向 Websocket 的 Python 示例

需要先安装 websockets 包，`pip install websockets`

```python
import uuid
import asyncio
import json

import websockets


async def async_input(prompt: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

async def receive_messages(ws):
    while True:
        message = await ws.recv()
        print(f"收到消息: {message}")


async def main():
    uri = "ws://localhost:3001"  # 替换为你的 LLOneBot WebSocket 正向地址
    group_id = await async_input("输入群号: ")
    
    async with websockets.connect(uri) as websocket:
        asyncio.create_task(receive_messages(websocket))
        while True:
            message = await async_input("输入消息内容: ")
            echo = str(uuid.uuid4())
            data = {
                "action": "send_group_msg",
                "params": {
                    "group_id": group_id,
                    "message": {
                        "type": "text",
                        "data": {
                            "text": message
                        }
                    }
                },
                'echo': echo
            }
            await websocket.send(json.dumps(data))

asyncio.run(main())
```

在 LLOneBot 启用 Websocket 正向，并填入端口 3001。

然后运行上面的 Python 代码，输入群号后开始打印收到的消息，再输入任意内容按回车会往刚刚输入的群号发送消息。


## 下面是反向 Websocket 的 Python 示例


需要先安装 websockets 包，`pip install websockets`

```python
import asyncio
import json
import uuid

import websockets

async def async_input(prompt: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

websocket_clients = []

# 处理客户端连接
async def handle_connection(websocket, path):
    print("LLOneBot 已连接")
    websocket_clients.append(websocket)
    try:
        async for message in websocket:
            print(f"收到消息: {message}")
    except websockets.ConnectionClosed:
        try:
            websocket_clients.remove(websocket)
        except ValueError:
            pass
        print("客户端断开连接")


# 启动 WebSocket 服务器
async def start_server():
    async with websockets.serve(handle_connection, "localhost", 8765):
        print("WebSocket 服务器已启动，监听 ws://localhost:8765")
        await asyncio.Future()

async def main():
    group_id = await async_input("输入群号: ")
    asyncio.create_task(start_server())
    while True:
        message = await async_input("输入消息内容: ")
        echo = str(uuid.uuid4())
        data = {
            "action": "send_group_msg",
            "params": {
                "group_id": group_id,
                "message": {
                    "type": "text",
                    "data": {
                        "text": message
                    }
                }
            },
            'echo': echo
        }
        for ws in websocket_clients:
            await ws.send(json.dumps(data))


asyncio.run(main())
```

在 LLOneBot 启用 Websocket 反向，并填入反向地址 ws://localhost:8765

运行上面的 Python 代码后，输入群号后开始打印收到的消息，再输入任意内容按回车会往刚刚输入的群号发送消息。

