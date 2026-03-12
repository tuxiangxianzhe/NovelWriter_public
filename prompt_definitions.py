# prompt_definitions.py
# -*- coding: utf-8 -*-
"""
集中存放所有提示词 (Prompt)，整合雪花写作法、角色弧光理论、悬念三要素模型等
并包含新增加的前三章摘要/下一章关键字提炼提示词，以及章节正文写作提示词。

支持提示词预设方案的加载、保存和切换。
"""

import os
import sys
import json
import logging
from utils import atomic_write_json

# ============================================================
# 所有提示词的 key 列表（共17个）
# ============================================================
PROMPT_KEYS = [
    "core_seed_prompt",
    "character_dynamics_prompt",
    "world_building_prompt",
    "plot_architecture_prompt",
    "create_character_state_prompt",
    "chapter_blueprint_prompt",
    "chunked_chapter_blueprint_prompt",
    "first_chapter_draft_prompt",
    "next_chapter_draft_prompt",
    "summarize_recent_chapters_prompt",
    "knowledge_search_prompt",
    "knowledge_filter_prompt",
    "summary_prompt",
    "update_character_state_prompt",
    "Character_Import_Prompt",
    "continuation_architecture_prompt",
    "continuation_characters_prompt",
    "continuation_arcs_prompt",
    "continuation_char_state_prompt",
    "continuation_seed_prompt",
    "continuation_world_prompt",
    "compress_summary_prompt",
    "compress_character_state_prompt",
    "compress_world_building_prompt",
    "style_analysis_prompt",
    "style_merge_prompt",
    "scene_expansion_prompt",
    "narrative_dna_analysis_prompt",
    "style_calibration_generate_prompt",
    "style_calibration_discriminate_prompt",
    "style_calibration_revise_prompt",
    "narrative_calibration_generate_prompt",
    "narrative_calibration_discriminate_prompt",
    "narrative_calibration_revise_prompt",
]

# 提示词中文名映射
PROMPT_DISPLAY_NAMES = {
    "core_seed_prompt": "核心种子设定",
    "character_dynamics_prompt": "角色动力学设定",
    "world_building_prompt": "世界构建矩阵",
    "plot_architecture_prompt": "情节架构",
    "create_character_state_prompt": "角色状态创建",
    "chapter_blueprint_prompt": "章节目录生成",
    "chunked_chapter_blueprint_prompt": "分块章节目录",
    "first_chapter_draft_prompt": "第一章草稿",
    "next_chapter_draft_prompt": "后续章节草稿",
    "summarize_recent_chapters_prompt": "章节摘要生成",
    "knowledge_search_prompt": "知识库检索",
    "knowledge_filter_prompt": "知识库过滤",
    "summary_prompt": "前文摘要更新",
    "update_character_state_prompt": "角色状态更新",
    "Character_Import_Prompt": "角色导入",
    "continuation_architecture_prompt": "续写架构生成",
    "continuation_characters_prompt": "续写新增角色",
    "continuation_arcs_prompt": "续写新增剧情弧",
    "continuation_char_state_prompt": "续写新角色状态",
    "continuation_seed_prompt": "续写方向大纲",
    "continuation_world_prompt": "续写世界观扩展",
    "compress_summary_prompt": "压缩前文摘要",
    "compress_character_state_prompt": "压缩角色状态",
    "compress_world_building_prompt": "压缩世界观",
    "style_analysis_prompt": "文风分析",
    "style_merge_prompt": "文风融合",
    "scene_expansion_prompt": "场景扩写",
    "narrative_dna_analysis_prompt": "叙事DNA分析",
    "style_calibration_generate_prompt": "文风校准-测试生成",
    "style_calibration_discriminate_prompt": "文风校准-风格判别",
    "style_calibration_revise_prompt": "文风校准-指令修订",
    "narrative_calibration_generate_prompt": "叙事校准-测试生成",
    "narrative_calibration_discriminate_prompt": "叙事校准-模式判别",
    "narrative_calibration_revise_prompt": "叙事校准-指令修订",
}

# ============================================================
# 默认提示词内容（内置于代码，作为 fallback）
# ============================================================
_DEFAULT_PROMPTS = {}

# =============== 生成草稿提示词当前章节摘要、知识库提炼 ===============
_DEFAULT_PROMPTS["summarize_recent_chapters_prompt"] = """\
作为一名专业的小说编辑和知识管理专家，正在基于已完成的前三章内容和本章信息生成当前章节的精准摘要。请严格遵循以下工作流程：
前三章内容：
{combined_text}

当前章节信息：
第{novel_number}章《{chapter_title}》：
├── 本章定位：{chapter_role}
├── 核心作用：{chapter_purpose}
├── 悬念密度：{suspense_level}
├── 伏笔操作：{foreshadowing}
├── 认知颠覆：{plot_twist_level}
└── 本章简述：{chapter_summary}

下一章信息：
第{next_chapter_number}章《{next_chapter_title}》：
├── 本章定位：{next_chapter_role}
├── 核心作用：{next_chapter_purpose}
├── 悬念密度：{next_chapter_suspense_level}
├── 伏笔操作：{next_chapter_foreshadowing}
├── 认知颠覆：{next_chapter_plot_twist_level}
└── 本章简述：{next_chapter_summary}

**上下文分析阶段**：
1. 回顾前三章核心内容：
   - 第一章核心要素：[章节标题]→[核心冲突/理论]→[关键人物/概念]
   - 第二章发展路径：[已建立的人物关系]→[技术/情节进展]→[遗留伏笔]
   - 第三章转折点：[新出现的变量]→[世界观扩展]→[待解决问题]
2. 提取延续性要素：
   - 必继承要素：列出前3章中必须延续的3个核心设定
   - 可调整要素：识别2个允许适度变化的辅助设定

**当前章节摘要生成规则**：
1. 内容架构：
   - 继承权重：70%内容需与前3章形成逻辑递进
   - 创新空间：30%内容可引入新要素，但需标注创新类型（如：技术突破/人物黑化）
2. 结构控制：
   - 采用"承继→发展→铺垫"三段式结构
   - 每段含1个前文呼应点+1个新进展
3. 预警机制：
   - 若检测到与前3章设定冲突，用[!]标记并说明
   - 对开放式发展路径，提供2种合理演化方向

现在请你基于目前故事的进展，完成以下两件事：
用最多800字，写一个简洁明了的「当前章节摘要」；

请按如下格式输出（不需要额外解释）：
当前章节摘要: <这里写当前章节摘要>
"""

_DEFAULT_PROMPTS["knowledge_search_prompt"] = """\
请基于以下当前写作需求，生成合适的知识库检索关键词：

章节元数据：
- 准备创作：第{chapter_number}章
- 章节主题：{chapter_title}
- 核心人物：{characters_involved}
- 关键道具：{key_items}
- 场景位置：{scene_location}

写作目标：
- 本章定位：{chapter_role}
- 核心作用：{chapter_purpose}
- 伏笔操作：{foreshadowing}

当前摘要：
{short_summary}

- 用户指导：
{user_guidance}

- 核心人物(可能未指定)：{characters_involved}
- 关键道具(可能未指定)：{key_items}
- 空间坐标(可能未指定)：{scene_location}
- 时间压力(可能未指定)：{time_constraint}

生成规则：

1.关键词组合逻辑：
-类型1：[实体]+[属性]（如"量子计算机 故障日志"）
-类型2：[事件]+[后果]（如"实验室爆炸 辐射泄漏"）
-类型3：[地点]+[特征]（如"地下城 氧气循环系统"）

2.优先级：
-首选用户指导中明确提及的术语
-次选当前章节涉及的核心道具/地点
-最后补充可能关联的扩展概念

3.过滤机制：
-排除抽象程度高于"中级"的概念
-排除与前3章重复率超60%的词汇

请生成3-5组检索词，按优先级降序排列。
格式：每组用"·"连接2-3个关键词，每组占一行

示例：
科技公司·数据泄露
地下实验室·基因编辑·禁忌实验
"""

