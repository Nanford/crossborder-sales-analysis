from sqlalchemy import Column, Integer, String, Float, DateTime, func, text
from sqlalchemy.sql import text
from database import Base, engine
from typing import List

class SalesData(Base):
    __tablename__ = "sales_data"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), index=True)
    spu = Column(String(100), index=True)
    platform = Column(String(100), index=True)
    shop = Column(String(100))
    site = Column(String(100))
    warehouse = Column(String(100))
    buyer_country = Column(String(100), index=True)
    sales_person = Column(String(100), index=True)
    order_count = Column(Integer, default=0)
    product_name = Column(String(500))
    sales_volume = Column(Float, default=0)
    sales_amount = Column(Float, default=0)
    cost = Column(Float, nullable=True)
    profit = Column(Float, nullable=True)
    profit_rate = Column(Float, default=0)
    order_status = Column(String(100), nullable=True)
    week = Column(String(20), index=True)
    month = Column(String(20))
    created_at = Column(DateTime, default=func.now())

# 创建数据库表
def create_tables():
    Base.metadata.create_all(bind=engine)

# 数据分析功能实现
def get_top_sales_volume(db, week=None, limit=5):
    """获取销量Top5"""
    query = db.query(
        SalesData.sku,
        SalesData.product_name,
        func.sum(SalesData.sales_volume).label('total_sales_volume')
    )
    
    if week:
        query = query.filter(SalesData.week == week)
    
    results = query.group_by(
        SalesData.sku,
        SalesData.product_name
    ).order_by(text('total_sales_volume DESC')).limit(limit).all()
    
    # 转换为字典列表
    return [
        {
            "sku": row.sku,
            "product_name": row.product_name,
            "value": float(row.total_sales_volume)
        }
        for row in results
    ]

def get_top_sales_amount(db, week=None, limit=5):
    """获取销售额Top5"""
    query = db.query(
        SalesData.sku,
        SalesData.product_name,
        func.sum(SalesData.sales_amount).label('total_sales_amount')
    )
    
    if week:
        query = query.filter(SalesData.week == week)
    
    results = query.group_by(
        SalesData.sku,
        SalesData.product_name
    ).order_by(text('total_sales_amount DESC')).limit(limit).all()
    
    # 转换为字典列表
    return [
        {
            "sku": row.sku,
            "product_name": row.product_name,
            "value": float(row.total_sales_amount)
        }
        for row in results
    ]

def get_top_increased_sales_amount(db, limit=5):
    """获取环比销售额上升Top5（按绝对增长量排序）"""
    query = """
    SELECT 
        t1.sku,
        t1.product_name,
        t1.current_amount,
        t2.previous_amount,
        (t1.current_amount - t2.previous_amount) AS amount_change,
        CASE 
            WHEN t2.previous_amount > 0 THEN 
                ((t1.current_amount - t2.previous_amount) / t2.previous_amount) * 100
            ELSE 0
        END AS change_rate
    FROM 
        (SELECT 
            sku, 
            product_name, 
            SUM(sales_amount) AS current_amount
         FROM 
            sales_data
         WHERE 
            week = '本周'
         GROUP BY 
            sku, product_name) AS t1
    JOIN 
        (SELECT 
            sku, 
            product_name, 
            SUM(sales_amount) AS previous_amount
         FROM 
            sales_data
         WHERE 
            week = '上周'
         GROUP BY 
            sku, product_name) AS t2
    ON 
        t1.sku = t2.sku
    WHERE
        t1.current_amount > t2.previous_amount
    ORDER BY 
        amount_change DESC
    LIMIT :limit
    """
    
    results = db.execute(text(query), {"limit": limit}).fetchall()
    
    # 确保数据转换正确，明确指定数据类型
    return [
        {
            "sku": row[0],
            "product_name": row[1],
            "current_value": float(row[2]) if row[2] is not None else 0.0,
            "previous_value": float(row[3]) if row[3] is not None else 0.0,
            "amount_change": float(row[4]) if row[4] is not None else 0.0,  # 确保这是正确的增长量
            "change_rate": float(row[5]) if row[5] is not None else 0.0
        }
        for row in results
    ]

