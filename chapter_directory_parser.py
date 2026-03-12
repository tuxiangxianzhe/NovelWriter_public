# chapter_blueprint_parser.py
# -*- coding: utf-8 -*-
import re

# 中文数字映射
_CN_NUM = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
           '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
_CN_UNIT = {'十': 10, '百': 100, '千': 1000}
_CN_DIGITS = '零一二三四五六七八九十百千'


def _cn_to_arabic(s: str):
    """将中文数字字符串转为整数，支持 一 到 几千。"""
    s = s.strip()
    if not s:
        return None
    result = 0
    temp = 0
    for c in s:
        if c in _CN_NUM:
            temp = _CN_NUM[c]
        elif c in _CN_UNIT:
            unit = _CN_UNIT[c]
            if temp == 0:
                temp = 1  # 十 → 10
            result += temp * unit
            temp = 0
    result += temp
    return result if result > 0 else None


def _parse_chapter_header(line: str):
    """
    从行文本中解析 (章节号: int, 章节标题: str)，失败返回 None。
    支持以下格式变体：
      第1章 - 标题 / 第1章 - [标题] / 第1章：标题 / 第1章: 标题
      第1章 标题 / 第1章《标题》 / 第一章 - 标题
      **第1章 - 标题** / ### 第1章 标题 / 第1章—标题
    """
    # 去除 Markdown 格式标记（# 开头、** ** 包裹等）
    line = re.sub(r'^[\s#>]+', '', line)
    line = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', line)
    line = line.strip()

    # 匹配 "第X章" 标头，章号支持阿拉伯数字或中文数字
    pattern = re.compile(
        r'^第\s*(\d+|[' + _CN_DIGITS + r']+)\s*章'
        r'(?:\s*[-—–：:]\s*|\s*《\s*|\s+)?'   # 可选分隔符
        r'(.*?)$'                                # 章节标题内容（可为空）
    )
    m = pattern.match(line)
    if not m:
        return None

    num_str = m.group(1).strip()
    title = m.group(2).strip()

    # 清理标题两端的括号/引号
    title = re.sub(r'^[\[【《「『"\']+', '', title)
    title = re.sub(r'[\]】》」』"\'\*]+$', '', title)
    title = title.strip()

    # 解析章节号
    if num_str.isdigit():
        chapter_number = int(num_str)
    else:
        chapter_number = _cn_to_arabic(num_str)

    if not chapter_number or chapter_number <= 0:
        return None

    return chapter_number, title


def _make_field_pattern(label: str) -> re.Pattern:
    """
    生成字段匹配正则，同时兼容全角冒号 `：` 和半角冒号 `:`。
    label 中不含冒号，例如 "本章定位"。
    """
    return re.compile(r'^' + re.escape(label) + r'[：:]\s*\[?(.*?)\]?\s*$')


def parse_chapter_blueprint(blueprint_text: str):
    """
    解析整份章节蓝图文本，返回一个列表，每个元素是一个 dict：
    {
      "chapter_number": int,
      "chapter_title": str,
      "chapter_role": str,       # 本章定位
      "chapter_purpose": str,    # 核心作用
      "suspense_level": str,     # 悬念密度
      "foreshadowing": str,      # 伏笔操作
      "plot_twist_level": str,   # 认知颠覆 / 官能强度
      "chapter_summary": str     # 本章简述
    }
    """

    # 先按空行进行分块，以免多章之间混淆
    chunks = re.split(r'\n\s*\n', blueprint_text.strip())
    results = []

    role_pattern       = _make_field_pattern('本章定位')
    purpose_pattern    = _make_field_pattern('核心作用')
    suspense_pattern   = _make_field_pattern('悬念密度')
    foreshadow_pattern = _make_field_pattern('伏笔操作')
    twist_pattern      = re.compile(r'^(?:认知颠覆|官能强度)[：:]\s*\[?(.*?)\]?\s*$')
    chars_pattern      = _make_field_pattern('涉及角色')
    summary_pattern    = _make_field_pattern('本章简述')

    for chunk in chunks:
        lines = chunk.strip().splitlines()
        if not lines:
            continue

        chapter_number      = None
        chapter_title       = ""
        chapter_role        = ""
        chapter_purpose     = ""
        suspense_level      = ""
        foreshadowing       = ""
        plot_twist_level    = ""
        characters_involved = ""
        chapter_summary     = ""

        # 尝试在前几行中找章节头（兼容标题前有空行或额外行的情况）
        header_found = False
        body_start = 1
        for i, line in enumerate(lines[:3]):
            parsed = _parse_chapter_header(line.strip())
            if parsed:
                chapter_number, chapter_title = parsed
                header_found = True
                body_start = i + 1
                break

        if not header_found:
            continue

        # 从剩余行匹配字段
        summary_lines = []
        in_summary = False
        for line in lines[body_start:]:
            line_stripped = line.strip()
            if not line_stripped:
                if in_summary:
                    summary_lines.append('')
                continue

            m_role = role_pattern.match(line_stripped)
            if m_role:
                in_summary = False
                chapter_role = m_role.group(1).strip()
                continue

            m_purpose = purpose_pattern.match(line_stripped)
            if m_purpose:
                in_summary = False
                chapter_purpose = m_purpose.group(1).strip()
                continue

            m_suspense = suspense_pattern.match(line_stripped)
            if m_suspense:
                in_summary = False
                suspense_level = m_suspense.group(1).strip()
                continue

            m_foreshadow = foreshadow_pattern.match(line_stripped)
            if m_foreshadow:
                in_summary = False
                foreshadowing = m_foreshadow.group(1).strip()
                continue

            m_twist = twist_pattern.match(line_stripped)
            if m_twist:
                in_summary = False
                plot_twist_level = m_twist.group(1).strip()
                continue

            m_chars = chars_pattern.match(line_stripped)
            if m_chars:
                in_summary = False
                characters_involved = m_chars.group(1).strip()
                continue

            m_summary = summary_pattern.match(line_stripped)
            if m_summary:
                in_summary = True
                first_line = m_summary.group(1).strip()
                if first_line:
                    summary_lines = [first_line]
                continue

            # 如果已进入本章简述，后续非字段行视为简述续行
            if in_summary:
                summary_lines.append(line_stripped)

        if summary_lines:
            chapter_summary = ' '.join(l for l in summary_lines if l)

        results.append({
            "chapter_number": chapter_number,
            "chapter_title": chapter_title,
            "chapter_role": chapter_role,
            "chapter_purpose": chapter_purpose,
            "suspense_level": suspense_level,
            "foreshadowing": foreshadowing,
            "plot_twist_level": plot_twist_level,
            "characters_involved": characters_involved,
            "chapter_summary": chapter_summary
        })

    # 按照 chapter_number 排序后返回
    results.sort(key=lambda x: x["chapter_number"])
    return results


def get_chapter_info_from_blueprint(blueprint_text: str, target_chapter_number: int):
    """
    在已经加载好的章节蓝图文本中，找到对应章号的结构化信息，返回一个 dict。
    若找不到则返回一个默认的结构。
    """
    all_chapters = parse_chapter_blueprint(blueprint_text)
    for ch in all_chapters:
        if ch["chapter_number"] == target_chapter_number:
            return ch
    # 默认返回
    return {
        "chapter_number": target_chapter_number,
        "chapter_title": f"第{target_chapter_number}章",
        "chapter_role": "",
        "chapter_purpose": "",
        "suspense_level": "",
        "foreshadowing": "",
        "plot_twist_level": "",
        "characters_involved": "",
        "chapter_summary": ""
    }
