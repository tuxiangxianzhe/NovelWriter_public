# llm_adapters.py
# -*- coding: utf-8 -*-
import logging
from typing import Optional
from langchain_openai import ChatOpenAI, AzureChatOpenAI
# from google import genai
import google.generativeai as genai
# from google.genai import types
from google.generativeai import types
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference.models import SystemMessage, UserMessage
from openai import OpenAI
import requests


def check_base_url(url: str) -> str:
    """
    处理base_url的规则：
    1. 如果url以#结尾，则移除#并直接使用用户提供的url
    2. 否则检查是否需要添加/v1后缀
    """
    import re
    url = url.strip()
    if not url:
        return url
        
    if url.endswith('#'):
        return url.rstrip('#')
        
    if not re.search(r'/v\d+$', url):
        if '/v1' not in url:
            url = url.rstrip('/') + '/v1'
    return url

class BaseLLMAdapter:
    """
    统一的 LLM 接口基类，为不同后端（OpenAI、Ollama、ML Studio、Gemini等）提供一致的方法签名。
    """
    last_reasoning: str = ""  # 最近一次调用的思考过程（仅思考模型会填充）

    def invoke(self, prompt: str, system_message: str = "") -> str:
        raise NotImplementedError("Subclasses must implement .invoke(prompt) method.")

    def invoke_stream(self, prompt: str, system_message: str = ""):
        """流式调用 LLM，yield 文本片段。默认回退到非流式。"""
        result = self.invoke(prompt, system_message=system_message)
        if result:
            yield result

    def invoke_chat_stream(self, messages: list):
        """流式多轮对话。messages = [{"role": ..., "content": ...}, ...]
        默认回退：提取 system 和最后一条 user 消息，调用 invoke_stream。"""
        system_msg = ""
        user_msg = ""
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            if m["role"] == "user":
                user_msg = m["content"]
        yield from self.invoke_stream(user_msg, system_message=system_msg)

def _openai_chat_stream_helper(client, model_name, messages, max_tokens, temperature, timeout):
    """OpenAI 兼容接口的通用多轮对话流式调用辅助函数。"""
    stream = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def _openai_stream_helper(client, model_name, prompt, system_message, max_tokens, temperature, timeout):
    """OpenAI 兼容接口的通用流式调用辅助函数。
    client: openai.OpenAI 实例
    返回: generator，逐片段 yield 文本
    """
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})
    stream = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


class DeepSeekAdapter(BaseLLMAdapter):
    """
    适配官方/OpenAI兼容接口（使用 langchain.ChatOpenAI）
    """
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        self._client = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
            max_retries=0
        )
        self._raw_client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=0
        )

    def invoke(self, prompt: str, system_message: str = "") -> str:
        from langchain_core.messages import SystemMessage as LCSystemMessage, HumanMessage
        if system_message:
            messages = [LCSystemMessage(content=system_message), HumanMessage(content=prompt)]
            response = self._client.invoke(messages)
        else:
            response = self._client.invoke(prompt)
        if not response:
            logging.warning("No response from DeepSeekAdapter.")
            return ""
        return response.content

    def invoke_stream(self, prompt: str, system_message: str = ""):
        yield from _openai_stream_helper(
            self._raw_client, self.model_name, prompt, system_message,
            self.max_tokens, self.temperature, self.timeout
        )

    def invoke_chat_stream(self, messages: list):
        yield from _openai_chat_stream_helper(
            self._raw_client, self.model_name, messages,
            self.max_tokens, self.temperature, self.timeout
        )

