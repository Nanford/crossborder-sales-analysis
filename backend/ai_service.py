import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv
import os

# 加载.env文件中的环境变量
load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # 请根据实际API地址调整
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") 

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
            "max_tokens": 3000
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=180)
        
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
        formatted_text += f"- {item['product_name']} (SKU: {item['sku']}): ${item['value']:.2f}\n"
    
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
        formatted_text += f"- {item['country']}: ${item['value']:.2f} ({item['percent']:.2f}%), 环比变化: {item['change_rate']:.2f}%\n"
    
    # 添加平台数据
    platform = data_summary["platform_data"]
    formatted_text += "\n## 平台总体表现:\n"
    formatted_text += f"- 销售额: ${platform.get('current_amount', 0):.2f}, 环比变化: {platform.get('amount_change_rate', 0):.2f}%\n"
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
        analysis += "请求失败展示样例数据：本周销售额前五的产品是:\n\n"
        for i, product in enumerate(data_summary["top_sales"][:5], 1):
            analysis += f"{i}. **{product['product_name']}** (SKU: {product['sku']})，销售额: ${product['value']:.2f}\n"
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
            analysis += f"{i}. **{country['country']}**: 销售额 ${country['value']:.2f} (占比 {country['percent']:.2f}%)，环比变化 {country['change_rate']:.2f}%\n"
        
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

def generate_monthly_analysis(data: Dict[Any, Any]) -> str:
    """使用DeepSeek AI生成月度销售数据分析"""
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
        sales_data_text = format_monthly_data_for_prompt(data_summary)
        
        # 创建DeepSeek请求
        prompt = f"""
        作为一名电子商务销售数据分析专家，请基于以下跨境电商月度销售数据对业务表现进行详细分析。
        请提供具体的业务洞察和改进建议。
        
        月度销售数据摘要:
        {sales_data_text}
        
        请从以下几个方面进行分析:
        1. 热销商品分析和建议
        2. 产品月度环比趋势分析
        3. 各国月度市场表现分析
        4. 销售平台月度表现分析
        5. 销售团队业绩分析
        6. 整体销售趋势和建议
        
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
            return generate_monthly_fallback_analysis(data_summary)
            
        return response
        
    except Exception as e:
        print(f"月度AI分析生成错误: {str(e)}")
        # 出错时返回基本分析
        return generate_monthly_fallback_analysis(data_summary)

def format_monthly_data_for_prompt(data_summary: Dict) -> str:
    """将月度数据格式化为AI提示的文本格式"""
    formatted_text = ""
    
    # 添加销售额Top5
    formatted_text += "## 月度销售额Top5商品:\n"
    for item in data_summary["top_sales"][:5]:
        formatted_text += f"- {item.get('product_name', '未知产品')} (SKU: {item.get('sku', '未知')}): ${item.get('value', 0):.2f}\n"
    
    # 添加环比上升Top5
    formatted_text += "\n## 月度销量环比上升Top5:\n"
    for item in data_summary["top_increased"][:5]:
        formatted_text += f"- {item.get('product_name', '未知产品')} (SKU: {item.get('sku', '未知')}): {item.get('change_rate', 0):.2f}% (当月:{item.get('current_value', 0)}, 上月:{item.get('previous_value', 0)})\n"
    
    # 添加环比下降Top5
    formatted_text += "\n## 月度销量环比下降Top5:\n"
    for item in data_summary["top_decreased"][:5]:
        formatted_text += f"- {item.get('product_name', '未知产品')} (SKU: {item.get('sku', '未知')}): {item.get('change_rate', 0):.2f}% (当月:{item.get('current_value', 0)}, 上月:{item.get('previous_value', 0)})\n"
    
    # 添加国家分布
    formatted_text += "\n## 月度国家销售分布:\n"
    for item in data_summary["country_distribution"][:5]:  # 只取前5个国家
        formatted_text += f"- {item.get('country', '未知')}：${item.get('value', 0):.2f} ({item.get('percent', 0):.2f}%), 环比变化: {item.get('change_rate', 0):.2f}%\n"
    
    # 添加平台数据
    platform_data = data_summary["platform_data"]
    formatted_text += "\n## 月度各平台表现:\n"
    
    # 如果是新的平台数据结构（有platforms字段）
    if isinstance(platform_data, dict) and platform_data.get('platforms'):
        platforms = platform_data.get('platforms', [])
        current_data = platform_data.get('current', {})
        previous_data = platform_data.get('previous', {})
        
        for platform in platforms:
            current = current_data.get(platform, {})
            previous = previous_data.get(platform, {})
            
            formatted_text += f"### {platform} 平台:\n"
            
            # 销售额环比
            current_amount = current.get('sales_amount', 0)
            previous_amount = previous.get('sales_amount', 0)
            amount_change = ((current_amount - previous_amount) / previous_amount * 100) if previous_amount > 0 else 0
            formatted_text += f"- 销售额: ${current_amount:.2f}, 环比变化: {amount_change:.2f}%\n"
            
            # 销量环比
            current_volume = current.get('sales_volume', 0)
            previous_volume = previous.get('sales_volume', 0)
            volume_change = ((current_volume - previous_volume) / previous_volume * 100) if previous_volume > 0 else 0
            formatted_text += f"- 销量: {current_volume}, 环比变化: {volume_change:.2f}%\n"
            
            # 订单数环比
            current_orders = current.get('order_count', 0)
            previous_orders = previous.get('order_count', 0)
            orders_change = ((current_orders - previous_orders) / previous_orders * 100) if previous_orders > 0 else 0
            formatted_text += f"- 订单数: {current_orders}, 环比变化: {orders_change:.2f}%\n"
            
            # 毛利率
            current_profit = current.get('profit_rate', 0)
            previous_profit = previous.get('profit_rate', 0)
            profit_change = current_profit - previous_profit
            formatted_text += f"- 毛利率: {current_profit:.2f}%, 环比变化: {profit_change:.2f}%\n\n"
    else:
        # 旧数据结构处理
        formatted_text += f"- 销售额: ${platform_data.get('current_amount', 0):.2f}, 环比变化: {platform_data.get('amount_change_rate', 0):.2f}%\n"
        formatted_text += f"- 销量: {platform_data.get('current_volume', 0)}, 环比变化: {platform_data.get('volume_change_rate', 0):.2f}%\n"
        formatted_text += f"- 订单数: {platform_data.get('current_orders', 0)}, 环比变化: {platform_data.get('orders_change_rate', 0):.2f}%\n"
        profit_rate = platform_data.get('current_profit_rate')
        if profit_rate is not None:
            formatted_text += f"- 毛利率: {profit_rate:.2f}%, 环比变化: {platform_data.get('profit_rate_change', 0):.2f}%\n"
    
    # 添加销售人员业绩数据
    formatted_text += "\n## 销售人员月度业绩:\n"
    for idx, person in enumerate(data_summary["salesperson_data"][:5]):  # 只取前5位销售
        formatted_text += f"### {person.get('sales_person', f'销售{idx+1}')}:\n"
        formatted_text += f"- 销售额: ${person.get('current_amount', 0):.2f}, 环比变化: {person.get('amount_change_rate', 0):.2f}%\n"
        formatted_text += f"- 销量: {person.get('current_volume', 0)}, 环比变化: {person.get('volume_change_rate', 0):.2f}%\n"
        formatted_text += f"- 订单数: {person.get('current_orders', 0)}, 环比变化: {person.get('orders_change_rate', 0):.2f}%\n"
        formatted_text += f"- 毛利率: {person.get('current_profit_rate', 0):.2f}%, 环比变化: {person.get('profit_rate_change', 0):.2f}%\n\n"
    
    return formatted_text

def generate_monthly_fallback_analysis(data_summary: Dict) -> str:
    """生成基本的月度分析结果（当AI API调用失败时使用）"""
    analysis = """