_DEFAULT_PROMPTS["knowledge_filter_prompt"] = """\
对知识库内容进行三级过滤：

待过滤内容：
{retrieved_texts}

当前叙事需求：
{chapter_info}

过滤流程：

冲突检测：

删除与已有摘要重复度＞40%的内容

标记存在世界观矛盾的内容（使用▲前缀）

价值评估：

关键价值点（❗标记）：
· 提供新的角色关系可能性
· 包含可转化的隐喻素材
· 存在至少2个可延伸的细节锚点

次级价值点（·标记）：
· 补充环境细节
· 提供技术/流程描述

结构重组：

按"情节燃料/人物维度/世界碎片/叙事技法"分类

为每个分类添加适用场景提示（如"可用于XX类型伏笔"）

输出格式：
[分类名称]→[适用场景]
❗/· [内容片段] （▲冲突提示）
...

示例：
[情节燃料]→可用于时间压力类悬念
❗ 地下氧气系统剩余23%储量（可制造生存危机）
▲ 与第三章提到的"永久生态循环系统"存在设定冲突

仅给出最终文本，不要解释任何内容。
提示词：内容
"""

# =============== 1. 核心种子设定（雪花第1层）===================
_DEFAULT_PROMPTS["core_seed_prompt"] = """\
作为专业作家，请用"雪花写作法"第一步构建故事核心：
主题：{topic}
类型：{genre}
篇幅：约{number_of_chapters}章（每章{word_number}字）

请用单句公式概括故事本质，例如：
"当[主角]遭遇[核心事件]，必须[关键行动]，否则[灾难后果]；与此同时，[隐藏的更大危机]正在发酵。"

要求：
1. 必须包含显性冲突与潜在危机
2. 体现人物核心驱动力
3. 暗示世界观关键矛盾
4. 使用25-100字精准表达

仅返回故事核心文本，不要解释任何内容。
"""

# =============== 2. 角色动力学设定（角色弧光模型）===================
_DEFAULT_PROMPTS["character_dynamics_prompt"] = """\
基于以下元素：
- 内容指导：{user_guidance}
- 核心种子：{core_seed}

请设计{num_characters}个具有动态变化潜力的核心角色，每个角色需包含：
特征：
- 背景、外貌、性别、年龄、职业等
- 暗藏的秘密或潜在弱点(可与世界观或其他角色有关)

核心驱动力三角：
- 表面追求（物质目标）
- 深层渴望（情感需求）
- 灵魂需求（哲学层面）

角色弧线设计：
初始状态 → 触发事件 → 认知失调 → 蜕变节点 → 最终状态

关系冲突网：
- 与其他角色的关系或对立点
- 与至少两个其他角色的价值观冲突
- 一个合作纽带
- 一个隐藏的背叛可能性

要求：
仅给出最终文本，不要解释任何内容。
"""

# =============== 3. 世界构建矩阵（三维度交织法）===================
_DEFAULT_PROMPTS["world_building_prompt"] = """\
基于以下元素：
- 内容指导：{user_guidance}
- 核心冲突："{core_seed}"

为服务上述内容，请构建三维交织的世界观：

1. 物理维度：
- 空间结构（地理×社会阶层分布图）
- 时间轴（关键历史事件年表）
- 法则体系（物理/魔法/社会规则的漏洞点）

2. 社会维度：
- 权力结构断层线（可引发冲突的阶层/种族/组织矛盾）
- 文化禁忌（可被打破的禁忌及其后果）
- 经济命脉（资源争夺焦点）

3. 隐喻维度：
- 贯穿全书的视觉符号系统（如反复出现的意象）
- 氣候/环境变化映射的心理状态
- 建筑风格暗示的文明困境

要求：
每个维度至少包含3个可与角色决策产生互动的动态元素。
仅给出最终文本，不要解释任何内容。
"""

# =============== 4. 情节架构（三幕式悬念）===================
_DEFAULT_PROMPTS["plot_architecture_prompt"] = """\
基于以下元素：
- 内容指导：{user_guidance}
- 核心种子：{core_seed}
- 角色体系：{character_dynamics}
- 世界观：{world_building}

要求按以下结构设计：
第一幕（触发）
- 日常状态中的异常征兆（3处铺垫）
- 引出故事：展示主线、暗线、副线的开端
- 关键事件：打破平衡的催化剂（需改变至少3个角色的关系）
- 错误抉择：主角的认知局限导致的错误反应

第二幕（对抗）
- 剧情升级：主线+副线的交叉点
- 双重压力：外部障碍升级+内部挫折
- 虚假胜利：看似解决实则深化危机的转折点
- 灵魂黑夜：世界观认知颠覆时刻

第三幕（解决）
- 代价显现：解决危机必须牺牲的核心价值
- 嵌套转折：至少包含三层认知颠覆（表面解→新危机→终极抉择）
- 余波：留下2个开放式悬念因子

每个阶段需包含3个关键转折点及其对应的伏笔回收方案。
仅给出最终文本，不要解释任何内容。
"""

# =============== 5. 章节目录生成（悬念节奏曲线）===================
_DEFAULT_PROMPTS["chapter_blueprint_prompt"] = """\
基于以下元素：
- 内容指导：{user_guidance}
- 小说架构：
{novel_architecture}

设计{number_of_chapters}章的节奏分布：
1. 章节集群划分：
- 每3-5章构成一个悬念单元，包含完整的小高潮
- 单元之间设置"认知过山车"（连续2章紧张→1章缓冲）
- 关键转折章需预留多视角铺垫

2. 每章需明确：
- 章节定位（角色/事件/主题等）
- 核心悬念类型（信息差/道德困境/时间压力等）
- 情感基调迁移（如从怀疑→恐惧→决绝）
- 伏笔操作（埋设/强化/回收）
- 认知颠覆强度（1-5级）

输出格式示例：
第n章 - [标题]
本章定位：[角色/事件/主题/...]
核心作用：[详细描述本章核心事件流程，包括具体发生了什么、涉及哪些角色互动、关键转折点和细节]
悬念密度：[紧凑/渐进/爆发/...]
伏笔操作：埋设(A线索)→强化(B矛盾)...
认知颠覆：★☆☆☆☆
涉及角色：[角色A、角色B、角色C]
本章简述：[一句话概括]

第n+1章 - [标题]
本章定位：[角色/事件/主题/...]
核心作用：[详细描述本章核心事件流程，包括具体发生了什么、涉及哪些角色互动、关键转折点和细节]
悬念密度：[紧凑/渐进/爆发/...]
伏笔操作：埋设(A线索)→强化(B矛盾)...
认知颠覆：★☆☆☆☆
涉及角色：[角色A、角色B]
本章简述：[一句话概括]

要求：
- 核心作用须详细展开，包含具体事件流程、角色互动和关键细节，每章核心作用不少于80字。
- 其余字段使用精炼语言描述。
- 合理安排节奏，确保整体悬念曲线的连贯性。
- 在生成{number_of_chapters}章前不要出现结局章节。

仅给出最终文本，不要解释任何内容。
"""

