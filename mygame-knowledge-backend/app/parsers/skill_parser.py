# app/parsers/skill_parser.py
from typing import Dict, Any, List
import re
from bs4 import BeautifulSoup

class SkillSpecializationParser:
    """专精技能页面解析器"""
    
    def __init__(self):
        self.skill_categories = {
            'passive': ['被动', '印记', '专精被动'],
            'active': ['主动', '天坠', '核心技能'],
            'talent': ['神性天赋', '觉醒'],
            'attribute': ['超凡属性']
        }
    
    def parse(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """解析专精技能页面"""
        result = {
            'title': self._extract_title(soup),
            'intro': self._extract_intro(soup),
            'core_skills': self._extract_core_skills(soup),
            'talents': self._extract_talents(soup),
            'attributes': self._extract_attributes(soup),
            'test_points': self._generate_test_points(soup)  # 直接生成测试点
        }
        return result
    
    def _extract_core_skills(self, soup: BeautifulSoup) -> List[Dict]:
        """提取核心技能"""
        skills = []
        
        # 查找技能表格
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue
            
            # 尝试解析表头
            headers = [th.get_text().strip() for th in rows[0].find_all(['th', 'td'])]
            
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    skill = self._parse_skill_row(cells, headers)
                    if skill:
                        skills.append(skill)
        
        return skills
    
    def _parse_skill_row(self, cells: List, headers: List) -> Dict:
        """解析单行技能数据"""
        skill = {
            'name': '',
            'type': '',
            'effect': '',
            'details': [],
            'test_cases': []
        }
        
        # 根据常见结构解析
        text_cells = [cell.get_text().strip() for cell in cells]
        
        if len(text_cells) >= 1:
            skill['name'] = text_cells[0]
        if len(text_cells) >= 2:
            skill['type'] = text_cells[1]
        if len(text_cells) >= 3:
            skill['effect'] = text_cells[2]
        
        # 从效果描述中提取数值和机制
        skill['details'] = self._extract_skill_details(skill['effect'])
        skill['test_cases'] = self._generate_skill_test_cases(skill)
        
        return skill
    
    def _extract_skill_details(self, effect_text: str) -> Dict:
        """从技能描述中提取详细数值"""
        details = {
            'damage': None,
            'duration': None,
            'cooldown': None,
            'conditions': [],
            'mechanics': []
        }
        
        # 提取伤害百分比
        damage_match = re.search(r'(\d+)%', effect_text)
        if damage_match:
            details['damage'] = int(damage_match.group(1))
        
        # 提取持续时间
        duration_match = re.search(r'(\d+)\s*秒', effect_text)
        if duration_match:
            details['duration'] = int(duration_match.group(1))
        
        # 提取机制关键词
        mechanics = ['眩晕', '减速', '霸体', '免疫', '追踪', '范围', '锁定']
        for mech in mechanics:
            if mech in effect_text:
                details['mechanics'].append(mech)
        
        return details
    
    def _generate_skill_test_cases(self, skill: Dict) -> List[str]:
        """为单个技能生成测试点"""
        test_cases = []
        name = skill['name']
        details = skill.get('details', {})
        
        if details.get('damage'):
            test_cases.append(f"验证 {name} 伤害系数是否为 {details['damage']}%")
        
        if details.get('duration'):
            test_cases.append(f"验证 {name} 持续时间是否为 {details['duration']}秒")
        
        for mech in details.get('mechanics', []):
            test_cases.append(f"验证 {name} 的 {mech} 效果是否生效")
        
        return test_cases
    
    def _generate_test_points(self, soup: BeautifulSoup) -> List[str]:
        """生成完整的测试点列表"""
        test_points = []
        
        # 1. 基础功能测试点
        test_points.append("【基础功能】验证专精解锁任务'专精·圣炎悲歌'是否正常")
        
        # 2. 技能数值测试点
        test_points.append("【数值验证】所有技能数值是否与官方文档一致")
        
        # 3. 核心机制测试点
        if '圣炎印记' in str(soup):
            test_points.append("【核心机制】验证耀日印记28秒生成周期")
            test_points.append("【核心机制】验证蚀日印记180秒生成周期")
            test_points.append("【核心机制】验证蚀日印记冷却缩减效果")
        
        # 4. 技能组合测试点
        test_points.append("【技能组合】验证阳炎天坠+印记增幅的组合效果")
        
        # 5. 天赋分支测试点
        talent_section = soup.find('h3', string=re.compile('神性天赋'))
        if talent_section:
            test_points.append("【天赋分支】验证所有神性天赋的觉醒条件")
            test_points.append("【天赋分支】验证天赋对基础技能的修改效果")
        
        return test_points