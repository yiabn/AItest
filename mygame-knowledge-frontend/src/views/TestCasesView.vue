# app/parsers/structured_parser.py
import re
import json
from bs4 import BeautifulSoup
import pandas as pd

class StructuredDataParser:
    """结构化数据解析器（表格/列表/嵌套属性）"""
    
    def parse_table_data(self, html: str) -> list[dict]:
        """解析HTML表格为结构化数据"""
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        table_data = []
        
        for table in tables:
            # 提取表头
            headers = []
            header_rows = table.find_all('th')
            if header_rows:
                headers = [th.get_text(strip=True) for th in header_rows]
            else:
                # 无表头则取第一行作为表头
                first_row = table.find('tr')
                if first_row:
                    headers = [td.get_text(strip=True) for td in first_row.find_all('td')]
            
            # 提取行数据
            rows = table.find_all('tr')[1:] if header_rows else table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) != len(headers):
                    continue
                row_dict = {}
                for idx, cell in enumerate(cells):
                    row_dict[headers[idx]] = cell.get_text(strip=True)
                table_data.append(row_dict)
        
        return table_data

    def parse_skill_specialization(self, html: str) -> dict:
        """解析技能专精页面（嵌套属性）"""
        soup = BeautifulSoup(html, 'html.parser')
        specialization_data = {}
        
        # 提取专精等级和效果
        level_sections = soup.find_all('div', class_=re.compile(r'level-\d+'))
        for section in level_sections:
            level = section.find('span', class_='level').get_text(strip=True).replace('等级', '')
            effects = section.find_all('div', class_='effect')
            effect_list = [e.get_text(strip=True) for e in effects]
            specialization_data[f"level_{level}"] = effect_list
        
        # 提取冷却时间、消耗等关键数值
        cd_match = re.search(r'冷却时间[:：](\d+)秒', soup.get_text())
        cost_match = re.search(r'魔力消耗[:：](\d+)', soup.get_text())
        
        if cd_match:
            specialization_data['cd'] = int(cd_match.group(1))
        if cost_match:
            specialization_data['mana_cost'] = int(cost_match.group(1))
        
        return specialization_data