_DEFAULT_PROMPTS["chunked_chapter_blueprint_prompt"] = """\
基于以下元素：
- 内容指导：{user_guidance}
- 小说架构：
{novel_architecture}

需要生成总共{number_of_chapters}章的节奏分布，

当前已有章节目录（若为空则说明是初始生成）：\n
{chapter_list}

现在请设计第{n}章到第{m}的节奏分布：
1. 章节集群划分：
- 每3-5章构成一个悬念单元，包含完整的小高潮
- 单元之间设置"认知过山车"（连续2章紧张→1章缓冲）
- 关键转折章需预留多视角铺垫

2. 每章需明确：
- 章节定位（角色/事件/主题等）
- 核心悬念类型（信息差/道德困境/时间压力等）
- 情感基调迁移（如从怀疑→恐惧→决绝）
- 伏笔操作（埋设/强化/回收）
- 认知颠覆强度（1-5级）

输出格式示例：
第n章 - [标题]
本章定位：[角色/事件/主题/...]
核心作用：[详细描述本章核心事件流程，包括具体发生了什么、涉及哪些角色互动、关键转折点和细节]
悬念密度：[紧凑/渐进/爆发/...]
伏笔操作：埋设(A线索)→强化(B矛盾)...
认知颠覆：★☆☆☆☆
涉及角色：[角色A、角色B、角色C]
本章简述：[一句话概括]

第n+1章 - [标题]
本章定位：[角色/事件/主题/...]
核心作用：[详细描述本章核心事件流程，包括具体发生了什么、涉及哪些角色互动、关键转折点和细节]
悬念密度：[紧凑/渐进/爆发/...]
伏笔操作：埋设(A线索)→强化(B矛盾)...
认知颠覆：★☆☆☆☆
涉及角色：[角色A、角色B]
本章简述：[一句话概括]

要求：
- 核心作用须详细展开，包含具体事件流程、角色互动和关键细节，每章核心作用不少于80字。
- 其余字段使用精炼语言描述。
- 合理安排节奏，确保整体悬念曲线的连贯性。
- 在生成{number_of_chapters}章前不要出现结局章节。

仅给出最终文本，不要解释任何内容。
"""

# =============== 6. 前文摘要更新 ===================
_DEFAULT_PROMPTS["summary_prompt"] = """\
以下是新完成的章节文本：
{chapter_text}

这是当前的前文摘要（可为空）：
{global_summary}

请根据本章新增内容，更新前文摘要。
要求：
- 保留既有重要信息，同时融入新剧情要点
- 以简洁、连贯的语言描述全书进展
- 客观描绘，不展开联想或解释
- 总字数控制在2000字以内

仅返回前文摘要文本，不要解释任何内容。
"""

# =============== 7. 角色状态更新 ===================
_DEFAULT_PROMPTS["create_character_state_prompt"] = """\
依据当前角色动力学设定：{character_dynamics}

请生成一个角色状态文档，内容格式：
例：
张三：
├──物品:
│  ├──青衫：一件破损的青色长袍，带有暗红色的污渍
│  └──寒铁长剑：一柄断裂的铁剑，剑身上刻有古老的符文
├──能力
│  ├──技能1：强大的精神感知能力：能够察觉到周围人的心中活动
│  └──技能2：无形攻击：能够释放一种无法被视觉捕捉的精神攻击
├──状态
│  ├──身体状态: 身材挺拔，穿着华丽的铠甲，面色冷峻
│  └──心理状态: 目前的心态比较平静，但内心隐藏着对柳溪镇未来掌控的野心和不安
├──主要角色间关系网
│  ├──李四：张三从小就与她有关联，对她的成长一直保持关注
│  └──王二：两人之间有着复杂的过去，最近因一场冲突而让对方感到威胁
├──触发或加深的事件
│  ├──村庄内突然出现不明符号：这个不明符号似乎在暗示柳溪镇即将发生重大事件
│  └──李四被刺穿皮肤：这次事件让两人意识到对方的强大实力，促使他们迅速离开队伍

角色名：
├──物品:
│  ├──某物(道具)：描述
│  └──XX长剑(武器)：描述
│   ...
├──能力
│  ├──技能1：描述
│  └──技能2：描述
│   ...
├──状态
│  ├──身体状态：描述
│  └──心理状态：描述
├──主要角色间关系网
│  ├──角色A：描述
│  └──角色B：描述
│   ...
├──触发或加深的事件
│  ├──事件1：描述
│  └──事件2：描述
    ...

新出场角色：
- (此处填写未来任何新增角色或临时出场人物的基本信息)

要求：
仅返回编写好的角色状态文本，不要解释任何内容。
"""

_DEFAULT_PROMPTS["update_character_state_prompt"] = """\
以下是新完成的章节文本：
{chapter_text}

这是当前的角色状态文档：
{old_state}

请更新主要角色状态，内容格式：
例：
张三：
├──物品:
│  ├──青衫：一件破损的青色长袍，带有暗红色的污渍
│  └──寒铁长剑：一柄断裂的铁剑，剑身上刻有古老的符文
├──能力
│  ├──技能1：强大的精神感知能力：能够察觉到周围人的心中活动
│  └──技能2：无形攻击：能够释放一种无法被视觉捕捉的精神攻击
├──状态
│  ├──身体状态: 身材挺拔，穿着华丽的铠甲，面色冷峻
│  └──心理状态: 目前的心态比较平静，但内心隐藏着对柳溪镇未来掌控的野心和不安
├──主要角色间关系网
│  ├──李四：张三从小就与她有关联，对她的成长一直保持关注
│  └──王二：两人之间有着复杂的过去，最近因一场冲突而让对方感到威胁
├──触发或加深的事件
│  ├──村庄内突然出现不明符号：这个不明符号似乎在暗示柳溪镇即将发生重大事件
│  └──李四被刺穿皮肤：这次事件让两人意识到对方的强大实力，促使他们迅速离开队伍

角色名：
├──物品:
│  ├──某物(道具)：描述
│  └──XX长剑(武器)：描述
│   ...
├──能力
│  ├──技能1：描述
│  └──技能2：描述
│   ...
├──状态
│  ├──身体状态：
│  └──心理状态：描述
│
├──主要角色间关系网
│  ├──李四：描述
│  └──王二：描述
│   ...
├──触发或加深的事件
│  ├──事件1：描述
│  └──事件2：描述
    ...

......

新出场角色：
- 任何新增角色或临时出场人物的基本信息，简要描述即可，不要展开，淡出视线的角色可删除。

要求：
- 请直接在已有文档基础上进行增删
- 不改变原有结构，语言尽量简洁、有条理

仅返回更新后的角色状态文本，不要解释任何内容。
"""

# =============== 8. 章节正文写作 ===================

_DEFAULT_PROMPTS["first_chapter_draft_prompt"] = """\
即将创作：第 {novel_number} 章《{chapter_title}》
本章定位：{chapter_role}
核心作用：{chapter_purpose}
悬念密度：{suspense_level}
伏笔操作：{foreshadowing}
认知颠覆：{plot_twist_level}
本章简述：{chapter_summary}

可用元素：
- 核心人物(可能未指定)：{characters_involved}
- 关键道具(可能未指定)：{key_items}
- 空间坐标(可能未指定)：{scene_location}
- 时间压力(可能未指定)：{time_constraint}

参考文档：
- 小说设定：
{novel_setting}

完成第 {novel_number} 章的正文，字数要求{word_number}字，至少设计下方2个或以上具有动态张力的场景：
1. 对话场景：
   - 潜台词冲突（表面谈论A，实际博弈B）
   - 权力关系变化（通过非对称对话长度体现）

2. 动作场景：
   - 环境交互细节（至少3个感官描写）
   - 节奏控制（短句加速+比喻减速）
   - 动作揭示人物隐藏特质

3. 心理场景：
   - 认知失调的具体表现（行为矛盾）
   - 隐喻系统的运用（连接世界观符号）
   - 决策前的价值天平描写

4. 环境场景：
   - 空间透视变化（宏观→微观→异常焦点）
   - 非常规感官组合（如"听见阳光的重量"）
   - 动态环境反映心理（环境与人物心理对应）

格式要求：
- 仅返回章节正文文本；
- 不使用分章节小标题；
- 不要使用markdown格式。

额外指导(可能未指定)：{user_guidance}
"""

