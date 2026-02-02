#!/usr/bin/env python3
"""
API测试脚本 (API Test Script)

测试所有API端点是否正常工作
Test if all API endpoints are working properly
"""
import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000/api"


def test_api():
    """测试API端点"""
    print("=" * 60)
    print("🧪 开始测试13F Tracker API")
    print("=" * 60)

    # 1. 测试Dashboard Summary
    print("\n1️⃣ 测试 Dashboard Summary...")
    try:
        response = requests.get(f"{BASE_URL}/dashboard/summary")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(
                f"   ✅ 成功! Top Picks Cards: {len(data.get('top_picks_cards', []))}"
            )
            print(f"   ✅ Recent Activity: {len(data.get('recent_activity', []))}")
        else:
            print(f"   ❌ 失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 2. 测试Institutions列表
    print("\n2️⃣ 测试 Institutions 列表...")
    try:
        response = requests.get(f"{BASE_URL}/institutions/")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功! 机构数量: {data.get('count', 0)}")
        else:
            print(f"   ❌ 失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 3. 测试Filings列表
    print("\n3️⃣ 测试 Filings 列表...")
    try:
        response = requests.get(f"{BASE_URL}/filings/")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功! 文件数量: {data.get('count', 0)}")
        else:
            print(f"   ❌ 失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 4. 测试Admin Companies
    print("\n4️⃣ 测试 Admin Companies...")
    try:
        response = requests.get(f"{BASE_URL}/admin/companies")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功! 监控公司数量: {len(data)}")
        else:
            print(f"   ❌ 失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 5. 测试System Status
    print("\n5️⃣ 测试 System Status...")
    try:
        response = requests.get(f"{BASE_URL}/admin/system-status")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功!")
            print(f"      - 成功次数: {data.get('success_count', 0)}")
            print(f"      - 错误次数: {data.get('error_count', 0)}")
            print(f"      - 总机构数: {data.get('total_institutions', 0)}")
            print(f"      - 总文件数: {data.get('total_filings', 0)}")
        else:
            print(f"   ❌ 失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")

    # 6. 测试添加机构
    print("\n6️⃣ 测试 添加机构 (Berkshire Hathaway)...")
    try:
        response = requests.post(
            f"{BASE_URL}/admin/companies/add",
            json={"cik": "0001067983"},
            headers={"Content-Type": "application/json"},
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"   ✅ 成功! 机构: {data.get('name', 'Unknown')}")
            print(f"      CIK: {data.get('cik', 'Unknown')}")
            return data.get("id")
        else:
            print(f"   ❌ 失败: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return None

    print("\n" + "=" * 60)
    print("✅ API测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    test_api()