def get_top_decreased_sales_amount(db, limit=5):
    """获取环比销售额下降Top5（按绝对下降量排序）"""
    query = """
    SELECT 
        t1.sku,
        t1.product_name,
        t1.current_amount,
        t2.previous_amount,
        (t2.previous_amount - t1.current_amount) AS amount_decrease,
        CASE 
            WHEN t2.previous_amount > 0 THEN 
                ((t1.current_amount - t2.previous_amount) / t2.previous_amount) * 100
            ELSE 0
        END AS change_rate
    FROM 
        (SELECT 
            sku, 
            product_name, 
            SUM(sales_amount) AS current_amount
         FROM 
            sales_data
         WHERE 
            week = '本周'
         GROUP BY 
            sku, product_name) AS t1
    JOIN 
        (SELECT 
            sku, 
            product_name, 
            SUM(sales_amount) AS previous_amount
         FROM 
            sales_data
         WHERE 
            week = '上周'
         GROUP BY 
            sku, product_name) AS t2
    ON 
        t1.sku = t2.sku
    WHERE
        t1.current_amount < t2.previous_amount
    ORDER BY 
        amount_decrease DESC
    LIMIT :limit
    """
    
    results = db.execute(text(query), {"limit": limit}).fetchall()
    
    # 确保数据转换正确，明确指定数据类型
    return [
        {
            "sku": row[0],
            "product_name": row[1],
            "current_value": float(row[2]) if row[2] is not None else 0.0,
            "previous_value": float(row[3]) if row[3] is not None else 0.0,
            "amount_decrease": float(row[4]) if row[4] is not None else 0.0,  # 确保这是正确的下降量
            "change_rate": float(row[5]) if row[5] is not None else 0.0
        }
        for row in results
    ]

def get_country_sales_distribution(db):
    """获取不同国家销售额占比和环比情况"""
    # 当前周数据
    current_week_data = db.query(
        SalesData.buyer_country,
        func.sum(SalesData.sales_amount).label('current_amount')
    ).filter(SalesData.week == "本周").group_by(
        SalesData.buyer_country
    ).subquery()
    
    # 上周数据
    previous_week_data = db.query(
        SalesData.buyer_country,
        func.sum(SalesData.sales_amount).label('previous_amount')
    ).filter(SalesData.week == "上周").group_by(
        SalesData.buyer_country
    ).subquery()
    
    # 合并查询
    results = db.query(
        current_week_data.c.buyer_country,
        current_week_data.c.current_amount,
        previous_week_data.c.previous_amount
    ).outerjoin(
        previous_week_data,
        current_week_data.c.buyer_country == previous_week_data.c.buyer_country
    ).all()
    
    # 计算总销售额用于计算占比
    total_current = sum([r.current_amount for r in results if r.current_amount])
    
    # 转换为字典列表
    return [
        {
            "country": row.buyer_country or "未知",
            "value": float(row.current_amount or 0),
            "percent": float(row.current_amount) / total_current * 100 if total_current else 0,
            "previous_value": float(row.previous_amount or 0),
            "change_rate": ((float(row.current_amount or 0) - float(row.previous_amount or 0)) / 
                            float(row.previous_amount or 1) * 100) if row.previous_amount else 0
        }
        for row in results
    ]

