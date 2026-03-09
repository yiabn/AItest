# app/crawlers/m99_crawler.py
import re
from typing import Dict, Any, Optional,List
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from loguru import logger

from .base import BaseCrawler  # 假设存在 BaseCrawler，如果不存在可自行实现基类


class M99Crawler(BaseCrawler):
    """
    魔域官网 (my.99.com) 专用爬虫
    支持页面类型：幻兽、装备、技能、副本、地图、新闻/攻略等
    """

    # 页面类型判断规则（URL 模式）
    PAGE_PATTERNS = {
        "pet": [r"/data/pet/", r"/chongwu/", r"/huanShou/", r"幻兽", r"宠物"],
        "equipment": [r"/data/equip/", r"/zhuangbei/", r"装备", r"武器", r"防具"],
        "skill": [r"/data/skill/", r"/jineng/", r"技能"],
        "dungeon": [r"/data/fuben/", r"/dungeon/", r"副本"],
        "map": [r"/data/map/", r"/ditu/", r"地图"],
        "quest": [r"/task/", r"/quest/", r"任务"],
        "news": [r"/content/", r"/news/", r"/article/"],  # 新闻/攻略页
    }

    def __init__(self, delay: float = 1.5):
        """
        初始化爬虫
        :param delay: 请求间隔（秒），避免被反爬
        """
        super().__init__(delay=delay)  # 调用基类构造函数，基类需实现 fetch 等方法

    def analyze_page(self, url: str) -> Dict[str, Any]:
        """
        分析页面主入口
        :param url: 页面 URL
        :return: 包含页面信息的字典，至少包含：
                 - url: 原始 URL
                 - title: 页面标题
                 - type: 检测到的页面类型
                 - data: 根据类型提取的结构化数据
                 - text: 纯文本内容
                 - html: 原始 HTML（可能较大，用于保存快照）
        """
        logger.info(f"开始分析页面: {url}")
        html = self.fetch(url)  # 假设基类有 fetch 方法
        if not html:
            return {"error": "抓取失败", "url": url}

        soup = BeautifulSoup(html, 'html.parser')

        # 检测页面类型
        page_type = self._detect_page_type(url, soup)

        # 提取标题
        title = self._extract_title(soup)

        # 根据类型提取结构化数据
        if page_type == "pet":
            data = self._extract_pet_info(soup)
        elif page_type == "equipment":
            data = self._extract_equipment_info(soup)
        elif page_type == "skill":
            data = self._extract_skill_info(soup)
        elif page_type == "dungeon":
            data = self._extract_dungeon_info(soup)
        elif page_type == "quest":
            data = self._extract_quest_info(soup)
        elif page_type == "news":
            data = self._extract_news_info(soup)
        else:
            data = self._extract_general_info(soup)

        # 提取纯文本（用于实体提取）
        text = self._extract_clean_text(soup)

        logger.success(f"页面分析完成: 类型={page_type}, 标题={title}")
        return {
            "url": url,
            "title": title,
            "type": page_type,
            "data": data,
            "text": text,
            "html": html,
        }

    # ========== 页面类型检测 ==========
    def _detect_page_type(self, url: str, soup: BeautifulSoup) -> str:
        url_lower = url.lower()
        title = soup.title.string if soup.title else ""
        # 取前1000字符用于内容检测，提高准确率
        text = soup.get_text()[:1000]

        # 定义标题/内容关键词映射（可独立于 URL 模式）
        type_keywords = {
            "pet": ["幻兽", "宠物", "年兽", "灵兽"],
            "skill": ["技能", "天赋", "战技"],
            "equipment": ["装备", "武器", "防具"],
            "dungeon": ["副本"],
            "quest": ["任务"],
        }

        # 1. 从标题匹配
        for ptype, keywords in type_keywords.items():
            for kw in keywords:
                if kw in title:
                    logger.debug(f"从标题匹配到类型: {ptype}")
                    return ptype

        # 2. 从内容前500字符匹配（已经截取前1000，这里再检查一次即可）
        for ptype, keywords in type_keywords.items():
            for kw in keywords:
                if kw in text:
                    logger.debug(f"从内容匹配到类型: {ptype}")
                    return ptype

        # 3. 按非新闻的 URL 模式匹配（避免 news 优先）
        for ptype, patterns in self.PAGE_PATTERNS.items():
            if ptype == "news":
                continue
            for pattern in patterns:
                if re.search(pattern, url_lower, re.I):
                    logger.debug(f"从 URL 匹配到类型: {ptype}")
                    return ptype

        # 4. 最后检查是否为新闻（包含 /content/ 等）
        for pattern in self.PAGE_PATTERNS.get("news", []):
            if re.search(pattern, url_lower, re.I):
                logger.debug(f"从 URL 匹配到类型: news")
                return "news"

        return "general"
    # ========== 标题提取 ==========
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取页面标题，多种备选方案"""
        # 尝试常见的标题选择器
        selectors = [
            "h1",
            ".title",
            ".page-title",
            ".article-title",
            ".detail-title",
            ".main-title",
            ".content-title",
        ]
        for sel in selectors:
            elem = soup.select_one(sel)
            if elem:
                title = elem.get_text().strip()
                if title:
                    return title
        # 最后使用 HTML title 标签
        if soup.title:
            title = soup.title.string
            # 去除网站名称等后缀
            title = re.sub(r'[-_|].*?$', '', title).strip()
            return title
        return "未知标题"

    # ========== 幻兽页面解析 ==========
    def _extract_pet_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取幻兽页面信息"""
        info = {
            "name": None,
            "level": None,
            "type": None,
            "element": None,
            "stats": {},       # 属性键值对
            "skills": [],      # 技能列表
            "description": None,
            "acquisition": None,  # 获取方式
        }
        # 提取名称（多种可能）
        name_elem = soup.select_one('h1, .pet-name, .name, .detail-title')
        if name_elem:
            info["name"] = name_elem.get_text().strip()

        # 提取属性表格
        table = soup.find('table', class_=re.compile(r'attr|stat|property'))
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    info["stats"][key] = value

        # 提取技能列表（通常在技能区域）
        skill_section = soup.find(['div', 'section'], class_=re.compile(r'skill|ability'))
        if skill_section:
            skills = skill_section.find_all(['li', 'tr', '.skill-item'])
            for skill in skills:
                name = skill.get_text().strip()
                if name and len(name) < 50:
                    info["skills"].append(name)

        # 提取描述
        desc_elem = soup.select_one('.description, .desc, .intro, .brief')
        if desc_elem:
            info["description"] = desc_elem.get_text().strip()

        # 提取获取方式（关键词附近段落）
        text = soup.get_text()
        for keyword in ["获得", "获取", "掉落", "兑换"]:
            if keyword in text:
                # 简单获取关键词所在段落
                for p in soup.find_all('p'):
                    if keyword in p.get_text():
                        info["acquisition"] = p.get_text().strip()
                        break
                if info["acquisition"]:
                    break

        return info

    # ========== 装备页面解析 ==========
    def _extract_equipment_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取装备页面信息"""
        info = {
            "name": None,
            "level": None,
            "quality": None,
            "type": None,
            "stats": {},
            "required_level": None,
            "required_class": None,
            "description": None,
            "acquisition": None,
        }
        name_elem = soup.select_one('h1, .equip-name, .name')
        if name_elem:
            info["name"] = name_elem.get_text().strip()

        # 提取品质（颜色词）
        quality_elem = soup.select_one('.quality, .rarity')
        if quality_elem:
            info["quality"] = quality_elem.get_text().strip()

        # 提取属性列表（常见于表格或列表）
        attr_elems = soup.select('.attr, .stat, .property, li')
        for elem in attr_elems:
            text = elem.get_text().strip()
            if ':' in text:
                k, v = text.split(':', 1)
                info["stats"][k.strip()] = v.strip()
            elif '：' in text:
                k, v = text.split('：', 1)
                info["stats"][k.strip()] = v.strip()

        return info

    # ========== 技能页面解析 ==========
    def _extract_skill_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        增强版技能页面解析器
        返回结构：
        {
            "skills": [  # 每个技能一个实体
                {
                    "name": "技能名称",
                    "type": "主动/被动/连携/神启战技/特殊",  # 根据表格判断
                    "belongs_to": "归属幻兽",  # 所属幻兽
                    "source": "技能来源",
                    "description": "技能描述",
                    "levels": [  # 如果有等级
                        {
                            "level": "Ⅰ/Ⅱ/Ⅲ 或数字",
                            "damage_percent": 数值,
                            "fixed_damage_cap": 数值,
                            "effects": [...],
                            ...
                        }
                    ],
                    "set_bonuses": [  # 套装加成
                        {
                            "score": 500,
                            "description": "效果描述",
                            "value": 数值
                        }
                    ],
                    "requirements": {  # 解锁要求
                        "score": 1200,
                        "stars": 30,
                        ...
                    },
                    "cooldown": 数值,
                    "cost": 数值,
                    "effect_details": [...]  # 效果细节，如击飞、沉默、治疗等
                }
            ]
        }
        """
        result = {
            "skills": [],
            "damage_levels": [],   # 保持兼容性
            "set_bonuses": [],
            "effects": []
        }

        # 查找所有表格
        tables = soup.find_all('table')
        for table in tables:
            # 尝试获取表头
            header_row = table.find('tr')
            if not header_row:
                continue
            headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]

            # 根据表头判断表格类型
            header_str = ' '.join(headers)

            if '归属幻兽' in header_str and '技能名称' in header_str and '技能效果' in header_str:
                # 被动-神骏特性 或 其他基础技能表格
                rows = table.find_all('tr')[1:]  # 跳过表头
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 3:
                        continue
                    # 提取单元格文本
                    belong = cells[0].get_text().strip()
                    skill_name = cells[1].get_text().strip()
                    skill_source = cells[2].get_text().strip() if len(cells) > 2 else ''
                    skill_effect = cells[3].get_text().strip() if len(cells) > 3 else ''
                    # 这里还可以提取非怀旧服和怀旧服说明，但先简化
                    # 创建技能对象
                    skill = {
                        "name": skill_name,
                        "type": "被动",  # 根据上下文判断，可能需要更精确
                        "belongs_to": belong,
                        "source": skill_source,
                        "description": skill_effect,
                        "levels": [],
                        "set_bonuses": [],
                        "requirements": {},
                        "effect_details": self._parse_effect(skill_effect)
                    }
                    result["skills"].append(skill)

            elif '多段范围伤害' in header_str or '技能效果' in header_str and '技能说明' in header_str:
                # 主动-多段范围伤害表格
                rows = table.find_all('tr')[1:]
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 3:
                        continue
                    belong = cells[0].get_text().strip()
                    skill_name = cells[1].get_text().strip()
                    skill_desc = cells[2].get_text().strip()  # 技能效果列
                    # 解析伤害等级
                    levels = self._parse_damage_levels(skill_desc)
                    skill = {
                        "name": skill_name,
                        "type": "主动",
                        "belongs_to": belong,
                        "description": skill_desc,
                        "levels": levels,
                        "set_bonuses": [],
                        "requirements": {}
                    }
                    result["skills"].append(skill)

            elif '连携技能' in header_str or '墨魂忠骨' in header_str:
                # 连携技能表格
                rows = table.find_all('tr')[1:]
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 3:
                        continue
                    skill_name = cells[0].get_text().strip()
                    skill_source = cells[1].get_text().strip()
                    skill_desc = cells[2].get_text().strip()
                    skill = {
                        "name": skill_name,
                        "type": "连携",
                        "source": skill_source,
                        "description": skill_desc,
                        "levels": [],
                        "set_bonuses": [],
                        "requirements": {}
                    }
                    result["skills"].append(skill)

            elif '神启战技' in header_str:
                # 被动-神启战技表格（比较复杂，有星级、等级、说明、神启强化）
                rows = table.find_all('tr')[1:]
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 5:
                        continue
                    belong = cells[0].get_text().strip()
                    skill_name = cells[2].get_text().strip()  # 第三列一般是技能名称
                    star_req = cells[3].get_text().strip()  # 要求星级
                    level = cells[4].get_text().strip()  # 技能等级
                    desc = cells[5].get_text().strip()  # 技能说明
                    enhance = cells[6].get_text().strip() if len(cells) > 6 else ''  # 神启强化
                    skill = {
                        "name": skill_name,
                        "type": "神启战技",
                        "belongs_to": belong,
                        "star_requirement": star_req,
                        "level": level,
                        "description": desc,
                        "enhance": enhance,
                        "levels": []
                    }
                    result["skills"].append(skill)

            # 可以继续添加其他表格类型判断...

        # 为了兼容原有的测试点生成器，我们也将数据填充到原有的字段中
        for skill in result["skills"]:
            if skill.get("levels"):
                result["damage_levels"].extend(skill["levels"])
            # 如果有套装加成，也加入
            # 简单起见，将效果描述收集起来
            result["effects"].append({"name": skill["name"], "description": skill.get("description", "")})

        return result

    def _parse_damage_levels(self, text: str) -> List[Dict]:
        """从文本中解析等级伤害，例如：
        Ⅰ级：对范围内敌人造成多段共计20000%伤害。技能结束后，对敌人额外造成一段至多为117000亿的固定伤害。
        """
        levels = []
        # 匹配等级标记（Ⅰ、Ⅱ、Ⅲ、Ⅳ、Ⅴ）
        # 先按等级分割
        level_pattern = r'([ⅠⅡⅢⅣⅤ]+)级[：:]\s*([^。]*(?:[0-9,]+%?[^。]*)?)'
        matches = re.findall(level_pattern, text)
        level_map = {"Ⅰ":1, "Ⅱ":2, "Ⅲ":3, "Ⅳ":4, "Ⅴ":5}
        for match in matches:
            level_str = match[0]
            level_num = level_map.get(level_str[0], 0)
            content = match[1]
            # 提取伤害百分比
            damage_match = re.search(r'(\d+)%', content)
            damage = int(damage_match.group(1)) if damage_match else None
            # 提取固定伤害封顶
            fixed_match = re.search(r'至多为(\d+)(?:[亿万]?)', content)
            fixed = int(fixed_match.group(1)) if fixed_match else None
            levels.append({
                "level": level_num,
                "damage": damage,
                "fixed_damage_cap": fixed
            })
        return levels

    def _parse_effect(self, text: str) -> List[Dict]:
        """解析效果描述，提取出效果类型和数值"""
        effects = []
        # 常见效果：击飞、沉默、眩晕、减伤、治疗等
        if '击飞' in text:
            effects.append({"type": "击飞"})
        if '沉默' in text:
            duration_match = re.search(r'沉默(\d+)秒', text)
            duration = int(duration_match.group(1)) if duration_match else None
            effects.append({"type": "沉默", "duration": duration})
        if '眩晕' in text:
            duration_match = re.search(r'眩晕(\d+)秒', text)
            duration = int(duration_match.group(1)) if duration_match else None
            effects.append({"type": "眩晕", "duration": duration})
        if '减伤' in text:
            value_match = re.search(r'(\d+)%减伤', text)
            value = int(value_match.group(1)) if value_match else None
            duration_match = re.search(r'持续(\d+)秒', text)
            duration = int(duration_match.group(1)) if duration_match else None
            effects.append({"type": "减伤", "value": value, "duration": duration})
        if '治疗' in text or '回复' in text:
            percent_match = re.search(r'回复(\d+)%', text)
            value = int(percent_match.group(1)) if percent_match else None
            effects.append({"type": "治疗", "value": value})
        return effects
    
    # ========== 副本页面解析 ==========
    def _extract_dungeon_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取副本页面信息"""
        info = {
            "name": None,
            "level_required": None,
            "location": None,
            "bosses": [],
            "rewards": [],
            "description": None,
        }
        name_elem = soup.select_one('h1, .dungeon-name, .name')
        if name_elem:
            info["name"] = name_elem.get_text().strip()

        # 可进一步解析
        return info

    # ========== 任务页面解析 ==========
    def _extract_quest_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取任务页面信息"""
        info = {
            "name": None,
            "type": None,
            "level_required": None,
            "start_npc": None,
            "objectives": [],
            "rewards": [],
            "description": None,
        }
        name_elem = soup.select_one('h1, .quest-name, .name')
        if name_elem:
            info["name"] = name_elem.get_text().strip()
        return info

    # ========== 新闻/攻略页面解析 ==========
    def _extract_news_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取新闻/攻略页面信息"""
        info = {
            "title": None,
            "publish_time": None,
            "content": None,
            "related_links": [],
        }
        # 标题已由 _extract_title 处理
        # 提取发布时间
        time_elem = soup.select_one('.time, .publish-time, .date')
        if time_elem:
            info["publish_time"] = time_elem.get_text().strip()

        # 提取正文内容（通常位于文章容器内）
        content_elem = soup.select_one('.content, .article-content, .main-content')
        if content_elem:
            info["content"] = content_elem.get_text().strip()[:2000]  # 限制长度
        return info

    # ========== 通用页面解析 ==========
    def _extract_general_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """通用页面提取：标题、段落、列表等"""
        info = {
            "headings": [],
            "paragraphs": [],
            "lists": [],
        }
        for h in soup.find_all(['h1', 'h2', 'h3']):
            text = h.get_text().strip()
            if text and len(text) < 100:
                info["headings"].append(text)
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 10:
                info["paragraphs"].append(text[:200])
        return info

    # ========== 提取干净的文本 ==========
    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """移除脚本、样式，提取纯文本"""
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        text = soup.get_text()
        # 清理多余空白
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text[:10000]  # 限制长度