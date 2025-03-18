import json
import requests
from typing import Dict, Any

# DeepSeek API配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # 请根据实际API地址调整
DEEPSEEK_API_KEY = "sk-d896625d1b1d408c96ca3b6e2ef5abb5"  # 替换为您的实际API密钥

def generate_analysis(data: Dict[Any, Any]) -> str:
    """使用DeepSeek AI生成销售数据分析"""
    try:
        # 确保所有数据都是可序列化的
        # 准备销售数据摘要
        data_summary = {
            "top_sales": data.get('top_sales', []),
            "top_increased": data.get('top_increased', []),
            "top_decreased": data.get('top_decreased', []),
            "country_distribution": data.get('country_distribution', []),
            "platform_data": data.get('platform_comparison', {}),
            "salesperson_data": data.get('salesperson_comparison', [])
        }
        
        # 格式化销售数据为文本，以便AI分析
        sales_data_text = format_data_for_prompt(data_summary)
        
        # 创建DeepSeek请求
        prompt = f"""
        作为一名电子商务销售数据分析专家，请基于以下跨境电商销售数据对业务表现进行详细分析。
        请提供具体的业务洞察和改进建议。
        
        数据摘要:
        {sales_data_text}
        
        请从以下几个方面进行分析:
        1. 热销商品分析和建议
        2. 产品涨跌趋势分析
        3. 各国市场表现分析
        4. 销售平台表现分析
        5. 整体销售趋势和建议
        
        格式要求:
        - 使用Markdown格式
        - 每个部分使用二级标题
        - 对重要的发现使用粗体强调
        - 包含3-5条切实可行的业务建议
        """
        
        # 调用DeepSeek API
        response = call_deepseek_api(prompt)
        
        # 如果没有获得AI响应，生成基本分析
        if not response:
            return generate_fallback_analysis(data_summary)
            
        return response
        
    except Exception as e:
        print(f"AI分析生成错误: {str(e)}")
        # 出错时返回基本分析
        return generate_fallback_analysis(data_summary)
    
def call_deepseek_api(prompt: str) -> str:
    """调用DeepSeek API"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        payload = {
            "model": "deepseek-chat",  # 使用适合的模型名称
            "messages": [
                {"role": "system", "content": "你是一位专业的电子商务销售数据分析师，擅长从数据中提取业务洞察。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,  # 较低的温度确保输出的一致性
            "max_tokens": 4000
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            print(f"DeepSeek API错误: {response.status_code}, {response.text}")
            return ""
    except requests.exceptions.Timeout:
        print("DeepSeek API请求超时")
        return ""        
    except Exception as e:
        print(f"调用DeepSeek API时出错: {str(e)}")
        return ""

def format_data_for_prompt(data_summary: Dict) -> str:
    """将数据格式化为AI提示的文本格式"""
    formatted_text = ""
    
    # 添加销售额Top5
    formatted_text += "## 销售额Top5商品:\n"
    for item in data_summary["top_sales"][:5]:
        formatted_text += f"- {item['product_name']} (SKU: {item['sku']}): ¥{item['value']:.2f}\n"
    
    # 添加环比上升Top5
    formatted_text += "\n## 销量环比上升Top5:\n"
    for item in data_summary["top_increased"][:5]:
        formatted_text += f"- {item['product_name']} (SKU: {item['sku']}): {item['change_rate']:.2f}% (本周:{item['current_value']}, 上周:{item['previous_value']})\n"
    
    # 添加环比下降Top5
    formatted_text += "\n## 销量环比下降Top5:\n"
    for item in data_summary["top_decreased"][:5]:
        formatted_text += f"- {item['product_name']} (SKU: {item['sku']}): {item['change_rate']:.2f}% (本周:{item['current_value']}, 上周:{item['previous_value']})\n"
    
    # 添加国家分布
    formatted_text += "\n## 国家销售分布:\n"
    for item in data_summary["country_distribution"]:
        formatted_text += f"- {item['country']}: ¥{item['value']:.2f} ({item['percent']:.2f}%), 环比变化: {item['change_rate']:.2f}%\n"
    
    # 添加平台数据
    platform = data_summary["platform_data"]
    formatted_text += "\n## 平台总体表现:\n"
    formatted_text += f"- 销售额: ¥{platform.get('current_amount', 0):.2f}, 环比变化: {platform.get('amount_change_rate', 0):.2f}%\n"
    formatted_text += f"- 销量: {platform.get('current_volume', 0):.2f}, 环比变化: {platform.get('volume_change_rate', 0):.2f}%\n"
    formatted_text += f"- 订单数: {platform.get('current_orders', 0)}, 环比变化: {platform.get('orders_change_rate', 0):.2f}%\n"
    if platform.get('current_profit_rate') is not None:
        formatted_text += f"- 毛利率: {platform.get('current_profit_rate', 0):.2f}%, 环比变化: {platform.get('profit_rate_change', 0):.2f}%\n"
    
    return formatted_text

def generate_fallback_analysis(data_summary: Dict) -> str:
    """生成基本的分析结果（当AI API调用失败时使用）"""
    analysis = """