_DEFAULT_PROMPTS["next_chapter_draft_prompt"] = """\
参考文档：
└── 前文摘要：
    {global_summary}

└── 前章结尾段：
    {previous_chapter_excerpt}

└── 用户指导：
    {user_guidance}

└── 角色状态：
    {character_state}

└── 当前章节摘要：
    {short_summary}
{world_building_block}

当前章节信息：
第{novel_number}章《{chapter_title}》：
├── 章节定位：{chapter_role}
├── 核心作用：{chapter_purpose}
├── 悬念密度：{suspense_level}
├── 伏笔设计：{foreshadowing}
├── 转折程度：{plot_twist_level}
├── 章节简述：{chapter_summary}
├── 字数要求：{word_number}字
├── 核心人物：{characters_involved}
├── 关键道具：{key_items}
├── 场景地点：{scene_location}
└── 时间压力：{time_constraint}

下一章节目录
第{next_chapter_number}章《{next_chapter_title}》：
├── 章节定位：{next_chapter_role}
├── 核心作用：{next_chapter_purpose}
├── 悬念密度：{next_chapter_suspense_level}
├── 伏笔设计：{next_chapter_foreshadowing}
├── 转折程度：{next_chapter_plot_twist_level}
└── 章节简述：{next_chapter_summary}

知识库参考：（按优先级应用）
{filtered_context}

🎯 知识库应用规则：
1. 内容分级：
   - 写作技法类（优先）：
     ▸ 场景构建模板
     ▸ 对话写作技巧
     ▸ 悬念营造手法
   - 设定资料类（选择性）：
     ▸ 独特世界观元素
     ▸ 未使用过的技术细节
   - 禁忌项类（必须规避）：
     ▸ 已在前文出现过的特定情节
     ▸ 重复的人物关系发展

2. 使用限制：
   ● 禁止直接复制已有章节的情节模式
   ● 历史章节内容仅允许：
     → 参照叙事节奏（不超过20%相似度）
     → 延续必要的人物反应模式（需改编30%以上）
   ● 第三方写作知识优先用于：
     → 增强场景表现力（占知识应用的60%以上）
     → 创新悬念设计（至少1处新技巧）

3. 冲突检测：
   ⚠️ 若检测到与历史章节重复：
     - 相似度>40%：必须重构叙事角度
     - 相似度20-40%：替换至少3个关键要素
     - 相似度<20%：允许保留核心概念但改变表现形式

依据前面所有设定，开始完成第 {novel_number} 章的正文，字数要求{word_number}字，
内容生成严格遵循：
-用户指导
-当前章节摘要
-当前章节信息
-无逻辑漏洞,
确保章节内容与前文摘要、前章结尾段衔接流畅、下一章目录保证上下文完整性，

格式要求：
- 仅返回章节正文文本；
- 不使用分章节小标题；
- 不要使用markdown格式。
"""

_DEFAULT_PROMPTS["Character_Import_Prompt"] = """\
根据以下文本内容，分析出所有角色及其属性信息，严格按照以下格式要求：

<<角色状态格式要求>>
1. 必须包含以下五个分类（按顺序）：
   ● 物品 ● 能力 ● 状态 ● 主要角色间关系网 ● 触发或加深的事件
2. 每个属性条目必须用【名称: 描述】格式
   例：├──青衫: 一件破损的青色长袍，带有暗红色的污渍
3. 状态必须包含：
   ● 身体状态: [当前身体状况]
   ● 心理状态: [当前心理状况]
4. 关系网格式：
   ● [角色名称]: [关系类型，如"竞争对手"/"盟友"]
5. 触发事件格式：
   ● [事件名称]: [简要描述及影响]

<<示例>>
李员外:
├──物品:
│  ├──青衫: 一件破损的青色长袍，带有暗红色污渍
│  └──寒铁长剑: 剑身有裂痕，刻有「青云」符文
├──能力:
│  ├──精神感知: 能感知半径30米内的生命体
│  └──剑气压制: 通过目光释放精神威压
├──状态:
│  ├──身体状态: 右臂有未愈合的刀伤
│  └──心理状态: 对苏明远的实力感到忌惮
├──主要角色间关系网:
│  ├──苏明远: 竞争对手，十年前的同僚
│  └──林婉儿: 暗中培养的继承人
├──触发或加深的事件:
│  ├──兵器库遇袭: 丢失三把传家宝剑，影响战力
│  └──匿名威胁信: 信纸带有檀香味，暗示内部泄密
│

请严格按上述格式分析以下内容：
<<待分析小说文本开始>>
{content}
<<待分析小说文本结束>>
"""


# =============== 9. 续写架构生成 ===================
_DEFAULT_PROMPTS["continuation_architecture_prompt"] = """\
你是一位资深的网络小说策划，擅长在已有故事基础上扩展新的剧情弧。

===== 已有架构 =====
{existing_architecture}

===== 前文摘要 =====
{global_summary}

===== 当前角色状态 =====
{character_state}

===== 续写要求 =====
新增章节数：{new_chapters} 章
用户构想：{user_guidance}

请基于上述已有内容，设计续写扩展方案，包含以下三部分：

一、新增角色设定
- 若用户构想中提及新角色，以此为基础设计
- 若未提及，根据剧情需要自由设计{num_characters}个新角色
- 每个新角色需包含：基础设定（姓名、身份、外貌特征）、核心驱动力、与已有角色的关系
- 新角色应与已有世界观和角色体系自然融合

二、新增剧情弧（根据新增章节数设计1-3个弧）
对每个新弧，设计：
- 弧名称与核心主题
- 核心冲突与悬念
- 弧内节奏规划（起承转合）
- 与已有剧情线的衔接点
- 新旧角色在此弧中的互动关系

三、新角色初始状态
按照已有角色状态文档的格式，为每个新增角色生成初始状态条目。

设计原则：
- 新弧应与已有故事保持风格统一、逻辑连贯
- 主角保持一致性，允许渐进式成长
- 最后一个新弧结尾保持开放，便于后续继续扩展
- 确保新旧角色关系网络的合理衔接

仅给出最终文本，不要解释任何内容。
"""

# =============== 9a. 续写分步：新增角色 ===================
_DEFAULT_PROMPTS["continuation_characters_prompt"] = """\
你是一位资深的网络小说策划，擅长在已有故事基础上设计新角色。

===== 已有架构 =====
{existing_architecture}

===== 前文摘要 =====
{global_summary}

===== 当前角色状态 =====
{character_state}

===== 续写要求 =====
新增章节数：{new_chapters} 章
用户构想：{user_guidance}

请基于上述已有内容，设计续写所需的新增角色。

新增角色设定：
- 若用户构想中提及新角色，以此为基础设计
- 若未提及，根据剧情需要自由设计{num_characters}个新角色
- 每个新角色需包含：基础设定（姓名、身份、外貌特征）、核心驱动力、与已有角色的关系
- 新角色应与已有世界观和角色体系自然融合

设计原则：
- 新角色需服务于后续新剧情弧的推进
- 与已有角色形成差异化
- 确保新旧角色关系网络的合理衔接

仅给出新增角色设定文本，不要解释任何内容。
"""

