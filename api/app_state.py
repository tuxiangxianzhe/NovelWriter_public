# api/app_state.py
# -*- coding: utf-8 -*-
"""全局应用状态：NovelGeneratorWeb 单例"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

_web_app = None


def get_web_app():
    """懒加载 NovelGeneratorWeb 单例"""
    global _web_app
    if _web_app is None:
        import sys
        import os

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, root)

        # 若 gradio 未安装，注入桩模块使 web_server.py 可以正常导入
        if 'gradio' not in sys.modules:
            try:
                import gradio  # noqa: F401
            except ImportError:
                import importlib.util
                stub_path = os.path.join(root, 'gradio_stub.py')
                spec = importlib.util.spec_from_file_location('gradio', stub_path)
                stub = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(stub)
                sys.modules['gradio'] = stub

        from web_server import NovelGeneratorWeb
        _web_app = NovelGeneratorWeb()
    return _web_app
