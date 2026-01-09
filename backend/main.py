"""
AI翻译助手后端 - FastAPI
调用通义千问API进行中英翻译
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(title="AI翻译助手", description="中英翻译服务")

# 配置CORS，允许Flutter Web访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class TranslateRequest(BaseModel):
    text: str

# 响应模型
class TranslateResponse(BaseModel):
    translation: str
    keywords: list[str]

# 通义千问API配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"


async def call_qwen_api(text: str) -> dict:
    """调用通义千问API进行翻译"""
    
    if not DASHSCOPE_API_KEY:
        raise HTTPException(status_code=500, detail="未配置DASHSCOPE_API_KEY")
    
    prompt = f"""请将以下中文翻译成英文，并提取3个关键词。

要翻译的中文内容：
{text}

请严格按照以下JSON格式返回结果，不要添加任何其他内容：
{{"translation": "英文翻译结果", "keywords": ["关键词1", "关键词2", "关键词3"]}}
"""
    
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "glm-4.7",
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的中英翻译专家。请将用户提供的中文翻译成准确、流畅的英文，并提取关键词。只返回JSON格式结果。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                DASHSCOPE_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # 解析返回的内容
            content = result["choices"][0]["message"]["content"]
            
            # 尝试解析JSON
            import json
            # 清理可能的markdown代码块标记
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            parsed = json.loads(content)
            return parsed
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"API调用失败: {str(e)}")
        except json.JSONDecodeError:
            # 如果解析失败，返回原始内容作为翻译
            return {
                "translation": content,
                "keywords": ["翻译", "内容", "结果"]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@app.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """翻译接口：将中文翻译成英文并提取关键词"""
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="翻译内容不能为空")
    
    result = await call_qwen_api(request.text)
    
    return TranslateResponse(
        translation=result.get("translation", ""),
        keywords=result.get("keywords", [])
    )


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "message": "AI翻译助手服务运行中"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