# =============== 9b. 续写分步：新增剧情弧 ===================
_DEFAULT_PROMPTS["continuation_arcs_prompt"] = """\
你是一位资深的网络小说策划，擅长在已有故事基础上扩展新的剧情弧。

===== 已有架构 =====
{existing_architecture}

===== 前文摘要 =====
{global_summary}

===== 当前角色状态 =====
{character_state}

===== 新增角色 =====
{new_characters}

===== 续写要求 =====
新增章节数：{new_chapters} 章
用户构想：{user_guidance}

请基于上述已有内容和新增角色，为 {new_chapters} 章的续写内容设计剧情弧。
弧数量建议：每3-5章构成一个弧为宜（例如续写5章可设计1-2个弧，续写10章可设计2-3个弧，续写20章可设计4-6个弧），请根据实际章节数灵活安排。
每个弧需标注其覆盖的章节范围（如"第N-M章"），所有弧的章节范围之和应恰好覆盖全部 {new_chapters} 章。

对每个新弧，设计：
- 弧名称与核心主题
- 覆盖章节范围（第X-Y章）
- 核心冲突与悬念（升级打怪、危机对抗等）
- 弧内节奏规划（起承转合）
- 与已有剧情线的衔接点
- 新旧角色在此弧中的互动关系

设计原则：
- 新弧应与已有故事保持风格统一、逻辑连贯
- 主角保持一致性，允许渐进式成长
- 最后一个新弧结尾保持开放，便于后续继续扩展
- 确保新旧角色关系网络的合理衔接

仅给出新增剧情弧文本，不要解释任何内容。
"""

# =============== 9c. 续写分步：新角色状态 ===================
_DEFAULT_PROMPTS["continuation_char_state_prompt"] = """\
依据以下新增角色设定：{new_characters}

请为这些新增角色生成登场时的初始角色状态文档，内容格式：
例：
张三：
├──物品:
│  ├──青衫：一件破损的青色长袍，带有暗红色的污渍
│  └──寒铁长剑：一柄断裂的铁剑，剑身上刻有古老的符文
├──能力
│  ├──技能1：强大的精神感知能力：能够察觉到周围人的心中活动
│  └──技能2：无形攻击：能够释放一种无法被视觉捕捉的精神攻击
├──状态
│  ├──身体状态: 身材挺拔，穿着华丽的铠甲，面色冷峻
│  └──心理状态: 心态比较平静，但内心隐藏着对柳溪镇未来掌控的野心和不安
├──主要角色间关系网
│  ├──李四：从小与她有关联，对她的成长一直保持关注
│  └──王二：两人之间有着复杂的过去
├──触发或加深的事件
│  └──暂无

要求：
- 仅根据角色设定生成登场时的初始状态，不要包含任何尚未发生的剧情内容
- 触发或加深的事件统一填写"暂无"
- 仅返回编写好的角色状态文本，不要解释任何内容。
"""

# =============== 9d. 压缩前文摘要 ===================
_DEFAULT_PROMPTS["compress_summary_prompt"] = """\
以下是当前的前文摘要：
{global_summary}

请对这份前文摘要进行语义压缩，目标字数控制在原文的50%左右。

压缩原则（网络小说向）：
1. 必须保留的内容：
   - 所有未解决的冲突、悬念与伏笔线索（埋设中/已强化但未回收的）
   - 主线与活跃副线的当前进展和局势
   - 主要角色的立场变化、阵营转换、关键决策
   - 升级体系/实力格局的当前状态（如有）
   - 势力关系与权力结构的最新变动
2. 可以精简的内容：
   - 已完结的支线：过程细节删除，仅保留一句话结果
   - 已回收的伏笔：删除埋设过程，仅保留回收结论
   - 早期铺垫章节的环境描写、日常互动细节
   - 已被后续事件覆盖的中间状态
3. 保持时间线清晰和因果逻辑完整，不要遗漏关键转折点

仅返回压缩后的摘要文本，不要解释任何内容。
"""

# =============== 9d2. 压缩角色状态 ===================
_DEFAULT_PROMPTS["compress_character_state_prompt"] = """\
以下是当前的角色状态文档：
{character_state}

请对这份角色状态文档进行语义压缩。

压缩原则（网络小说向）：
1. 主要角色（主角、核心配角）完整保留：
   - 当前物品/装备、能力/技能、身体和心理状态
   - 关系网中所有活跃关系
   - 未解决的个人线索和成长节点
2. "触发或加深的事件"精简：
   - 保留未解决或对后续剧情有影响的事件
   - 已完结事件（伏笔已回收、冲突已解决）用一句话概括或直接删除
   - 多个同类小事件可合并为一条
3. 次要角色（路人、已退场角色）：
   - 已退场且无后续影响的角色可整体删除
   - 仍有潜在影响的次要角色保留名字和一句话状态即可
4. 保持原有的树状格式不变（├──、│、└── 等）

仅返回压缩后的角色状态文本，不要解释任何内容。
"""

# =============== 9d3. 压缩世界观 ===================
_DEFAULT_PROMPTS["compress_world_building_prompt"] = """\
以下是当前的世界观设定文档：
{world_building}

请对这份世界观设定进行语义压缩，目标字数控制在原文的50%左右。

压缩原则（网络小说向）：
1. 物理维度（必须保留的内容）：
   - 当前活跃场景/地点的空间结构与地理信息
   - 仍在生效的法则体系（物理/魔法/社会规则）
   - 尚未被探索或揭示的空间留白
2. 社会维度（必须保留的内容）：
   - 当前活跃的权力结构与势力格局
   - 未被打破的文化禁忌及其潜在后果
   - 仍在争夺中的经济命脉/资源
3. 隐喻维度（必须保留的内容）：
   - 贯穿全书的视觉符号系统和反复出现的意象
   - 尚在发挥作用的环境-心理映射关系
4. 可以精简的内容：
   - 已被剧情推翻或覆盖的早期设定
   - 已完结事件中的具体场景描述（仅保留对世界观有持久影响的结论）
   - 多次续写扩展中重复或冗余的描述
   - 已不再活跃的势力/组织的详细描述（保留一句话存在感即可）
5. 保持三维度（物理/社会/隐喻）的结构完整性

仅返回压缩后的世界观设定文本，不要解释任何内容。
"""

# =============== 9e. 续写分步：续写方向简介 ===================
_DEFAULT_PROMPTS["continuation_seed_prompt"] = """\
你是一位资深的网络小说策划。请基于已有故事内容，为续写部分生成一段简明的"续写方向简介"，作为后续分步展开（世界观扩展、新增角色、剧情弧、角色状态更新）的指引信号。

===== 已有架构 =====
{existing_architecture}

===== 前文摘要 =====
{global_summary}

===== 当前角色状态 =====
{character_state}

===== 续写要求 =====
新增章节数：{new_chapters} 章
用户构想：{user_guidance}

请输出一段紧凑的续写方向简介（3-5 个段落），依次涵盖：
1. 续写核心方向：用 1-2 句话概括续写部分要做什么——核心冲突或发展重心是什么
2. 要延续/利用的关键伏笔与线索：从前文和角色状态中挑出后续需要接上的线头
3. 新引入元素的方向提示：若需引入新角色、新势力或新场景，只说方向，不展开设计
4. 整体基调与节奏倾向：简述续写章节的氛围和轻重缓急

要求：
- 简介应与已有故事风格统一、逻辑连贯
- 充分利用已有伏笔和未解决冲突
- 不要写详细剧情，不要设计具体角色，不要给出章节级别大纲——这些是后续步骤的任务
- 仅返回方向简介文本，不要解释任何内容。
"""