def get_platform_comparison(db):
    """获取平台销售额、销量、订单、毛利率环比"""
    query = """
    SELECT 
        SUM(CASE WHEN week = '本周' THEN sales_amount ELSE 0 END) as current_amount,
        SUM(CASE WHEN week = '上周' THEN sales_amount ELSE 0 END) as previous_amount,
        SUM(CASE WHEN week = '本周' THEN sales_volume ELSE 0 END) as current_volume,
        SUM(CASE WHEN week = '上周' THEN sales_volume ELSE 0 END) as previous_volume,
        SUM(CASE WHEN week = '本周' THEN order_count ELSE 0 END) as current_orders,
        SUM(CASE WHEN week = '上周' THEN order_count ELSE 0 END) as previous_orders,
        AVG(CASE WHEN week = '本周' THEN profit_rate ELSE NULL END) as current_profit_rate,
        AVG(CASE WHEN week = '上周' THEN profit_rate ELSE NULL END) as previous_profit_rate
    FROM 
        sales_data
    """
    
    result = db.execute(text(query)).fetchone()
    return {
        "current_amount": result[0],
        "previous_amount": result[1],
        "amount_change_rate": (result[0] - result[1]) / result[1] * 100 if result[1] else None,
        "current_volume": result[2],
        "previous_volume": result[3],
        "volume_change_rate": (result[2] - result[3]) / result[3] * 100 if result[3] else None,
        "current_orders": result[4],
        "previous_orders": result[5],
        "orders_change_rate": (result[4] - result[5]) / result[5] * 100 if result[5] else None,
        "current_profit_rate": result[6],
        "previous_profit_rate": result[7],
        "profit_rate_change": result[6] - result[7] if result[6] and result[7] else None
    }

def get_salesperson_comparison(db):
    """获取销售人员销售额、销量、订单、毛利率环比"""
    query = """
    SELECT 
        sales_person,
        SUM(CASE WHEN week = '本周' THEN sales_amount ELSE 0 END) as current_amount,
        SUM(CASE WHEN week = '上周' THEN sales_amount ELSE 0 END) as previous_amount,
        SUM(CASE WHEN week = '本周' THEN sales_volume ELSE 0 END) as current_volume,
        SUM(CASE WHEN week = '上周' THEN sales_volume ELSE 0 END) as previous_volume,
        SUM(CASE WHEN week = '本周' THEN order_count ELSE 0 END) as current_orders,
        SUM(CASE WHEN week = '上周' THEN order_count ELSE 0 END) as previous_orders,
        AVG(CASE WHEN week = '本周' THEN profit_rate ELSE NULL END) as current_profit_rate,
        AVG(CASE WHEN week = '上周' THEN profit_rate ELSE NULL END) as previous_profit_rate
    FROM 
        sales_data
    GROUP BY 
        sales_person
    HAVING 
        current_amount > 0 OR previous_amount > 0
    ORDER BY 
        current_amount DESC
    """
    
    results = db.execute(text(query)).fetchall()
    return [
        {
            "sales_person": result[0],
            "current_amount": result[1],
            "previous_amount": result[2],
            "amount_change_rate": (result[1] - result[2]) / result[2] * 100 if result[2] else None,
            "current_volume": result[3],
            "previous_volume": result[4],
            "volume_change_rate": (result[3] - result[4]) / result[4] * 100 if result[4] else None,
            "current_orders": result[5],
            "previous_orders": result[6],
            "orders_change_rate": (result[5] - result[6]) / result[6] * 100 if result[6] else None,
            "current_profit_rate": result[7],
            "previous_profit_rate": result[8],
            "profit_rate_change": result[7] - result[8] if result[7] and result[8] else None
        }
        for result in results
    ]

def get_data_for_ai_analysis(db):
    """获取用于AI分析的数据"""
    # 获取销售额Top5
    top_sales = get_top_sales_amount(db, limit=5)
    
    # 获取环比增长和下降数据
    increased = get_top_increased_sales_amount(db, limit=5)
    decreased = get_top_decreased_sales_amount(db, limit=5)
    
    # 获取国家分布
    country_distribution = get_country_sales_distribution(db)
    
    # 获取平台总体数据
    platform_data = get_platform_comparison(db)
    
    return {
        "top_sales": top_sales,
        "increased_sales": increased,
        "decreased_sales": decreased,
        "country_distribution": country_distribution,
        "platform_data": platform_data
    } 

