"""
测试SEC API连接
Test SEC API connection
"""

import requests


def test_sec_api():
    """测试不同的SEC API端点"""

    # Berkshire Hathaway的CIK
    cik = "1067983"

    print("测试SEC API连接...")
    print("=" * 60)

    # 测试1: Submissions API
    print("\n1. 测试Submissions API:")
    url1 = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
    print(f"   URL: {url1}")

    headers = {
        "User-Agent": "13F-Tracker test@example.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    }

    try:
        response = requests.get(url1, headers=headers, timeout=10)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 成功! 公司: {data.get('name', 'Unknown')}")
            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            print(f"   最近的表单类型: {forms[:5]}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")

    # 测试2: 使用EDGAR浏览器
    print("\n2. 测试EDGAR浏览器API:")
    url2 = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=13F-HR&dateb=&owner=exclude&count=10&output=atom"
    print(f"   URL: {url2}")

    headers2 = {
        "User-Agent": "13F-Tracker test@example.com",
    }

    try:
        response = requests.get(url2, headers=headers2, timeout=10)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ 成功! 响应长度: {len(response.text)} 字节")
            # 简单检查是否包含13F-HR
            if "13F-HR" in response.text:
                print("   ✅ 找到13F-HR文件")
    except Exception as e:
        print(f"   ❌ 失败: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_sec_api()
