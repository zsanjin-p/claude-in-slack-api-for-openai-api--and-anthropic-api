import json
from os import getenv
from typing import Union
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from slack import client  # Assuming 'client' is capable of handling and generating SSE events
from typing import List, Optional

from fastapi.middleware.cors import CORSMiddleware

class Message(BaseModel):
    role: Optional[str] = ""  # 设置默认值为空字符串
    content: Optional[str] = ""  # 设置默认值为空字符串

class ChatCompletionsRequest(BaseModel):
    stream: Optional[bool] = False  # 将stream字段设置为可选，并提供默认值
    model: str
    messages: List[Message]
    temperature: float
    max_tokens: Optional[int] = None  # 将max_tokens字段设置为可选，并提供默认值
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0 
    presence_penalty: Optional[float] = 0.0


app = FastAPI()

origins = [
    "*",  # 允许此来源的跨域请求
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许来自上述来源列表的跨域请求
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

server_token = getenv("SERVER_TOKEN")

async def must_token(x_token: Union[str, None] = Header(None)):
    if server_token and x_token != server_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "msg": "must token",
            }
        )

class ClaudeChatPrompt(BaseModel):
    prompt: str
    stream: Optional[bool] = None  # 添加stream参数，允许为空


def format_event(event_str: str) -> dict:
    # Assuming 'event_str' is a plain text string and not JSON
    event_content = {
        "completion": event_str,
        "stop_reason": None,  # You might need to adjust this based on your application logic
        "model": "claude-2.0"
    }
    json_event_content = json.dumps(event_content, ensure_ascii=False)  # Set ensure_ascii=False
    return {"event": "completion", "data": json_event_content}


@app.post("/v1/complete", dependencies=[Depends(must_token)])
async def chat(body: ClaudeChatPrompt):
    # 删除body.prompt中的开头的"\n\nHuman: "和"\n\nAssistant"
    cleaned_prompt = body.prompt.replace("\n\nHuman: ", "", 1).replace("\n\nAssistant:", "", 1)
    
    await client.open_channel()
    await client.chat(cleaned_prompt)  # 使用处理后的cleaned_prompt
    
    async def event_generator():
        async for event_str in client.get_stream_reply():
            formatted_event = format_event(event_str)
            yield formatted_event
    
    if body.stream:
        return EventSourceResponse(event_generator(), ping=2000)
    else:
        # 对于非流式传输，等待slack的回复，然后构造并返回一个简单的JSON响应
        reply = await client.get_reply()
        return {
            "completion": reply,
            "stop_reason": "stop_sequence",
            "model": "claude-2"
        }


def format_custom_event(event_str: str, is_initial: bool = False, is_final: bool = False) -> str:
    if is_initial:
        event_content = {
            "id": "chatcmpl-87FpvEcXVGUigZE9y0OoYGqxKHLQT",
            "object": "chat.completion.chunk",
            "created": 1696739863,
            "model": "gpt-3.5-turbo-0613",
            "choices": [{"index": 0, "delta": {"role": "assistant", "content": ""}, "finish_reason": None}]
        }
    elif is_final:
        event_content = {
            "id": "chatcmpl-87FpvEcXVGUigZE9y0OoYGqxKHLQT",
            "object": "chat.completion.chunk",
            "created": 1696739863,
            "model": "gpt-3.5-turbo-0613",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
    else:
        event_content = {
            "id": "chatcmpl-87FpvEcXVGUigZE9y0OoYGqxKHLQT",
            "object": "chat.completion.chunk",
            "created": 1696739863,
            "model": "gpt-3.5-turbo-0613",
            "choices": [{"index": 0, "delta": {"content": event_str}, "finish_reason": None}]
        }

    json_event_content = json.dumps(event_content, ensure_ascii=False)
    return f'data: {json_event_content}\n\n'

def format_response(event_str: str) -> dict:
    # 假设 event_str 是你的 assistant 的回应
    response_content = {
        "model": "gpt-35-turbo",
        "object": "chat.completion",
        "usage": {
            "prompt_tokens": 238,  # 这需要从你的模型或某处获取
            "completion_tokens": 187,  # 这也需要从你的模型或某处获取
            "total_tokens": 425  # 这也需要从你的模型或某处获取
        },
        "id": "chatcmpl-88UsRDsT3GHYNwHqEKsrOA4rYaY2D",  # 这也需要从你的模型或某处获取
        "created": 1697036007,  # 这也需要从你的模型或某处获取
        "choices": [{
            "index": 0,
            "delta": None,
            "message": {
                "role": "assistant",
                "content": event_str
            },
            "finish_reason": "stop"
        }]
    }
    return response_content

@app.post("/v1/chat/completions", dependencies=[Depends(must_token)])
async def chat_completions(body: ChatCompletionsRequest):
    # 将消息合并成一个字符串，以便传递给chat函数
    # 在合并时，如果role或content为空，将其视为空字符串处理
    prompt = '\n\n'.join(f'{msg.role if msg.role else "Unknown"}: {msg.content if msg.content else ""}' for msg in body.messages)

    await client.open_channel()
    await client.chat(prompt)  # 使用合并后的prompt
    if body.stream:
        async def event_generator():
        # 发送初始化消息
            initial_event = format_custom_event("", is_initial=True)
            yield initial_event
            async for event_str in client.get_stream_reply():
                formatted_event = format_custom_event(event_str)
                yield formatted_event  # 每条消息前都会有'data: '
            final_event = format_custom_event("", is_final=True)
            yield final_event  # 添加换行符以分隔事件
            yield 'data: [DONE]\n\n'  # 发送终止事件

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    else:
        reply = await client.get_reply()
        formatted_response = format_response(reply)
        return formatted_response  # 在无stream的情况下返回常规JSON响应


@app.post("/claude/reset", dependencies=[Depends(must_token)])
async def chat():
    await client.open_channel()
    await client.chat("请忘记上面的会话内容")

    return {
        "claude": await client.get_reply()
    }

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8089)