def get_no_orders_this_week(db, limit=5):
    """获取上周有出单但本周没有出单的SKU，按上周销售额排序"""
    query = """
    SELECT 
        t2.sku,
        t2.product_name,
        t2.sales_amount AS previous_amount
    FROM 
        (SELECT 
            sku
         FROM 
            sales_data
         WHERE 
            week = '本周'
         GROUP BY 
            sku) AS t1
    RIGHT JOIN 
        (SELECT 
            sku, 
            product_name, 
            SUM(sales_amount) AS sales_amount
         FROM 
            sales_data
         WHERE 
            week = '上周'
         GROUP BY 
            sku, product_name) AS t2
    ON 
        t1.sku = t2.sku
    WHERE
        t1.sku IS NULL
    ORDER BY 
        t2.sales_amount DESC
    LIMIT :limit
    """
    
    results = db.execute(text(query), {"limit": limit}).fetchall()
    
    # 转换为字典列表
    return [
        {
            "sku": row[0],
            "product_name": row[1],
            "value": float(row[2]) if row[2] is not None else 0.0
        }
        for row in results
    ]

def get_month_top_sales_volume(db, month=None, limit=10):
    """获取月度销量Top10"""
    query = db.query(
        SalesData.sku,
        SalesData.product_name,
        func.sum(SalesData.sales_volume).label('total_sales_volume')
    )
    
    if month:
        query = query.filter(SalesData.month == month)
    
    results = query.group_by(
        SalesData.sku,
        SalesData.product_name
    ).order_by(text('total_sales_volume DESC')).limit(limit).all()
    
    # 转换为字典列表
    return [
        {
            "sku": row.sku,
            "product_name": row.product_name,
            "value": float(row.total_sales_volume)
        }
        for row in results
    ]

def get_month_top_sales_amount(db, month=None, limit=10):
    """获取月度销售额Top10"""
    query = db.query(
        SalesData.sku,
        SalesData.product_name,
        func.sum(SalesData.sales_amount).label('total_sales_amount')
    )
    
    if month:
        query = query.filter(SalesData.month == month)
    
    results = query.group_by(
        SalesData.sku,
        SalesData.product_name
    ).order_by(text('total_sales_amount DESC')).limit(limit).all()
    
    # 转换为字典列表
    return [
        {
            "sku": row.sku,
            "product_name": row.product_name,
            "value": float(row.total_sales_amount)
        }
        for row in results
    ]

def get_month_top_increased_sales_volume(db, current_month=None, previous_month=None, limit=10):
    """获取月度环比销量上升Top10"""
    if not current_month or not previous_month:
        # 获取所有月份并按降序排列
        all_months = db.query(SalesData.month).distinct().order_by(SalesData.month.desc()).all()
        months = [m[0] for m in all_months if m[0]]
        
        if len(months) >= 2:
            current_month = months[0]
            previous_month = months[1]
        else:
            return []  # 没有足够的月份数据进行比较
    
    query = """
    SELECT 
        t1.sku,
        t1.product_name,
        t1.current_volume,
        t2.previous_volume,
        (t1.current_volume - t2.previous_volume) AS volume_change,
        CASE 
            WHEN t2.previous_volume > 0 THEN 
                ((t1.current_volume - t2.previous_volume) / t2.previous_volume) * 100
            ELSE 0
        END AS change_rate
    FROM 
        (SELECT 
            sku, 
            product_name, 
            SUM(sales_volume) AS current_volume
         FROM 
            sales_data
         WHERE 
            month = :current_month
         GROUP BY 
            sku, product_name) AS t1
    JOIN 
        (SELECT 
            sku, 
            product_name, 
            SUM(sales_volume) AS previous_volume
         FROM 
            sales_data
         WHERE 
            month = :previous_month
         GROUP BY 
            sku, product_name) AS t2
    ON 
        t1.sku = t2.sku
    WHERE
        t1.current_volume > t2.previous_volume
    ORDER BY 
        volume_change DESC
    LIMIT :limit
    """
    
    results = db.execute(text(query), {
        "current_month": current_month,
        "previous_month": previous_month,
        "limit": limit
    }).fetchall()
    
    return [
        {
            "sku": row[0],
            "product_name": row[1],
            "current_value": float(row[2]) if row[2] is not None else 0.0,
            "previous_value": float(row[3]) if row[3] is not None else 0.0,
            "amount_change": float(row[4]) if row[4] is not None else 0.0,
            "change_rate": float(row[5]) if row[5] is not None else 0.0
        }
        for row in results
    ]

