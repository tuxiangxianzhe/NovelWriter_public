# gradio_stub.py
# -*- coding: utf-8 -*-
"""
极简 Gradio 桩模块，仅用于在无 Gradio 环境下让 web_server.py 成功导入。
FastAPI 路由使用 ProgressQueue 替代 gr.Progress()，不依赖真实 Gradio。
"""


class _Progress:
    """模拟 gr.Progress 的签名，实际不做任何事。"""
    def __call__(self, value=None, desc="", total=None):
        pass


class _Update(dict):
    """模拟 gr.update() 的返回值（一个 dict 子类）。"""


def update(**kwargs):
    return _Update(**kwargs)


def _noop(*args, **kwargs):
    return None


Progress = _Progress

# 常用组件的占位（仅需能被 import，不需实际工作）
class _Component:
    def __init__(self, *args, **kwargs): pass

Dropdown = Textbox = Checkbox = Slider = Button = Accordion = _Component
Row = Column = Tab = Tabs = Blocks = HTML = Markdown = File = _Component
Number = Radio = CheckboxGroup = State = _Component


class themes:
    class Soft:
        def __init__(self, *args, **kwargs): pass
