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