def get_month_top_decreased_sales_volume(db, current_month=None, previous_month=None, limit=10):
    """获取月度环比销量下降Top10"""
    if not current_month or not previous_month:
        # 获取所有月份并按降序排列
        all_months = db.query(SalesData.month).distinct().order_by(SalesData.month.desc()).all()
        months = [m[0] for m in all_months if m[0]]
        
        if len(months) >= 2:
            current_month = months[0]
            previous_month = months[1]
        else:
            return []  # 没有足够的月份数据进行比较
    
    query = """
    SELECT 
        t1.sku,
        t1.product_name,
        t1.current_volume,
        t2.previous_volume,
        (t2.previous_volume - t1.current_volume) AS volume_decrease,
        CASE 
            WHEN t2.previous_volume > 0 THEN 
                ((t1.current_volume - t2.previous_volume) / t2.previous_volume) * 100
            ELSE 0
        END AS change_rate
    FROM 
        (SELECT 
            sku, 
            product_name, 
            SUM(sales_volume) AS current_volume
         FROM 
            sales_data
         WHERE 
            month = :current_month
         GROUP BY 
            sku, product_name) AS t1
    JOIN 
        (SELECT 
            sku, 
            product_name, 
            SUM(sales_volume) AS previous_volume
         FROM 
            sales_data
         WHERE 
            month = :previous_month
         GROUP BY 
            sku, product_name) AS t2
    ON 
        t1.sku = t2.sku
    WHERE
        t1.current_volume < t2.previous_volume
    ORDER BY 
        volume_decrease DESC
    LIMIT :limit
    """
    
    results = db.execute(text(query), {
        "current_month": current_month,
        "previous_month": previous_month,
        "limit": limit
    }).fetchall()
    
    return [
        {
            "sku": row[0],
            "product_name": row[1],
            "current_value": float(row[2]) if row[2] is not None else 0.0,
            "previous_value": float(row[3]) if row[3] is not None else 0.0,
            "amount_change": float(row[4]) if row[4] is not None else 0.0,
            "change_rate": float(row[5]) if row[5] is not None else 0.0
        }
        for row in results
    ]

def get_month_country_sales_distribution(db, current_month=None, previous_month=None):
    """获取月度国家销售额分布与环比"""
    if not current_month or not previous_month:
        # 获取所有月份并按降序排列
        all_months = db.query(SalesData.month).distinct().order_by(SalesData.month.desc()).all()
        months = [m[0] for m in all_months if m[0]]
        
        if len(months) >= 2:
            current_month = months[0]
            previous_month = months[1]
        else:
            return []  # 没有足够的月份数据进行比较
    
    # 当前月销售额
    current_query = db.query(
        SalesData.buyer_country,
        func.sum(SalesData.sales_amount).label('total_amount')
    ).filter(
        SalesData.month == current_month
    ).group_by(
        SalesData.buyer_country
    ).order_by(text('total_amount DESC')).all()
    
    # 上月销售额
    previous_query = db.query(
        SalesData.buyer_country,
        func.sum(SalesData.sales_amount).label('total_amount')
    ).filter(
        SalesData.month == previous_month
    ).group_by(
        SalesData.buyer_country
    ).all()
    
    # 转换为字典 {country: amount}
    previous_data = {row.buyer_country: float(row.total_amount) for row in previous_query if row.buyer_country}
    
    # 计算环比
    result = []
    for row in current_query:
        if not row.buyer_country:
            continue
            
        current_amount = float(row.total_amount) if row.total_amount else 0
        previous_amount = previous_data.get(row.buyer_country, 0)
        
        # 计算环比变化率
        change_rate = 0
        if previous_amount > 0:
            change_rate = (current_amount - previous_amount) / previous_amount * 100
        
        result.append({
            "country": row.buyer_country,
            "value": current_amount,
            "previous_value": previous_amount,
            "change_rate": round(change_rate, 2)
        })
    
    return result

