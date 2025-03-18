import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """测试所有API端点并输出响应数据结构"""
    endpoints = [
        "/analysis/top-sales-volume/",
        "/analysis/top-sales-amount/",
        "/analysis/top-increased/",
        "/analysis/top-decreased/",
        "/analysis/country-distribution/",
        "/analysis/platform-comparison/",
        "/analysis/salesperson-comparison/"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        full_url = f"{BASE_URL}{endpoint}"
        print(f"\n测试API: {full_url}")
        
        try:
            response = requests.get(full_url)
            response.raise_for_status()
            
            data = response.json()
            results[endpoint] = {
                "status": response.status_code,
                "data_type": type(data).__name__,
                "sample": data[:2] if isinstance(data, list) and data else data,
                "success": True
            }
            
            if isinstance(data, list) and data:
                print(f"返回 {len(data)} 条记录")
                print("数据字段:", list(data[0].keys()) if data else "空数据")
                print("第一条记录样本:")
                pprint(data[0])
            else:
                print("返回数据:")
                pprint(data)
            
        except Exception as e:
            results[endpoint] = {
                "status": getattr(response, "status_code", "Unknown"),
                "error": str(e),
                "success": False
            }
            print(f"错误: {str(e)}")
    
    # 保存结果到文件
    with open("api_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n测试结果已保存到 api_test_results.json")

if __name__ == "__main__":
    test_api_endpoints() 