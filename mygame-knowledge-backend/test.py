# test_knowledge_api.py
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/knowledge"

async def test_knowledge_api():
    """测试知识库接口"""
    
    async with httpx.AsyncClient() as client:
        
        # 1. 获取统计信息
        print("\n1. 获取知识库统计:")
        response = await client.get(f"{BASE_URL}/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   总实体数: {stats['total_entities']}")
            print(f"   类型分布: {stats['type_distribution']}")
        else:
            print(f"   失败: {response.status_code}")
        
        # 2. 获取实体列表
        print("\n2. 获取实体列表:")
        response = await client.get(f"{BASE_URL}/entities?limit=5")
        if response.status_code == 200:
            entities = response.json()
            print(f"   获取到 {len(entities)} 个实体")
            for e in entities:
                print(f"   - {e['name']} ({e['type']})")
        else:
            print(f"   失败: {response.status_code}")
        
        # 3. 获取类型统计
        print("\n3. 获取类型统计:")
        response = await client.get(f"{BASE_URL}/types")
        if response.status_code == 200:
            types = response.json()
            for t in types:
                print(f"   - {t['type']}: {t['count']}个")
        else:
            print(f"   失败: {response.status_code}")
        
        # 4. 搜索测试
        print("\n4. 搜索 '龙':")
        response = await client.get(f"{BASE_URL}/search?keyword=龙")
        if response.status_code == 200:
            search_result = response.json()
            print(f"   找到 {search_result['total']} 个结果")
            for r in search_result['results'][:3]:
                print(f"   - {r['name']} ({r['type']})")
        else:
            print(f"   失败: {response.status_code}")
        
        # 5. 获取最近实体
        print("\n5. 最近添加的实体:")
        response = await client.get(f"{BASE_URL}/recent?limit=5")
        if response.status_code == 200:
            recent = response.json()
            for r in recent:
                print(f"   - {r['name']} ({r['created_at']})")
        else:
            print(f"   失败: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_knowledge_api())