class OpenAIAdapter(BaseLLMAdapter):
    """
    适配官方/OpenAI兼容接口（使用 langchain.ChatOpenAI）
    当 enable_thinking=True 时，改用原生 openai.OpenAI 客户端以支持
    thinking_budget 扩展参数，并记录思考过程到日志。
    """
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600, enable_thinking: bool = False, thinking_budget: int = 0):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget

        if self.enable_thinking:
            self._raw_client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=0
            )
            self._client = None
            logging.info(f"OpenAIAdapter: 启用思考模式, thinking_budget={self.thinking_budget}, model={self.model_name}")
        else:
            self._raw_client = None
            self._client = ChatOpenAI(
                model=self.model_name,
                api_key=self.api_key,
                base_url=self.base_url,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
                max_retries=0
            )

    def invoke(self, prompt: str, system_message: str = "") -> str:
        if self._raw_client:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            api_params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
            }
            if self.thinking_budget > 0:
                api_params["extra_body"] = {"thinking_budget": self.thinking_budget}
            response = self._raw_client.chat.completions.create(**api_params)
            if not response or not response.choices:
                logging.warning("No response from OpenAIAdapter (thinking mode).")
                return ""
            msg = response.choices[0].message
            # 从多种位置尝试获取 reasoning_content（不同 SDK 版本存放位置不同）
            reasoning = (
                getattr(msg, 'reasoning_content', None)
                or (msg.model_extra or {}).get('reasoning_content')
                or ""
            )
            self.last_reasoning = reasoning
            if reasoning:
                logging.info(f"[Thinking] 思考过程 ({len(reasoning)}字):\n{reasoning[:500]}{'...(截断)' if len(reasoning) > 500 else ''}")
            else:
                logging.info(f"[Thinking] 未获取到 reasoning_content, msg字段: {list(vars(msg).keys()) if hasattr(msg, '__dict__') else dir(msg)}")
            content = msg.content or ""
            if not content and reasoning:
                logging.warning("[Thinking] content 为空但有 reasoning_content, 可能模型仅返回了思考过程")
            return content
        else:
            self.last_reasoning = ""
            from langchain_core.messages import SystemMessage as LCSystemMessage, HumanMessage
            if system_message:
                messages = [LCSystemMessage(content=system_message), HumanMessage(content=prompt)]
                response = self._client.invoke(messages)
            else:
                response = self._client.invoke(prompt)
            if not response:
                logging.warning("No response from OpenAIAdapter.")
                return ""
            return response.content

    def invoke_stream(self, prompt: str, system_message: str = ""):
        if self._raw_client:
            # thinking 模式也支持流式
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            api_params = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "stream": True,
            }
            if self.thinking_budget > 0:
                api_params["extra_body"] = {"thinking_budget": self.thinking_budget}
            stream = self._raw_client.chat.completions.create(**api_params)
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            yield from _openai_stream_helper(
                OpenAI(base_url=self.base_url, api_key=self.api_key,
                       timeout=self.timeout, max_retries=0),
                self.model_name, prompt, system_message,
                self.max_tokens, self.temperature, self.timeout
            )

    def invoke_chat_stream(self, messages: list):
        if self._raw_client:
            yield from _openai_chat_stream_helper(
                self._raw_client, self.model_name, messages,
                self.max_tokens, self.temperature, self.timeout
            )
        else:
            raw = OpenAI(base_url=self.base_url, api_key=self.api_key,
                         timeout=self.timeout, max_retries=0)
            yield from _openai_chat_stream_helper(
                raw, self.model_name, messages,
                self.max_tokens, self.temperature, self.timeout
            )

class GeminiAdapter(BaseLLMAdapter):
    """
    适配 Google Gemini (Google Generative AI) 接口
    """

    # PenBo 修复新版本google-generativeai 不支持 Client 类问题；而是使用 GenerativeModel 类来访问API
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600):
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        # 配置API密钥
        genai.configure(api_key=self.api_key)
        
        # 创建生成模型实例
        self._model = genai.GenerativeModel(model_name=self.model_name)

    def invoke(self, prompt: str, system_message: str = "") -> str:
        try:
            # 设置生成配置
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            # Gemini 通过 system_instruction 注入 system message
            effective_prompt = prompt
            if system_message:
                effective_prompt = f"{system_message}\n\n{prompt}"

            # 生成内容
            response = self._model.generate_content(
                effective_prompt,
                generation_config=generation_config
            )

            if response and response.text:
                return response.text
            else:
                logging.warning("No text response from Gemini API.")
                return ""
        except Exception as e:
            logging.error(f"Gemini API 调用失败: {e}")
            return ""

class AzureOpenAIAdapter(BaseLLMAdapter):
    """
    适配 Azure OpenAI 接口（使用 langchain.ChatOpenAI）
    """
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600):
        import re
        match = re.match(r'https://(.+?)/openai/deployments/(.+?)/chat/completions\?api-version=(.+)', base_url)
        if match:
            self.azure_endpoint = f"https://{match.group(1)}"
            self.azure_deployment = match.group(2)
            self.api_version = match.group(3)
        else:
            raise ValueError("Invalid Azure OpenAI base_url format")
        
        self.api_key = api_key
        self.model_name = self.azure_deployment
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        self._client = AzureChatOpenAI(
            azure_endpoint=self.azure_endpoint,
            azure_deployment=self.azure_deployment,
            api_version=self.api_version,
            api_key=self.api_key,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
            max_retries=0
        )

    def invoke(self, prompt: str, system_message: str = "") -> str:
        from langchain_core.messages import SystemMessage as LCSystemMessage, HumanMessage
        if system_message:
            messages = [LCSystemMessage(content=system_message), HumanMessage(content=prompt)]
            response = self._client.invoke(messages)
        else:
            response = self._client.invoke(prompt)
        if not response:
            logging.warning("No response from AzureOpenAIAdapter.")
            return ""
        return response.content