## 销售数据分析报告

### 热销商品分析
"""
    # 添加热销商品分析
    if data_summary["top_sales"]:
        analysis += "本周销售额前五的产品是:\n\n"
        for i, product in enumerate(data_summary["top_sales"][:5], 1):
            analysis += f"{i}. **{product['product_name']}** (SKU: {product['sku']})，销售额: ¥{product['value']:.2f}\n"
        analysis += "\n**建议**: 确保这些热销商品库存充足，并考虑开发相似产品线。\n\n"
    
    # 产品涨跌趋势
    analysis += "### 产品涨跌趋势分析\n\n"
    
    if data_summary["top_increased"]:
        analysis += "**销量增长最快的产品**:\n\n"
        for i, product in enumerate(data_summary["top_increased"][:3], 1):
            analysis += f"{i}. **{product['product_name']}** 增长率: {product['change_rate']:.2f}%\n"
        analysis += "\n**建议**: 增加这些产品的营销投入，扩大增长趋势。\n\n"
    
    if data_summary["top_decreased"]:
        analysis += "**销量下降最多的产品**:\n\n"
        for i, product in enumerate(data_summary["top_decreased"][:3], 1):
            analysis += f"{i}. **{product['product_name']}** 下降率: {product['change_rate']:.2f}%\n"
        analysis += "\n**建议**: 检查这些产品的价格竞争力和市场定位，考虑调整促销策略。\n\n"
    
    # 国家分布分析
    analysis += "### 各国市场表现分析\n\n"
    
    if data_summary["country_distribution"]:
        # 按销售额排序
        sorted_countries = sorted(data_summary["country_distribution"], key=lambda x: x['value'], reverse=True)
        top_countries = sorted_countries[:3]
        
        analysis += "主要销售市场:\n\n"
        for i, country in enumerate(top_countries, 1):
            analysis += f"{i}. **{country['country']}**: 销售额 ¥{country['value']:.2f} (占比 {country['percent']:.2f}%)，环比变化 {country['change_rate']:.2f}%\n"
        
        # 寻找增长最快的市场
        growth_countries = sorted(data_summary["country_distribution"], key=lambda x: x['change_rate'], reverse=True)
        if growth_countries and growth_countries[0]['change_rate'] > 0:
            analysis += f"\n增长最快的市场是 **{growth_countries[0]['country']}**，环比增长 {growth_countries[0]['change_rate']:.2f}%\n"
        
        analysis += "\n**建议**: 对主要市场增加本地化服务，探索增长市场的新机会。\n\n"
    
    # 整体业务建议
    analysis += """### 整体业务建议

1. **库存管理优化**: 根据热销商品和增长趋势调整库存水平
2. **营销资源分配**: 将资源集中在增长市场和增长产品上
3. **产品组合调整**: 考虑淘汰持续下滑的产品，增加有增长潜力的品类
4. **价格策略优化**: 对下滑产品进行价格竞争力分析，必要时调整定价
5. **市场扩展计划**: 基于国家分布数据，制定新市场开发计划

*分析基于当前可用数据生成，建议结合实际业务情况进行决策。*
"""
    
    return analysis 