## 月度销售数据分析报告

### 热销商品分析
"""
    # 添加热销商品分析
    if data_summary["top_sales"]:
        analysis += "本月销售额前五的产品是:\n\n"
        for i, product in enumerate(data_summary["top_sales"][:5], 1):
            analysis += f"{i}. **{product.get('product_name', '未知产品')}** (SKU: {product.get('sku', '未知')})，销售额: ${product.get('value', 0):.2f}\n"
        analysis += "\n**建议**: 确保这些热销商品库存充足，并考虑开发相似产品线。\n\n"
    
    # 产品涨跌趋势
    analysis += "### 产品月度涨跌趋势分析\n\n"
    
    if data_summary["top_increased"]:
        analysis += "**销量增长最快的产品**:\n\n"
        for i, product in enumerate(data_summary["top_increased"][:3], 1):
            analysis += f"{i}. **{product.get('product_name', '未知产品')}** 增长率: {product.get('change_rate', 0):.2f}%\n"
        analysis += "\n**建议**: 增加这些产品的营销投入，扩大增长趋势。\n\n"
    
    if data_summary["top_decreased"]:
        analysis += "**销量下降最多的产品**:\n\n"
        for i, product in enumerate(data_summary["top_decreased"][:3], 1):
            analysis += f"{i}. **{product.get('product_name', '未知产品')}** 下降率: {product.get('change_rate', 0):.2f}%\n"
        analysis += "\n**建议**: 检查这些产品的价格竞争力和市场定位，考虑调整促销策略。\n\n"
    
    # 国家分布分析
    analysis += "### 各国月度市场表现分析\n\n"
    
    if data_summary["country_distribution"]:
        # 按销售额排序
        sorted_countries = sorted(data_summary["country_distribution"], key=lambda x: x.get('value', 0), reverse=True)
        top_countries = sorted_countries[:3]
        
        analysis += "主要销售市场:\n\n"
        for i, country in enumerate(top_countries, 1):
            analysis += f"{i}. **{country.get('country', '未知')}**: 销售额 ${country.get('value', 0):.2f} (占比 {country.get('percent', 0):.2f}%)，环比变化 {country.get('change_rate', 0):.2f}%\n"
        
        # 寻找增长最快的市场
        growth_countries = sorted(data_summary["country_distribution"], key=lambda x: x.get('change_rate', 0), reverse=True)
        if growth_countries and growth_countries[0].get('change_rate', 0) > 0:
            analysis += f"\n增长最快的市场是 **{growth_countries[0].get('country', '未知')}**，环比增长 {growth_countries[0].get('change_rate', 0):.2f}%\n"
        
        analysis += "\n**建议**: 对主要市场增加本地化服务，探索增长市场的新机会。\n\n"
    
    # 平台表现分析
    analysis += "### 平台月度表现分析\n\n"
    platform_data = data_summary["platform_data"]
    
    if isinstance(platform_data, dict) and platform_data.get('platforms'):
        platforms = platform_data.get('platforms', [])
        current_data = platform_data.get('current', {})
        previous_data = platform_data.get('previous', {})
        
        # 找出表现最好的平台
        best_platform = None
        best_growth = -float('inf')
        
        for platform in platforms:
            current = current_data.get(platform, {})
            previous = previous_data.get(platform, {})
            
            current_amount = current.get('sales_amount', 0)
            previous_amount = previous.get('sales_amount', 0)
            
            if previous_amount > 0:
                growth = ((current_amount - previous_amount) / previous_amount * 100)
                if growth > best_growth:
                    best_growth = growth
                    best_platform = platform
        
        if best_platform:
            analysis += f"**表现最佳的平台**: {best_platform}，销售额环比增长 {best_growth:.2f}%\n\n"
            
        analysis += "**平台表现概况**:\n\n"
        for platform in platforms[:3]:  # 只展示前三个平台
            current = current_data.get(platform, {})
            previous = previous_data.get(platform, {})
            
            current_amount = current.get('sales_amount', 0)
            previous_amount = previous.get('sales_amount', 0)
            amount_change = ((current_amount - previous_amount) / previous_amount * 100) if previous_amount > 0 else 0
            
            analysis += f"- **{platform}**: 销售额 ${current_amount:.2f}，环比变化 {amount_change:.2f}%\n"
    
    # 销售团队表现分析
    analysis += "\n### 销售团队月度表现分析\n\n"
    
    if data_summary["salesperson_data"]:
        # 按销售额排序
        sorted_salespersons = sorted(data_summary["salesperson_data"], key=lambda x: x.get('current_amount', 0), reverse=True)
        top_salespersons = sorted_salespersons[:3]
        
        analysis += "**销售业绩前三**:\n\n"
        for i, person in enumerate(top_salespersons, 1):
            analysis += f"{i}. **{person.get('sales_person', f'销售{i}')}**: 销售额 ${person.get('current_amount', 0):.2f}，环比变化 {person.get('amount_change_rate', 0):.2f}%\n"
        
        # 寻找增长最快的销售
        growth_salespersons = sorted(data_summary["salesperson_data"], key=lambda x: x.get('amount_change_rate', 0), reverse=True)
        if growth_salespersons and growth_salespersons[0].get('amount_change_rate', 0) > 0:
            analysis += f"\n**增长最快的销售**: {growth_salespersons[0].get('sales_person', '未知')}，环比增长 {growth_salespersons[0].get('amount_change_rate', 0):.2f}%\n"
    
    # 整体业务建议
    analysis += """
### 整体业务建议

1. **库存管理优化**: 根据月度热销商品和增长趋势调整库存水平，避免滞销积压
2. **销售团队激励**: 分析高绩效销售的成功经验，建立有效的奖励机制提升整体团队业绩
3. **平台资源分配**: 将更多资源投入到表现较好的平台，提高投资回报率
4. **市场扩展计划**: 基于国家分布数据，制定新市场开发和现有市场深耕计划
5. **产品组合优化**: 逐步淘汰持续下滑的产品，增加有增长潜力的品类

*分析基于当前可用月度数据生成，建议结合实际业务情况进行决策。*
"""
    
    return analysis