def get_month_platform_comparison(db, current_month=None, previous_month=None):
    """获取月度平台销售数据环比"""
    if not current_month or not previous_month:
        # 获取所有月份并按降序排列
        all_months = db.query(SalesData.month).distinct().order_by(SalesData.month.desc()).all()
        months = [m[0] for m in all_months if m[0]]
        
        if len(months) >= 2:
            current_month = months[0]
            previous_month = months[1]
        else:
            return {"current": {}, "previous": {}, "platforms": []}  # 没有足够的月份数据
    
    # 当前月平台数据
    current_query = db.query(
        SalesData.platform,
        func.sum(SalesData.sales_amount).label('sales_amount'),
        func.sum(SalesData.sales_volume).label('sales_volume'),
        func.sum(SalesData.order_count).label('order_count'),
        func.sum(SalesData.profit).label('profit')
    ).filter(
        SalesData.month == current_month
    ).group_by(
        SalesData.platform
    ).all()
    
    # 上月平台数据
    previous_query = db.query(
        SalesData.platform,
        func.sum(SalesData.sales_amount).label('sales_amount'),
        func.sum(SalesData.sales_volume).label('sales_volume'),
        func.sum(SalesData.order_count).label('order_count'),
        func.sum(SalesData.profit).label('profit')
    ).filter(
        SalesData.month == previous_month
    ).group_by(
        SalesData.platform
    ).all()
    
    # 汇总当前月数据
    current_data = {}
    for row in current_query:
        if not row.platform:
            continue
            
        platform = row.platform
        sales_amount = float(row.sales_amount) if row.sales_amount else 0
        sales_volume = float(row.sales_volume) if row.sales_volume else 0
        order_count = int(row.order_count) if row.order_count else 0
        profit = float(row.profit) if row.profit else 0
        
        # 计算毛利率
        profit_rate = 0
        if sales_amount > 0:
            profit_rate = (profit / sales_amount) * 100
        
        current_data[platform] = {
            "sales_amount": sales_amount,
            "sales_volume": sales_volume,
            "order_count": order_count,
            "profit_rate": round(profit_rate, 2)
        }
    
    # 汇总上月数据
    previous_data = {}
    for row in previous_query:
        if not row.platform:
            continue
            
        platform = row.platform
        sales_amount = float(row.sales_amount) if row.sales_amount else 0
        sales_volume = float(row.sales_volume) if row.sales_volume else 0
        order_count = int(row.order_count) if row.order_count else 0
        profit = float(row.profit) if row.profit else 0
        
        # 计算毛利率
        profit_rate = 0
        if sales_amount > 0:
            profit_rate = (profit / sales_amount) * 100
        
        previous_data[platform] = {
            "sales_amount": sales_amount,
            "sales_volume": sales_volume,
            "order_count": order_count,
            "profit_rate": round(profit_rate, 2)
        }
    
    # 获取所有平台
    all_platforms = set(list(current_data.keys()) + list(previous_data.keys()))
    
    return {
        "current": current_data,
        "previous": previous_data,
        "platforms": list(all_platforms)
    }