# =============== 9f. 续写分步：世界观扩展 ===================
_DEFAULT_PROMPTS["continuation_world_prompt"] = """\
你是一位资深的网络小说策划，擅长世界观扩展。

===== 已有架构 =====
{existing_architecture}

===== 前文摘要 =====
{global_summary}

===== 续写方向大纲 =====
{continuation_seed}

===== 续写要求 =====
新增章节数：{new_chapters} 章
用户构想：{user_guidance}

请基于续写方向，扩展世界观设定：

1. 新场景/地点：续写中可能涉及的新地理位置或场景空间
2. 新势力/组织：如果续写需要，设计新的势力格局变化
3. 规则/法则扩展：如果续写涉及新的能力、规则或社会制度变化
4. 环境氛围演变：随剧情推进，世界整体氛围、时代感的变化

要求：
- 与已有世界观自然衔接，不产生矛盾
- 只扩展续写实际需要的内容，不过度设定
- 若续写规模较小（5章以内），可简化或标注"无需扩展"
- 仅给出世界观扩展文本，不要解释任何内容。
"""

# =============== 10. 文风分析 ===================
_DEFAULT_PROMPTS["style_analysis_prompt"] = """\
你是一位资深的文学评论家和文体学专家。请对以下文本样本进行深入的文风分析。

===== 待分析文本 =====
{sample_text}

===== 分析维度 =====

请从以下五个维度进行系统分析：

1. 用词偏好
   - 词汇密度与丰富度（华丽/朴实、书面/口语）
   - 抽象词汇与具象词汇的比例
   - 是否带有方言色彩、时代感或特定领域术语
   - 高频词汇与标志性用词

2. 句式特征
   - 长短句偏好与节奏模式
   - 特定句式结构（如排比、倒装、省略等）
   - 叙述与对话的比例及对话风格
   - 段落结构与篇章节奏

3. 修辞手法
   - 隐喻/比喻的风格倾向（新奇/古典/日常化）
   - 描写侧重（心理描写/环境描写/动作描写的比重）
   - 感官描写的偏好（视觉/听觉/触觉/嗅觉/味觉）
   - 其他常用修辞（夸张、反讽、通感、留白等）

4. 叙事视角与语气
   - 人称选择与视角切换模式
   - 语调特征（冷静/讽刺/悲悯/激昂/温柔/冷硬等）
   - 作者介入程度（全知/有限/零度叙事）
   - 情感表达方式（直抒/克制/暗涌）

5. 独特指纹
   - 标志性语气词或口头禅
   - 特殊的衔接词使用习惯
   - 独特的节奏感与韵律
   - 其他使该文风区别于常规写作的显著特征

===== 输出要求 =====

请先输出结构化的完整分析报告（按上述5个维度逐一分析），然后在报告末尾输出一段精简的风格指令摘要。

风格指令摘要的要求：
- 以 [风格指令摘要] 作为标记
- 400-500字
- 将分析结论转化为可直接指导创作的风格指令
- 格式示例："以XX风格写作：使用……的句式，偏好……的词汇，语气……，擅长……的描写手法，节奏……"
"""

# =============== 11. 文风融合 ===================
_DEFAULT_PROMPTS["style_merge_prompt"] = """\
你是一位资深的文学评论家和文体学专家。现在需要将多种文风的优点融合为一种新的统一文风。

===== 待融合的文风 =====
{styles_info}

===== 用户偏好说明（可能为空）=====
{user_preference}

===== 任务要求 =====

请仔细分析每种文风的特点，将它们的优势融合为一种协调统一的新文风。融合时需注意：

1. 兼容性分析
   - 识别各文风之间可能冲突的特征（如一个偏长句、一个偏短句）
   - 对冲突特征提出折中方案或明确取舍

2. 融合策略
   - 从每种文风中提取最具辨识度和表现力的特征
   - 确保融合后的文风内部一致，不会出现风格割裂
   - 如果用户提供了偏好说明，优先按照用户意愿取舍

3. 输出要求
   - 先简要说明融合思路（各取了哪些特点、如何处理冲突）
   - 然后输出融合后的风格指令摘要

风格指令摘要的要求：
- 以 [风格指令摘要] 作为标记
- 400-500字
- 将融合结论转化为可直接指导创作的风格指令
- 格式示例："以XX风格写作：使用……的句式，偏好……的词汇，语气……，擅长……的描写手法，节奏……"
"""

# =============== 12. 场景扩写 ===================
_DEFAULT_PROMPTS["scene_expansion_prompt"] = """\
你是一位资深的小说编辑，擅长对已完成的章节进行场景扩写与细化。

===== 章节原文 =====
{chapter_text}

===== 官能/情感强度 =====
{sensuality_level}

===== 任务 =====
请识别上述章节中的关键场景（情感高潮、冲突爆发、亲密互动等），对其进行大幅扩写和细化：

扩写要素：
1. 感官细节：补充视觉、听觉、触觉、嗅觉等多维感官描写
2. 心理刻画：深化角色在关键时刻的内心活动与情感波动
3. 动作细化：将概括性的动作描写拆解为具体的连贯动作
4. 氛围渲染：通过环境、光线、声音等烘托场景情绪
5. 对话丰富：在适当处补充能体现角色性格的对话与潜台词

===== 禁止事项 =====
× 不准删减原文中的任何情节内容
× 不准改变原有的剧情走向和角色关系发展
× 不准用省略号或概括性语句代替具体描写
× 不准减少原文的篇幅，只能增加

===== 输出要求 =====
输出完整的扩写后章节文本（包含原有的非关键场景部分），不要解释任何内容。
"""

# =============== 13. 叙事DNA分析 ===================
_DEFAULT_PROMPTS["narrative_dna_analysis_prompt"] = """\
你是一位深度分析叙事模式的专业编辑。请对以下文本样本从叙事层面进行系统性分析，挖掘作者的叙事DNA——即那些超越文笔、体现在内容选择和故事推进上的深层模式。

===== 待分析文本 =====
{sample_text}

===== 分析维度 =====

请逐一分析以下7个维度，每个维度给出具体、可量化的结论：

1. **内容配比**
   - 纯情节推进 vs 亲密/情感场景的大致字数比例
   - 高张力/高潮场景在文本中的占比
   - 过渡/铺垫段落的平均长度

2. **推进节奏**
   - 从故事开始到出现实质性张力/冲突/亲密接触的铺垫长度（大约多少字/段落）
   - 情感/关系升温的典型步骤数和节奏感
   - 关键时刻（高潮/转折）前的紧张积累方式

3. **场景结构**
   - 高张力场景的固定内部结构（如：心理准备→外部动作→感官描写→情绪余韵的比例）
   - 场景收尾的习惯处理方式（淡出/切换/留白）
   - 单个高强度场景的典型长度

4. **角色关系模式**
   - 人物间权力关系的偏好（主导/对等/顺从）
   - 角色情感变化的触发机制（什么事件/言语引发转变）
   - 高频出现的角色性格特质组合

5. **玩法与场景偏好**
   - 高频出现的具体情境、场所类型
   - 反复使用的叙事道具或意象
   - 特定的情节套路或公式

6. **对话风格**
   - 高张力场景中对话的密度（对话vs叙事的比例）
   - 对话的直白程度、情感表达方式
   - 角色言语的标志性语气或口癖

7. **叙事视角偏好**
   - 高张力描写时的视角倾向（深度主观内心vs外部客观描述）
   - 感官描写的侧重（视觉/触觉/听觉/心理感受的比重）
   - 时间处理（慢镜头式细化 vs 快节奏跳接）

===== 输出格式 =====

[叙事DNA分析报告]
（详细分析以上7个维度，每个维度2-4句具体结论）

[架构指令]
（100-150字，面向情节架构和剧情弧设计：如何规划故事的整体节奏、内容配比、关键转折点的位置，使其符合作者叙事模式）

[蓝图指令]
（100-150字，面向章节蓝图规划：如何在各章节中分配张力密度、推进节奏和场景类型，使章节结构符合作者叙事模式）

[章节指令]
（150-200字，面向正文创作：如何在具体章节写作中体现作者的场景结构、对话风格、视角偏好和推进节奏）
"""

