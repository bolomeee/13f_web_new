"""
检查SEC 13F文件结构 - 使用Archives URL
Check SEC 13F filing structure - using Archives URL
"""

import requests
from bs4 import BeautifulSoup

# Berkshire Hathaway最新的13F文件
accession_number = "0001193125-25-282901"
accession_no_dash = accession_number.replace("-", "")
cik = "1067983"

# 构建Archives索引页面URL
index_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=13F-HR&dateb=&owner=exclude&count=10"

print(f"方法1: 获取13F列表\n{index_url}\n")

headers = {"User-Agent": "13F-Tracker test@example.com"}

try:
    response = requests.get(index_url, headers=headers, timeout=30)
    print(f"状态码: {response.status_code}\n")

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # 查找Documents按钮
        doc_links = soup.find_all("a", {"id": "documentsbutton"})
        if doc_links:
            print(f"找到 {len(doc_links)} 个Documents链接\n")
            first_doc_link = doc_links[0]["href"]
            print(f"第一个文件的Documents页面: https://www.sec.gov{first_doc_link}\n")

            # 访问Documents页面
            doc_response = requests.get(
                f"https://www.sec.gov{first_doc_link}", headers=headers, timeout=30
            )
            if doc_response.status_code == 200:
                doc_soup = BeautifulSoup(doc_response.text, "html.parser")

                print("文件列表:")
                print("=" * 80)

                # 查找文件表格
                table = doc_soup.find("table", {"class": "tableFile"})
                if table:
                    rows = table.find_all("tr")[1:]  # 跳过表头
                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) >= 3:
                            doc_type = (
                                cols[3].get_text().strip() if len(cols) > 3 else ""
                            )
                            filename = cols[2].get_text().strip()
                            link = cols[2].find("a")

                            if link and "xml" in filename.lower():
                                file_url = f"https://www.sec.gov{link['href']}"
                                print(f"类型: {doc_type}")
                                print(f"文件名: {filename}")
                                print(f"URL: {file_url}")
                                print("-" * 80)

except Exception as e:
    print(f"错误: {e}")
    import traceback

    traceback.print_exc()
