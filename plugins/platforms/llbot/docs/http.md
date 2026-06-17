# HTTP 调用/接收消息

## 调用接口

首先需要在 LLTwoBot 中开启 OneBot 的 HTTP 服务。

参考具体接口用法，如果是查看Python的示例，注意`http.client.HTTPSConnection`需要改成`http.client.HTTPConnection`

## HTTP Server 的方式接收消息

此方法会建立一个 HTTP 服务来接收 LLOneBot 上报的消息

在 LLOneBot 中开启HTTP上报，并填入上报地址，这样 Bot 在收到消息后会往这个地址 POST 一个消息JSON。

这个地址是一个 HTTP 服务端地址，意味着你需要建立一个 HTTP 服务端来接受消息。

举例：

用 Python 建立一个 `http://localhost:8080` 的服务端用于接受 Bot 的上报消息

```python
import uvicorn
from fastapi import FastAPI, Request

app = FastAPI()


@app.post("/")
async def root(request: Request):
    data = await request.json()  # 获取事件数据
    print(data)
    return {}

if __name__ == "__main__":
    uvicorn.run(app, port=8080)
```

运行这个 Python 代码后，会在本地 8080 端口启动一个 HTTP 服务，

在LLOneBot`设置中开启 HTTP 事件上报，地址为 http://localhost:8080/`，

当有事件发生时，Bot 会向 http://localhost:8080/ 发送 POST JSON 请求。

## HTTP SSE 的方式接收消息 

此方法是主动连接 LLOneBot HTTP 接口建立长连接获取消息，需要 LLOneBot 4.7.3版本以上

```python
import httpx
import asyncio

async def get_data():
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream('GET', 'http://localhost:3000/_events') as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    data = line.split("data:", 1)[1]
                    print(data)



asyncio.run(get_data())
```