# =============== 14. 文风迭代校准 ===================

_DEFAULT_PROMPTS["style_calibration_generate_prompt"] = """\
你是一位技艺精湛的小说作家。请严格按照以下风格指令创作一段800-1200字的小说片段。

===== 风格指令 =====
{style_instruction}

===== 创作要求 =====
1. 场景：{scenario}
2. 必须包含：环境描写、人物心理活动、至少一段对话、动作描写。
3. 严格遵循上述风格指令中的所有要求（用词偏好、句式特征、修辞手法、叙事语气等）。
4. 不要解释你的创作思路，直接输出小说正文。

===== 输出 =====
直接输出小说片段正文，不要加任何标题或说明。
"""

_DEFAULT_PROMPTS["style_calibration_discriminate_prompt"] = """\
你是一位资深文体学盲测鉴定专家。现在进行一场图灵测试：你将看到三段文本，需要判断哪一段是AI仿写。

===== 参考文本 A（已确认为真实作品）=====
{reference_sample}

===== 文本一 =====
{text_one}

===== 文本二 =====
{text_two}

===== 鉴定任务 =====

文本一和文本二中，有一段是与参考文本A同一作者的真实作品，另一段是AI根据风格指令仿写的。
请从以下文风维度综合判断哪段是仿写：
1. 用词偏好：词汇密度、书面/口语倾向、标志性用词
2. 句式特征：长短句节奏、句式结构、段落节奏
3. 修辞手法：比喻风格、描写侧重、感官描写偏好
4. 叙事语气：视角、语调、情感表达方式
5. 独特指纹：语气词、衔接习惯、节奏韵律

===== 输出格式（严格遵守）=====

[判断结果]
A：文本一是仿写
B：文本二是仿写
C：无法判断

请输出 A 或 B 或 C 中的一个字母。

[分析依据]
（从上述5个维度逐一说明你的判断理由，具体指出哪些特征让你认为某段是仿写）

[改进建议]
（如果你能判断出仿写，针对仿写文本最突出的2-3个破绽，给出具体的风格指令修改方向）
"""

_DEFAULT_PROMPTS["style_calibration_revise_prompt"] = """\
你是一位文风指令工程师。根据鉴定专家的反馈，修订风格指令使其更精准地还原目标作者的写作风格。

===== 当前风格指令 =====
{current_instruction}

===== 鉴定反馈 =====
{discrimination_feedback}

===== 修订要求 =====

1. 仔细阅读鉴定反馈中的分析依据和改进建议
2. 针对每个破绽，在风格指令中增加或修改对应的约束
3. 保留原指令中被鉴定为准确的部分，只调整有偏差的维度
4. 修订后的指令应更加具体、可执行，避免笼统描述
5. **硬性字数限制：修订后的指令总长度不得超过1200字。如有需要，精简合并已有条目，而非追加新条目。**

===== 输出格式 =====

[修订后风格指令]
（直接输出修订后的风格指令文本，不要加任何解释）
"""

# =============== 15. 叙事DNA章节指令迭代校准 ===================

_DEFAULT_PROMPTS["narrative_calibration_generate_prompt"] = """\
你是一位技艺精湛的小说作家。请严格按照以下章节指令（以及风格指令，如有）创作一段1200-1800字的小说片段。

===== 章节指令（叙事DNA）=====
{narrative_instruction}

===== 风格指令 =====
{style_instruction}

===== 创作要求 =====
1. 场景：{scenario}
2. 必须包含：场景环境描写、人物心理活动、至少两段对话、动作描写、至少一次视角或时间线切换。
3. 严格遵循上述章节指令中的所有叙事要求（推进节奏、场景结构、对话风格、角色互动模式、视角与感官偏好等）。
4. 如有风格指令，同时遵循其用词偏好和句式特征。
5. 不要解释你的创作思路，直接输出小说正文。

===== 输出 =====
直接输出小说片段正文，不要加任何标题或说明。
"""

_DEFAULT_PROMPTS["narrative_calibration_discriminate_prompt"] = """\
你是一位资深叙事学盲测鉴定专家。现在进行一场图灵测试：你将看到三段文本，需要判断哪一段是AI仿写。

===== 参考文本 A（已确认为真实作品）=====
{reference_sample}

===== 文本一 =====
{text_one}

===== 文本二 =====
{text_two}

===== 鉴定任务 =====

文本一和文本二中，有一段是与参考文本A同一作者的真实作品，另一段是AI根据叙事指令仿写的。
请从以下叙事维度综合判断哪段是仿写：
1. 推进节奏：叙事加速与减速的节奏、场景停留时长、快慢交替的模式
2. 场景结构：场景切换方式（硬切/过渡/闪回）、场景内部的段落组织、场景粒度
3. 对话风格：对话密度、对话与叙述的穿插方式、对话标签使用习惯
4. 角色互动模式：角色之间的张力构建方式、冲突推进手法、情感交流节奏
5. 视角与感官偏好：叙事视角、感官描写侧重、内心独白的使用频率

===== 输出格式（严格遵守）=====

[判断结果]
A：文本一是仿写
B：文本二是仿写
C：无法判断

请输出 A 或 B 或 C 中的一个字母。

[分析依据]
（从上述5个叙事维度逐一说明你的判断理由，具体指出哪些叙事特征让你认为某段是仿写）

[改进建议]
（如果你能判断出仿写，针对仿写文本最突出的2-3个叙事破绽，给出具体的章节指令修改方向）
"""

_DEFAULT_PROMPTS["narrative_calibration_revise_prompt"] = """\
你是一位叙事指令工程师。根据鉴定专家的反馈，修订章节指令使其更精准地还原目标作者的叙事模式。

===== 当前章节指令 =====
{current_narrative_instruction}

===== 鉴定反馈 =====
{discrimination_feedback}

===== 修订要求 =====

1. 仔细阅读鉴定反馈中的分析依据和改进建议
2. 针对每个破绽，在章节指令中增加或修改对应的叙事约束
3. 保留原指令中被鉴定为准确的部分，只调整有偏差的维度
4. 修订后的指令应更加具体、可执行，聚焦于叙事层面（推进节奏、场景结构、对话风格、角色互动、视角偏好）
5. **硬性字数限制：修订后的指令总长度不得超过1200字。如有需要，精简合并已有条目，而非追加新条目。**

===== 输出格式 =====

[修订后章节指令]
（直接输出修订后的章节指令文本，不要加任何解释）
"""

