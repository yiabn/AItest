# app/crawlers/m99_crawler.py
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
import re
from bs4 import BeautifulSoup
from loguru import logger

from .base import BaseCrawler

class M99Crawler(BaseCrawler):
    """魔域99.com专用爬虫"""
    
    BASE_DOMAIN = "my.99.com"
    BASE_URL = "https://my.99.com"
    
    # 页面类型判断规则
    PAGE_PATTERNS = {
        "pet": [
            r"/data/pet/",
            r"/chongwu/",
            r"/huanShou/",
            r"幻兽",
            r"宠物"
        ],
        "equipment": [
            r"/data/equip/",
            r"/zhuangbei/",
            r"装备",
            r"武器",
            r"防具"
        ],
        "skill": [
            r"/data/skill/",
            r"/jineng/",
            r"技能"
        ],
        "dungeon": [
            r"/data/fuben/",
            r"/dungeon/",
            r"副本"
        ],
        "map": [
            r"/data/map/",
            r"/ditu/",
            r"地图"
        ]
    }
    
    def __init__(self):
        super().__init__(delay=1.5)  # 魔域官网适当延迟，避免被封
        
    def analyze_page(self, url: str) -> Dict[str, Any]:
        """分析页面内容"""
        html = self.fetch(url)
        if not html:
            return {"error": "抓取失败"}
        
        # 使用多种解析器
        soup = None
        for parser in ['html.parser', 'lxml', 'html5lib']:
            try:
                soup = BeautifulSoup(html, parser)
                break
            except:
                continue
        
        if not soup:
            return {"error": "无法解析HTML"}
        
        # 判断页面类型
        page_type = self._detect_page_type(url, soup)
        
        # 提取标题 - 多种策略
        title = self._extract_title_improved(soup)
        
        # 根据页面类型提取内容
        if page_type == "pet":
            data = self._extract_pet_info_improved(soup)
        elif page_type == "equipment":
            data = self._extract_equipment_info_improved(soup)
        elif page_type == "skill":
            data = self._extract_skill_info_improved(soup)
        else:
            data = self._extract_general_info_improved(soup)
        
        # 提取所有文本
        text = self._extract_clean_text(soup)
        
        # 提取实体
        entities = self._extract_entities_from_data(data, page_type)
        
        return {
            "url": url,
            "title": title,
            "type": page_type,
            "data": data,
            "entities": entities,
            "text": text[:5000],  # 限制长度
            "html": html[:50000] if len(html) > 50000 else html
        }
    

    def _detect_page_type(self, url: str, soup: BeautifulSoup) -> str:
        """检测页面类型 - 增强版"""
        url_lower = url.lower()
        title = soup.title.string if soup.title else ""
        text = soup.get_text()
        
        # 1. 先检查是否是新闻/攻略页面
        if '/content/' in url_lower:
            # 检查页面特征
            if '专精' in text and '技能' in text:
                return 'skill_specialization'  # 专精技能页
            elif '攻略' in title or '攻略' in text:
                return 'guide'  # 攻略页
            elif '更新' in title or '公告' in title:
                return 'update'  # 更新公告
            else:
                return 'article'  # 普通文章
        
        # 2. 资料库页面判断
        for page_type, patterns in self.PAGE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower, re.I):
                    return page_type
        
        # 3. 从页面结构判断
        if soup.find('table'):  # 有表格
            if '技能' in text and '效果' in text:
                return 'skill_table'
        
        return 'general'


    def _extract_title_improved(self, soup: BeautifulSoup) -> str:
        """改进的标题提取"""
        # 尝试多种选择器
        selectors = [
            'h1',
            '.title',
            '.page-title',
            '.article-title',
            '.detail-title',
            '.name',
            '.pet-name',
            '.equip-name',
            '.skill-name',
            '.main-title',
            '.content-title'
        ]
        
        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text().strip()
                if title and len(title) < 100:
                    return title
        
        # 使用网页标题
        if soup.title:
            title = soup.title.string
            # 清理标题
            title = re.sub(r'[-_|].*?$', '', title).strip()
            title = re.sub(r'魔域|官网|资料|攻略', '', title).strip()
            return title
        
        return "未知标题"
    
    def _extract_skill_info_improved(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """改进的技能信息提取，专精于复杂的技能页面"""
        skill_info = {
            "name": None,
            "type": None,
            "cooldown": None,
            "cost": None,
            "description": None,
            "effects": [],
            "details": []  # 用于存储表格等详细信息
        }
        
        # 1. 提取标题（通常是技能名称）
        title_elem = soup.find('h1') or soup.find('h2')
        if title_elem:
            skill_info["name"] = title_elem.get_text().strip()
        
        # 2. 查找所有表格，技能数据通常在表格中
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            table_data = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text().strip() for cell in cells]
                if row_data:
                    table_data.append(row_data)
            if table_data:
                skill_info["details"].append(table_data)
        
        # 3. 提取技能效果（通常以列表或段落形式存在）
        content_div = soup.find('div', class_='content') or soup.find('div', class_='article-content')
        if content_div:
            # 查找所有标题和描述
            for elem in content_div.find_all(['h3', 'h4', 'p', 'li']):
                text = elem.get_text().strip()
                if text and len(text) < 200:
                    skill_info["effects"].append(text)
        
        # 4. 提取具体描述（合并所有文本）
        all_text = soup.get_text()
        # 清理和截取描述
        lines = [line.strip() for line in all_text.splitlines() if line.strip()]
        skill_info["description"] = ' '.join(lines)[:500]
        
        return skill_info


    def _extract_pet_info_improved(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """改进的幻兽信息提取"""
        pet_info = {
            "name": None,
            "level": None,
            "type": None,
            "element": None,
            "stats": {},
            "skills": [],
            "description": None,
            "acquisition": None
        }
        
        # 提取所有文本
        text = soup.get_text()
        
        # 1. 提取名称
        name_selectors = ['h1', '.pet-name', '.name', '.detail-title']
        for selector in name_selectors:
            elem = soup.select_one(selector)
            if elem:
                pet_info["name"] = elem.get_text().strip()
                break
        
        # 2. 提取属性表格
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    
                    # 过滤掉太长的值
                    if len(key) < 20 and len(value) < 50:
                        pet_info["stats"][key] = value
        
        # 3. 提取技能 - 查找技能关键词
        skill_patterns = ['技能', '天赋', '觉醒', '伤害', '效果', '冷却']
        for pattern in skill_patterns:
            if pattern in text:
                # 查找技能列表
                skill_section = soup.find(['div', 'section'], class_=re.compile(r'skill|ability|技'))
                if skill_section:
                    skills = skill_section.find_all(['li', 'p', 'div'])
                    for skill in skills:
                        skill_text = skill.get_text().strip()
                        if skill_text and len(skill_text) < 50 and '技能' not in skill_text:
                            pet_info["skills"].append(skill_text)
        
        # 4. 提取元素属性
        elements = ['火', '水', '地', '风','']
        for elem in elements:
            if elem in text:
                pet_info["element"] = elem
                break
        
        # 5. 提取描述
        desc_selectors = ['.description', '.desc', '.intro', '.brief', '.summary']
        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem:
                pet_info["description"] = elem.get_text().strip()[:200]
                break
        
        # 6. 提取获取方式
        acquire_patterns = ['获得', '获取', '掉落', '兑换', '购买']
        for pattern in acquire_patterns:
            if pattern in text:
                # 查找包含获取方式的段落
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    p_text = p.get_text()
                    if pattern in p_text and len(p_text) < 200:
                        pet_info["acquisition"] = p_text.strip()
                        break
        
        return pet_info
    
    def _extract_entities_from_data(self, data: Dict, page_type: str) -> List[Dict]:
        """从提取的数据中构建实体列表"""
        entities = []
        
        if page_type == "pet" and data.get("name"):
            # 主实体 - 幻兽本身
            main_entity = {
                "name": data["name"],
                "type": "pet",
                "attributes": {
                    "元素": data.get("element", "未知"),
                    "等级": data.get("level", "未知"),
                    "描述": data.get("description", "")[:50] + "..." if data.get("description") else ""
                }
            }
            
            # 添加属性到 attributes
            for key, value in data.get("stats", {}).items():
                main_entity["attributes"][key] = value
            
            entities.append(main_entity)
            
            # 技能实体
            for skill in data.get("skills", []):
                entities.append({
                    "name": skill,
                    "type": "skill",
                    "attributes": {
                        "所属": data["name"]
                    }
                })
            
            # 获取方式实体
            if data.get("acquisition"):
                entities.append({
                    "name": f"{data['name']}获取方式",
                    "type": "info",
                    "attributes": {
                        "方式": data["acquisition"]
                    }
                })
        
        return entities
    
    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """提取干净的文本"""
        # 移除脚本和样式
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # 获取文本
        text = soup.get_text()
        
        # 清理空白
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line and len(line) > 1:  # 过滤掉单个字符
                lines.append(line)
        
        return '\n'.join(lines)
        
    def _detect_page_type(self, url: str, soup: BeautifulSoup) -> str:
        """检测页面类型"""
        url_lower = url.lower()
        
        # 从URL判断
        for page_type, patterns in self.PAGE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url_lower, re.I):
                    logger.info(f"从URL判断页面类型: {page_type}")
                    return page_type
                    
        # 从页面标题判断
        title = soup.title.string if soup.title else ""
        if title:
            for page_type, patterns in self.PAGE_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, title, re.I):
                        logger.info(f"从标题判断页面类型: {page_type}")
                        return page_type
                        
        # 从页面内容判断
        text = soup.get_text()
        if "幻兽" in text or "宠物" in text:
            return "pet"
        elif "装备" in text or "武器" in text:
            return "equipment"
        elif "技能" in text:
            return "skill"
            
        return "general"
        
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        # 尝试多种标题选择器
        title_selectors = [
            "h1",
            ".title",
            ".page-title",
            ".article-title",
            ".detail-title",
            ".name"
        ]
        
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text().strip()
                
        # 使用网页标题
        if soup.title:
            title = soup.title.string
            # 去除网站名称
            title = re.sub(r'[-_|].*?$', '', title).strip()
            return title
            
        return "未知标题"
        
    def _extract_pet_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取幻兽信息"""
        pet_info = {
            "name": None,
            "level": None,
            "type": None,
            "element": None,
            "stats": {},
            "skills": [],
            "description": None,
            "image": None
        }
        
        # 提取名称
        name_elem = soup.select_one('h1, .name, .pet-name, .detail-title')
        if name_elem:
            pet_info["name"] = name_elem.get_text().strip()
            
        # 提取属性表格
        table = soup.find('table', class_=re.compile(r'attr|stat|property'))
        if table:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    pet_info["stats"][key] = value
                    
        # 提取技能
        skill_section = soup.find(['div', 'section'], class_=re.compile(r'skill|ability'))
        if skill_section:
            skills = skill_section.find_all(['li', 'tr', '.skill-item'])
            for skill in skills:
                skill_name = skill.get_text().strip()
                if skill_name and len(skill_name) < 50:  # 过滤太长的文本
                    pet_info["skills"].append(skill_name)
                    
        # 提取描述
        desc_elem = soup.select_one('.description, .desc, .intro')
        if desc_elem:
            pet_info["description"] = desc_elem.get_text().strip()
            
        return pet_info
        
    def _extract_equipment_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取装备信息"""
        equip_info = {
            "name": None,
            "level": None,
            "quality": None,
            "type": None,
            "stats": {},
            "required_level": None,
            "required_class": None,
            "description": None
        }
        
        # 提取名称
        name_elem = soup.select_one('h1, .name, .equip-name')
        if name_elem:
            equip_info["name"] = name_elem.get_text().strip()
            
        # 提取品质
        quality_elem = soup.select_one('.quality, .rarity')
        if quality_elem:
            equip_info["quality"] = quality_elem.get_text().strip()
            
        # 提取属性
        attr_elem = soup.select('.attr, .stat, .property')
        for elem in attr_elem:
            text = elem.get_text().strip()
            if ':' in text:
                key, value = text.split(':', 1)
                equip_info["stats"][key.strip()] = value.strip()
                
        return equip_info
        
    def _extract_skill_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取技能信息"""
        skill_info = {
            "name": None,
            "type": None,
            "cooldown": None,
            "cost": None,
            "target": None,
            "description": None,
            "effects": []
        }
        
        # 提取名称
        name_elem = soup.select_one('h1, .name, .skill-name')
        if name_elem:
            skill_info["name"] = name_elem.get_text().strip()
            
        # 提取描述
        desc_elem = soup.select_one('.description, .desc, .effect')
        if desc_elem:
            skill_info["description"] = desc_elem.get_text().strip()
            
        # 提取冷却时间
        cd_text = re.search(r'冷却[时间]?[：:]?\s*(\d+\.?\d*)\s*秒', soup.get_text())
        if cd_text:
            skill_info["cooldown"] = cd_text.group(1)
            
        return skill_info
        
    def _extract_general_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取通用信息"""
        info = {
            "headings": [],
            "paragraphs": [],
            "lists": []
        }
        
        # 提取所有标题
        for h in soup.find_all(['h1', 'h2', 'h3']):
            text = h.get_text().strip()
            if text and len(text) < 100:
                info["headings"].append(text)
                
        # 提取段落
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 10:
                info["paragraphs"].append(text[:200])  # 只保留前200字符
                
        return info
        
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """提取纯文本内容"""
        # 移除脚本和样式
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text()
        # 清理空白字符
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text[:10000]  # 限制长度