class OllamaAdapter(BaseLLMAdapter):
    """
    Ollama 同样有一个 OpenAI-like /v1/chat 接口，可直接使用 ChatOpenAI。
    """
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        if self.api_key == '':
            self.api_key= 'ollama'

        self._client = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
            max_retries=0
        )

    def invoke(self, prompt: str, system_message: str = "") -> str:
        from langchain_core.messages import SystemMessage as LCSystemMessage, HumanMessage
        if system_message:
            messages = [LCSystemMessage(content=system_message), HumanMessage(content=prompt)]
            response = self._client.invoke(messages)
        else:
            response = self._client.invoke(prompt)
        if not response:
            logging.warning("No response from OllamaAdapter.")
            return ""
        return response.content

    def invoke_stream(self, prompt: str, system_message: str = ""):
        raw = OpenAI(base_url=self.base_url, api_key=self.api_key,
                     timeout=self.timeout, max_retries=0)
        yield from _openai_stream_helper(
            raw, self.model_name, prompt, system_message,
            self.max_tokens, self.temperature, self.timeout
        )

    def invoke_chat_stream(self, messages: list):
        raw = OpenAI(base_url=self.base_url, api_key=self.api_key,
                     timeout=self.timeout, max_retries=0)
        yield from _openai_chat_stream_helper(
            raw, self.model_name, messages,
            self.max_tokens, self.temperature, self.timeout
        )

class MLStudioAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        self._client = ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            timeout=self.timeout,
            max_retries=0
        )

    def invoke(self, prompt: str, system_message: str = "") -> str:
        try:
            from langchain_core.messages import SystemMessage as LCSystemMessage, HumanMessage
            if system_message:
                messages = [LCSystemMessage(content=system_message), HumanMessage(content=prompt)]
                response = self._client.invoke(messages)
            else:
                response = self._client.invoke(prompt)
            if not response:
                logging.warning("No response from MLStudioAdapter.")
                return ""
            return response.content
        except Exception as e:
            logging.error(f"ML Studio API 调用超时或失败: {e}")
            return ""

class AzureAIAdapter(BaseLLMAdapter):
    """
    适配 Azure AI Inference 接口，用于访问Azure AI服务部署的模型
    使用 azure-ai-inference 库进行API调用
    """
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600):
        import re
        # 匹配形如 https://xxx.services.ai.azure.com/models/chat/completions?api-version=xxx 的URL
        match = re.match(r'https://(.+?)\.services\.ai\.azure\.com(?:/models)?(?:/chat/completions)?(?:\?api-version=(.+))?', base_url)
        if match:
            # endpoint需要是形如 https://xxx.services.ai.azure.com/models 的格式
            self.endpoint = f"https://{match.group(1)}.services.ai.azure.com/models"
            # 如果URL中包含api-version参数，使用它；否则使用默认值
            self.api_version = match.group(2) if match.group(2) else "2024-05-01-preview"
        else:
            raise ValueError("Invalid Azure AI base_url format. Expected format: https://<endpoint>.services.ai.azure.com/models/chat/completions?api-version=xxx")
        
        self.base_url = self.endpoint  # 存储处理后的endpoint URL
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        self._client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key),
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout
        )

    def invoke(self, prompt: str, system_message: str = "") -> str:
        try:
            sys_msg = system_message if system_message else "You are a helpful assistant."
            response = self._client.complete(
                messages=[
                    SystemMessage(sys_msg),
                    UserMessage(prompt)
                ]
            )
            if response and response.choices:
                return response.choices[0].message.content
            else:
                logging.warning("No response from AzureAIAdapter.")
                return ""
        except Exception as e:
            logging.error(f"Azure AI Inference API 调用失败: {e}")
            return ""

# 火山引擎实现
class VolcanoEngineAIAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=0
        )
    def invoke(self, prompt: str, system_message: str = "") -> str:
        try:
            sys_msg = system_message if system_message else "你是DeepSeek，是一个 AI 人工智能助手"
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": prompt},
                ],
                timeout=self.timeout
            )
            if not response:
                logging.warning("No response from VolcanoEngineAIAdapter.")
                return ""
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"火山引擎API调用超时或失败: {e}")
            return ""

    def invoke_stream(self, prompt: str, system_message: str = ""):
        yield from _openai_stream_helper(
            self._client, self.model_name, prompt,
            system_message or "你是DeepSeek，是一个 AI 人工智能助手",
            self.max_tokens, self.temperature, self.timeout
        )

class SiliconFlowAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600, enable_thinking: bool = False, thinking_budget: int = 0):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget

        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=0
        )
    def invoke(self, prompt: str, system_message: str = "") -> str:
        try:
            sys_msg = system_message if system_message else "你是DeepSeek，是一个 AI 人工智能助手"
            api_params = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": prompt},
                ],
                "timeout": self.timeout
            }

            if self.enable_thinking and self.thinking_budget > 0:
                api_params["extra_body"] = {"thinking_budget": self.thinking_budget}
                logging.info(f"启用思考模式，thinking_budget={self.thinking_budget}")

            response = self._client.chat.completions.create(**api_params)

            if not response:
                logging.warning("No response from SiliconFlowAdapter.")
                return ""
            msg = response.choices[0].message
            reasoning = (
                getattr(msg, 'reasoning_content', None)
                or (msg.model_extra or {}).get('reasoning_content')
                or ""
            )
            self.last_reasoning = reasoning
            if reasoning:
                logging.info(f"[Thinking] 思考过程 ({len(reasoning)}字):\n{reasoning[:500]}{'...(截断)' if len(reasoning) > 500 else ''}")
            content = msg.content or ""
            if not content and reasoning:
                logging.warning("[Thinking] content 为空但有 reasoning_content, 可能模型仅返回了思考过程")
            return content
        except Exception as e:
            logging.error(f"硅基流动API调用超时或失败: {e}")
            return ""

    def invoke_stream(self, prompt: str, system_message: str = ""):
        yield from _openai_stream_helper(
            self._client, self.model_name, prompt,
            system_message or "你是DeepSeek，是一个 AI 人工智能助手",
            self.max_tokens, self.temperature, self.timeout
        )

    def invoke_chat_stream(self, messages: list):
        yield from _openai_chat_stream_helper(
            self._client, self.model_name, messages,
            self.max_tokens, self.temperature, self.timeout
        )

# grok實現
class GrokAdapter(BaseLLMAdapter):
    """
    适配 xAI Grok API
    """
    def __init__(self, api_key: str, base_url: str, model_name: str, max_tokens: int, temperature: float = 0.7, timeout: Optional[int] = 600):
        self.base_url = check_base_url(base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        self._client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=0
        )

    def invoke(self, prompt: str, system_message: str = "") -> str:
        try:
            sys_msg = system_message if system_message else "You are Grok, created by xAI."
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )
            if response and response.choices:
                return response.choices[0].message.content
            else:
                logging.warning("No response from GrokAdapter.")
                return ""
        except Exception as e:
            logging.error(f"Grok API 调用失败: {e}")
            return ""

    def invoke_stream(self, prompt: str, system_message: str = ""):
        yield from _openai_stream_helper(
            self._client, self.model_name, prompt,
            system_message or "You are Grok, created by xAI.",
            self.max_tokens, self.temperature, self.timeout
        )

    def invoke_chat_stream(self, messages: list):
        yield from _openai_chat_stream_helper(
            self._client, self.model_name, messages,
            self.max_tokens, self.temperature, self.timeout
        )

def create_llm_adapter(
    interface_format: str,
    base_url: str,
    model_name: str,
    api_key: str,
    temperature: float,
    max_tokens: int,
    timeout: int,
    enable_thinking: bool = False,
    thinking_budget: int = 0
) -> BaseLLMAdapter:
    """
    工厂函数：根据 interface_format 返回不同的适配器实例。
    """
    fmt = interface_format.strip().lower()
    if fmt == "deepseek":
        return DeepSeekAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    elif fmt == "openai":
        return OpenAIAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout, enable_thinking, thinking_budget)
    elif fmt == "azure openai":
        return AzureOpenAIAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    elif fmt == "azure ai":
        return AzureAIAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    elif fmt == "ollama":
        return OllamaAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    elif fmt == "ml studio":
        return MLStudioAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    elif fmt == "gemini":
        return GeminiAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    elif fmt == "阿里云百炼":
        return OpenAIAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout, enable_thinking, thinking_budget)
    elif fmt == "火山引擎":
        return VolcanoEngineAIAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    elif fmt == "硅基流动":
        return SiliconFlowAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout, enable_thinking, thinking_budget)
    elif fmt == "grok":
        return GrokAdapter(api_key, base_url, model_name, max_tokens, temperature, timeout)
    else:
        raise ValueError(f"Unknown interface_format: {interface_format}")
