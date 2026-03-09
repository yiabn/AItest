# app/services/ai_analyzer.py
import json
import os
import re
import requests
from typing import Dict, Any, Optional
from loguru import logger

class DoubaoAnalyzer:
    """使用火山引擎 ARK 服务分析页面内容，提取技能信息和测试点"""

    def __init__(self):
        # 从环境变量读取配置（请确保 .env 中已设置）
        self.api_key = os.getenv("ARK_API_KEY", "0affc7f2-1aa8-462b-9de8-ed9283945003")
        print(self.api_key)
        self.base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.model = os.getenv("ARK_MODEL_ID", "ep-20260310210158-dpghz")

        if not self.api_key or not self.model:
            logger.warning("ARK API key 或模型 ID 未配置，AI 分析功能将不可用")

    SYSTEM_PROMPT = """
你是一个专业的游戏测试专家，精通魔域等MMORPG游戏的技能机制。你的任务是从给定的游戏页面文本中，提取出所有相关的技能信息，并生成可执行的测试点。

**重要：你必须只输出一个 JSON 对象，不要包含任何解释、前言、后语或 markdown 代码块标记。输出的内容必须可以被 Python 的 json.loads() 直接解析。**

输出结构必须是一个 JSON 对象，包含两个字段：
- "skills": 技能信息列表
- "test_points": 测试点列表（每个测试点可关联到特定技能）

### 技能信息格式 (skills 数组中的每个元素)
{
  "name": "技能名称",
  "belongs_to": "归属幻兽（如果有）",
  "type": "技能类型（主动技能/被动技能/连携技能/特殊技能/传承技能）",
  "subtype": "更细的分类（如神骏特性、自身增益、全体增益、神启战技等）",
  "description": "完整技能描述",
  "level_data": [
    {
      "level": 1,
      "damage_percent": "20000%",
      "fixed_damage_cap": "117000亿",
      "other_effects": "其他效果"
    }
  ],
  "trigger_condition": "触发条件（如生命值低于80%、幻兽评分达1200等）",
  "cooldown": "冷却时间（秒）",
  "cost": "消耗（魔力/能量等）",
  "set_bonuses": [
    {
      "score": 500,
      "effect": "额外提升最终伤害18%"
    }
  ],
  "star_requirement": "星级要求（如30星）",
  "notes": "其他重要备注"
}

### 测试点格式 (test_points 数组中的每个元素)
{
  "skill_name": "关联的技能名称（可选）",
  "category": "测试类别（数值验证/机制验证/组合测试/边界测试）",
  "description": "测试点描述",
  "expected_result": "预期结果",
  "test_steps": "测试步骤（可选）",
  "priority": "优先级（high/medium/low）"
}

## 注意事项
- 如果某个信息在文本中不存在，可以省略对应字段。
- 仔细从文本中提取数值和条件，例如“Ⅰ级：造成20000%伤害”、“幻兽评分达1200分”等。
- 测试点要具体、可执行，基于技能描述中的数值和机制生成。
- **请只输出 JSON 对象，不要有任何额外文字。**
"""

    def analyze(self, text: str) -> Dict[str, Any]:
        """分析文本，返回包含 skills 和 test_points 的字典"""
        if not self.api_key or not self.model:
            logger.error("ARK 配置缺失，跳过 AI 分析")
            return {"skills": [], "test_points": []}

        # 控制输入长度
        text_text = """
    精灵游侠在目标位置布下两个箭阵并降下群星箭雨，箭雨将进行5次打击，分别造成695%、765%、834%、904%、973%的伤害。精灵游侠还将在箭阵周围召唤4个精灵之影，使用其它技能攻击箭阵内的目标时，所有精灵之影将同步射出灵箭，对攻击目标造成147%的物理伤害；若同时对多目标造成伤害，精灵之影则会随机选择一个受击目标进行同步攻击。
    """
        truncated_text = text_text[:12000]
        combined_text = f"{self.SYSTEM_PROMPT}\n\n以下是要分析的页面文本，请严格按照要求输出JSON，不要有任何解释或额外文字：\n{truncated_text}"

        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": combined_text
                        }
                    ]
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{self.base_url}/responses",
                json=payload,
                headers=headers,
                timeout=180
            )
            logger.debug(f"ARK 原始响应: {response.text}")
            response.raise_for_status()
            data = response.json()
            logger.debug(f"ARK 解析后数据: {data}")

            # ---------- 修正内容提取，适配火山引擎 ARK 格式 ----------
            content = None

            # 1. 处理火山引擎 ARK 格式（output 字段）
            if "output" in data and isinstance(data["output"], list):
                for item in data["output"]:
                    # 查找 type 为 message，role 为 assistant 的项
                    if item.get("type") == "message" and item.get("role") == "assistant":
                        content_list = item.get("content", [])
                        for sub_item in content_list:
                            if sub_item.get("type") == "output_text":
                                content = sub_item.get("text")
                                break
                        if content:
                            break

            # 2. 处理标准 OpenAI 兼容格式（choices 字段）
            elif "choices" in data and len(data["choices"]) > 0:
                msg = data["choices"][0].get("message", {})
                raw_content = msg.get("content")
                if isinstance(raw_content, str):
                    content = raw_content
                elif isinstance(raw_content, list):
                    # 如果 content 是列表（多模态），拼接文本片段
                    parts = []
                    for item in raw_content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            parts.append(item.get("text", ""))
                    content = "\n".join(parts)

            # 3. 处理直接返回 text 字段的简单接口
            elif "text" in data:
                content = data["text"]

            # 4. 如果 content 仍未找到，尝试取整个 data 的字符串表示（后备）
            if not content:
                logger.error("ARK 返回内容为空或格式无法识别")
                return {"skills": [], "test_points": []}

            # 确保 content 是字符串
            if not isinstance(content, str):
                content = str(content)

            # 提取 JSON
            result = self._extract_json(content)
            if result:
                logger.info(f"ARK 分析成功，提取到 {len(result.get('skills', []))} 个技能，{len(result.get('test_points', []))} 个测试点")
                return result
            else:
                logger.error("无法解析 ARK 返回的 JSON")
                return {"skills": [], "test_points": []}

        except requests.exceptions.RequestException as e:
            logger.error(f"ARK 请求异常: {e}")
            return {"skills": [], "test_points": []}
        except Exception as e:
            logger.error(f"ARK 分析异常: {e}")
            return {"skills": [], "test_points": []}

    def _extract_json(self, text: str) -> Optional[Dict]:
        """从文本中提取 JSON 对象（可能被 ```json 包裹）"""
        # 尝试匹配 ```json ... ```
        pattern = r'```json\s*([\s\S]*?)\s*```'
        match = re.search(pattern, text)
        if match:
            json_str = match.group(1)
        else:
            json_str = text
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # 如果失败，尝试查找最外层花括号
            try:
                start = text.index('{')
                end = text.rindex('}') + 1
                return json.loads(text[start:end])
            except:
                return None