# ============================================================
# 运行时活跃提示词（唯一数据源）
# ============================================================
_active_prompts = dict(_DEFAULT_PROMPTS)

# 当前激活的预设名称
_active_preset_name = "网络小说"

# ============================================================
# 模块级变量（兼容原有 import 方式的初始值）
# ============================================================
core_seed_prompt = _active_prompts["core_seed_prompt"]
character_dynamics_prompt = _active_prompts["character_dynamics_prompt"]
world_building_prompt = _active_prompts["world_building_prompt"]
plot_architecture_prompt = _active_prompts["plot_architecture_prompt"]
create_character_state_prompt = _active_prompts["create_character_state_prompt"]
chapter_blueprint_prompt = _active_prompts["chapter_blueprint_prompt"]
chunked_chapter_blueprint_prompt = _active_prompts["chunked_chapter_blueprint_prompt"]
first_chapter_draft_prompt = _active_prompts["first_chapter_draft_prompt"]
next_chapter_draft_prompt = _active_prompts["next_chapter_draft_prompt"]
summarize_recent_chapters_prompt = _active_prompts["summarize_recent_chapters_prompt"]
knowledge_search_prompt = _active_prompts["knowledge_search_prompt"]
knowledge_filter_prompt = _active_prompts["knowledge_filter_prompt"]
summary_prompt = _active_prompts["summary_prompt"]
update_character_state_prompt = _active_prompts["update_character_state_prompt"]
Character_Import_Prompt = _active_prompts["Character_Import_Prompt"]
continuation_architecture_prompt = _active_prompts["continuation_architecture_prompt"]
continuation_characters_prompt = _active_prompts["continuation_characters_prompt"]
continuation_arcs_prompt = _active_prompts["continuation_arcs_prompt"]
continuation_char_state_prompt = _active_prompts["continuation_char_state_prompt"]
continuation_seed_prompt = _active_prompts["continuation_seed_prompt"]
continuation_world_prompt = _active_prompts["continuation_world_prompt"]
compress_summary_prompt = _active_prompts["compress_summary_prompt"]
compress_character_state_prompt = _active_prompts["compress_character_state_prompt"]
compress_world_building_prompt = _active_prompts["compress_world_building_prompt"]
style_analysis_prompt = _active_prompts["style_analysis_prompt"]
style_merge_prompt = _active_prompts["style_merge_prompt"]
scene_expansion_prompt = _active_prompts["scene_expansion_prompt"]
narrative_dna_analysis_prompt = _active_prompts["narrative_dna_analysis_prompt"]
style_calibration_generate_prompt = _active_prompts["style_calibration_generate_prompt"]
style_calibration_discriminate_prompt = _active_prompts["style_calibration_discriminate_prompt"]
style_calibration_revise_prompt = _active_prompts["style_calibration_revise_prompt"]
narrative_calibration_generate_prompt = _active_prompts["narrative_calibration_generate_prompt"]
narrative_calibration_discriminate_prompt = _active_prompts["narrative_calibration_discriminate_prompt"]
narrative_calibration_revise_prompt = _active_prompts["narrative_calibration_revise_prompt"]


# ============================================================
# 预设目录
# ============================================================
PRESETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")


def _sync_module_vars():
    """将 _active_prompts 同步到模块级变量，使 prompt_definitions.X 访问到最新值"""
    module = sys.modules[__name__]
    for key in PROMPT_KEYS:
        if key in _active_prompts:
            setattr(module, key, _active_prompts[key])


def ensure_default_preset():
    """确保默认预设文件存在，首次运行时自动创建"""
    os.makedirs(PRESETS_DIR, exist_ok=True)
    default_file = os.path.join(PRESETS_DIR, "网络小说.json")
    if not os.path.exists(default_file):
        save_preset("网络小说", "适用于起点、番茄等网络连载小说的默认提示词方案", dict(_DEFAULT_PROMPTS))
        logging.info("Default preset '网络小说.json' created.")


def list_presets():
    """列出 prompts/ 目录下所有预设名（不含 .json 后缀）"""
    os.makedirs(PRESETS_DIR, exist_ok=True)
    presets = []
    for f in os.listdir(PRESETS_DIR):
        if f.endswith(".json"):
            presets.append(f[:-5])
    return sorted(presets)


def get_preset_info(name):
    """获取预设的元数据（名称和描述）"""
    filepath = os.path.join(PRESETS_DIR, f"{name}.json")
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "preset_name": data.get("preset_name", name),
            "description": data.get("description", ""),
        }
    except Exception as e:
        logging.error(f"Failed to read preset info '{name}': {e}")
        return None


def load_preset(name):
    """从 JSON 文件加载并激活预设，返回 (success, message)"""
    global _active_prompts, _active_preset_name
    filepath = os.path.join(PRESETS_DIR, f"{name}.json")
    if not os.path.exists(filepath):
        return False, f"预设文件不存在: {name}.json"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        prompts = data.get("prompts", {})
        # 以默认值为底，覆盖预设中存在的 key
        _active_prompts = dict(_DEFAULT_PROMPTS)
        for key in PROMPT_KEYS:
            if key in prompts:
                _active_prompts[key] = prompts[key]
        _active_preset_name = name
        _sync_module_vars()
        logging.info(f"Preset '{name}' loaded and activated.")
        return True, f"预设 '{name}' 已激活"
    except Exception as e:
        logging.error(f"Failed to load preset '{name}': {e}")
        return False, f"加载预设失败: {str(e)}"


def save_preset(name, description, prompts_dict):
    """保存预设到 JSON 文件，返回 (success, message)"""
    os.makedirs(PRESETS_DIR, exist_ok=True)
    filepath = os.path.join(PRESETS_DIR, f"{name}.json")
    try:
        data = {
            "preset_name": name,
            "description": description,
            "prompts": {}
        }
        for key in PROMPT_KEYS:
            if key in prompts_dict:
                data["prompts"][key] = prompts_dict[key]
        atomic_write_json(data, filepath, indent=2)
        logging.info(f"Preset '{name}' saved.")
        return True, f"预设 '{name}' 已保存"
    except Exception as e:
        logging.error(f"Failed to save preset '{name}': {e}")
        return False, f"保存预设失败: {str(e)}"


def delete_preset(name):
    """删除预设文件，返回 (success, message)"""
    filepath = os.path.join(PRESETS_DIR, f"{name}.json")
    if not os.path.exists(filepath):
        return False, f"预设文件不存在: {name}.json"
    try:
        os.remove(filepath)
        logging.info(f"Preset '{name}' deleted.")
        return True, f"预设 '{name}' 已删除"
    except Exception as e:
        logging.error(f"Failed to delete preset '{name}': {e}")
        return False, f"删除预设失败: {str(e)}"


def get_all_prompts():
    """返回当前活跃提示词字典的副本"""
    return dict(_active_prompts)


def get_active_preset_name():
    """返回当前激活的预设名称"""
    return _active_preset_name


def update_active_prompt(key, value):
    """更新单个活跃提示词（不保存到文件）"""
    global _active_prompts
    if key in PROMPT_KEYS:
        _active_prompts[key] = value
        _sync_module_vars()


def reset_to_default():
    """恢复为内置默认提示词"""
    global _active_prompts, _active_preset_name
    _active_prompts = dict(_DEFAULT_PROMPTS)
    _active_preset_name = "网络小说"
    _sync_module_vars()
    logging.info("Prompts reset to built-in defaults.")
    return True, "已恢复为内置默认提示词"