def get_month_salesperson_comparison(db, current_month=None, previous_month=None):
    """获取月度销售人员数据环比"""
    if not current_month or not previous_month:
        # 获取所有月份并按降序排列
        all_months = db.query(SalesData.month).distinct().order_by(SalesData.month.desc()).all()
        months = [m[0] for m in all_months if m[0]]
        
        if len(months) >= 2:
            current_month = months[0]
            previous_month = months[1]
        else:
            return []  # 没有足够的月份数据
    
    # 当前月销售人员数据
    current_query = db.query(
        SalesData.sales_person,
        func.sum(SalesData.sales_amount).label('sales_amount'),
        func.sum(SalesData.sales_volume).label('sales_volume'),
        func.sum(SalesData.order_count).label('order_count'),
        func.sum(SalesData.profit).label('profit')
    ).filter(
        SalesData.month == current_month
    ).group_by(
        SalesData.sales_person
    ).all()
    
    # 上月销售人员数据
    previous_query = db.query(
        SalesData.sales_person,
        func.sum(SalesData.sales_amount).label('sales_amount'),
        func.sum(SalesData.sales_volume).label('sales_volume'),
        func.sum(SalesData.order_count).label('order_count'),
        func.sum(SalesData.profit).label('profit')
    ).filter(
        SalesData.month == previous_month
    ).group_by(
        SalesData.sales_person
    ).all()
    
    # 将上月数据转换为字典 {sales_person: data}
    previous_data = {}
    for row in previous_query:
        if not row.sales_person:
            continue
            
        sales_person = row.sales_person
        sales_amount = float(row.sales_amount) if row.sales_amount else 0
        sales_volume = float(row.sales_volume) if row.sales_volume else 0
        order_count = int(row.order_count) if row.order_count else 0
        profit = float(row.profit) if row.profit else 0
        
        # 计算毛利率
        profit_rate = 0
        if sales_amount > 0:
            profit_rate = (profit / sales_amount) * 100
        
        previous_data[sales_person] = {
            "sales_amount": sales_amount,
            "sales_volume": sales_volume,
            "order_count": order_count,
            "profit_rate": round(profit_rate, 2)
        }
    
    # 整合数据并计算环比
    result = []
    for row in current_query:
        if not row.sales_person:
            continue
            
        sales_person = row.sales_person
        current_amount = float(row.sales_amount) if row.sales_amount else 0
        current_volume = float(row.sales_volume) if row.sales_volume else 0
        current_orders = int(row.order_count) if row.order_count else 0
        current_profit = float(row.profit) if row.profit else 0
        
        # 计算当前毛利率
        current_profit_rate = 0
        if current_amount > 0:
            current_profit_rate = (current_profit / current_amount) * 100
        
        # 获取上月数据
        prev_data = previous_data.get(sales_person, {})
        previous_amount = prev_data.get("sales_amount", 0)
        previous_volume = prev_data.get("sales_volume", 0)
        previous_orders = prev_data.get("order_count", 0)
        previous_profit_rate = prev_data.get("profit_rate", 0)
        
        # 计算环比变化率
        amount_change_rate = 0
        if previous_amount > 0:
            amount_change_rate = (current_amount - previous_amount) / previous_amount * 100
            
        volume_change_rate = 0
        if previous_volume > 0:
            volume_change_rate = (current_volume - previous_volume) / previous_volume * 100
            
        orders_change_rate = 0
        if previous_orders > 0:
            orders_change_rate = (current_orders - previous_orders) / previous_orders * 100
            
        profit_rate_change = current_profit_rate - previous_profit_rate
        
        result.append({
            "sales_person": sales_person,
            "sales_amount": current_amount,
            
            "current_amount": current_amount,
            "previous_amount": previous_amount,
            "amount_change_rate": round(amount_change_rate, 2),
            
            "current_volume": current_volume,
            "previous_volume": previous_volume,
            "volume_change_rate": round(volume_change_rate, 2),
            
            "current_orders": current_orders,
            "previous_orders": previous_orders,
            "orders_change_rate": round(orders_change_rate, 2),
            
            "current_profit_rate": round(current_profit_rate, 2),
            "previous_profit_rate": round(previous_profit_rate, 2),
            "profit_rate_change": round(profit_rate_change, 2)
        })
    
    # 按销售额排序
    result.sort(key=lambda x: x["sales_amount"], reverse=True)
    
    return result

def get_available_months(db):
    """获取所有可用的月份"""
    result = db.query(SalesData.month).distinct().order_by(SalesData.month.desc()).all()
    months = [row[0] for row in result if row[0]]
    return months