from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import pandas as pd
import io
import models
import schemas
import database
from database import get_db
import ai_service
import os
from pydantic import BaseModel
from sqlalchemy import func, distinct
from datetime import datetime, timedelta
import asyncio

app = FastAPI(title="跨境电商销售数据分析看板")

# 设置上传目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 添加权限检查
try:
    test_file = os.path.join(UPLOAD_DIR, "test_perm.tmp")
    with open(test_file, "w") as f:
        f.write("测试权限")
    os.remove(test_file)
    print(f"上传目录 {UPLOAD_DIR} 权限正常")
except Exception as e:
    print(f"上传目录权限错误: {str(e)}")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 分析数据模型
class AnalysisRequest(BaseModel):
    top_sales_amount: Optional[List[Dict[str, Any]]] = []
    top_increased: Optional[List[Dict[str, Any]]] = []
    top_decreased: Optional[List[Dict[str, Any]]] = []
    country_distribution: Optional[List[Dict[str, Any]]] = []
    platform_comparison: Optional[Dict[str, Any]] = {}

@app.post("/upload/", response_model=schemas.UploadResponse)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传并处理Excel或CSV文件"""
    try:
        # 先保存文件到本地
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 根据文件扩展名决定如何读取文件
        if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
            df = pd.read_excel(file_path)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            os.remove(file_path)  # 删除不支持的文件
            raise HTTPException(status_code=400, detail="仅支持Excel或CSV文件")
        
        # 打印接收到的数据的前几行，帮助调试
        print(f"文件头部数据预览:\n{df.head()}")
        print(f"文件列名:{df.columns.tolist()}")
        
        # 检查必要的列是否存在
        required_columns = ['sku', 'spu', '名称', '销量', '销售额']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            os.remove(file_path)  # 清理文件
            raise HTTPException(
                status_code=400, 
                detail=f"文件缺少必要的列: {', '.join(missing_columns)}"
            )
        
        # 数据处理和清洗
        try:
            processed_df = process_data(df)
            print(f"处理后数据预览:\n{processed_df.head()}")
        except Exception as e:
            os.remove(file_path)  # 清理文件
            print(f"数据处理错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"数据处理错误: {str(e)}")
        
        # 保存数据到数据库
        try:
            rows_saved = save_to_database(processed_df, db)
            os.remove(file_path)  # 处理完成后删除文件
        except Exception as e:
            os.remove(file_path)  # 清理文件
            print(f"数据库保存错误: {str(e)}")
            raise HTTPException(status_code=500, detail=f"数据库保存错误: {str(e)}")
        
        return {"message": f"成功处理并保存{rows_saved}行数据"}
    
    except HTTPException:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        print(f"处理文件时发生未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理文件时出错: {str(e)}")

@app.get("/analysis/top-sales-volume/", response_model=List[schemas.ProductAnalysis])
def get_top_sales_volume(week: Optional[str] = None, db: Session = Depends(get_db)):
    """获取销量Top5产品"""
    try:
        result = models.get_top_sales_volume(db, week)
        return result
    except Exception as e:
        print(f"获取销量Top5时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据查询错误: {str(e)}")

@app.get("/analysis/top-sales-amount/", response_model=List[schemas.ProductAnalysis])
def get_top_sales_amount(week: Optional[str] = None, db: Session = Depends(get_db)):
    """获取销售额Top5产品"""
    try:
        result = models.get_top_sales_amount(db, week)
        return result
    except Exception as e:
        print(f"获取销售额Top5时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据查询错误: {str(e)}")

@app.get("/analysis/top-increased/", response_model=List[schemas.ComparisonAnalysis])
def get_top_increased(db: Session = Depends(get_db)):
    """获取环比销售额上升Top5"""
    result = models.get_top_increased_sales_amount(db, limit=5)
    return result

@app.get("/analysis/top-decreased/", response_model=List[schemas.ComparisonAnalysis])
def get_top_decreased(db: Session = Depends(get_db)):
    """获取环比销售额下降Top5"""
    result = models.get_top_decreased_sales_amount(db, limit=5)
    return result

@app.get("/analysis/country-distribution/", response_model=List[schemas.CountryAnalysis])
def get_country_distribution(db: Session = Depends(get_db)):
    """获取不同国家销售额占比和环比情况"""
    result = models.get_country_sales_distribution(db)
    return result

@app.get("/analysis/platform-comparison/", response_model=schemas.PlatformComparison)
def get_platform_comparison(db: Session = Depends(get_db)):
    """获取平台销售额、销量、订单、毛利率环比"""
    result = models.get_platform_comparison(db)
    return result

@app.get("/analysis/salesperson-comparison/")
def get_salesperson_comparison(db: Session = Depends(get_db), week: Optional[str] = None):
    """获取销售人员业绩数据"""
    # 查询当前周期数据
    current_query = db.query(
        models.SalesData.sales_person,
        func.sum(models.SalesData.sales_amount).label("sales_amount"),
        func.sum(models.SalesData.sales_volume).label("sales_volume"),
        func.sum(models.SalesData.order_count).label("order_count")
    )
    
    # 如果指定了特定周期，按指定周期筛选，否则使用"本周"
    if week and week != 'all':
        current_query = current_query.filter(models.SalesData.week == week)
    else:
        current_query = current_query.filter(models.SalesData.week == "本周")
    
    current_result = current_query.group_by(models.SalesData.sales_person).all()
    
    # 查询上一周期数据以计算环比
    prev_query = db.query(
        models.SalesData.sales_person,
        func.sum(models.SalesData.sales_amount).label("prev_sales_amount"),
        func.sum(models.SalesData.sales_volume).label("prev_sales_volume"),
        func.sum(models.SalesData.order_count).label("prev_order_count")
    )
    
    # 如果指定了特定周期，需要确定对应的上一周期
    if week and week != 'all':
        # 添加特定周期的上一周期计算逻辑
        prev_query = prev_query.filter(models.SalesData.week == "上周")
    else:
        prev_query = prev_query.filter(models.SalesData.week == "上周")
    
    prev_result = {r.sales_person: {
        "amount": float(r.prev_sales_amount), 
        "volume": float(r.prev_sales_volume),
        "orders": int(r.prev_order_count)
    } for r in prev_query.group_by(models.SalesData.sales_person).all()}
    
    # 格式化结果
    salesperson_data = []
    for r in current_result:
        if not r.sales_person:
            continue
            
        # 当前数据
        current_amount = float(r.sales_amount)
        current_volume = float(r.sales_volume)
        current_orders = int(r.order_count)
        
        # 获取历史数据
        prev_data = prev_result.get(r.sales_person, {})
        previous_amount = prev_data.get("amount", 0)
        previous_volume = prev_data.get("volume", 0)
        previous_orders = prev_data.get("orders", 0)
        
        # 计算变化率
        amount_change_rate = 0
        if previous_amount > 0:
            amount_change_rate = (current_amount - previous_amount) / previous_amount * 100
            
        volume_change_rate = 0
        if previous_volume > 0:
            volume_change_rate = (current_volume - previous_volume) / previous_volume * 100
            
        orders_change_rate = 0
        if previous_orders > 0:
            orders_change_rate = (current_orders - previous_orders) / previous_orders * 100
        
        # 计算客单价
        current_avg_order = 0
        if current_orders > 0:
            current_avg_order = current_amount / current_orders
            
        previous_avg_order = 0
        if previous_orders > 0:
            previous_avg_order = previous_amount / previous_orders
            
        # 利润率变化 (假设这个数据暂不可用)
        current_profit_rate = None
        previous_profit_rate = None
        profit_rate_change = None
        
        # 将数据添加到结果列表
        salesperson_data.append({
            "sales_person": r.sales_person,
            "sales_amount": current_amount,  # 为前端兼容性保留此字段
            "sales_volume": current_volume,  # 为前端兼容性保留此字段
            "order_count": current_orders,   # 为前端兼容性保留此字段
            "average_order": round(current_avg_order, 2),  # 为前端兼容性保留此字段
            "change_rate": round(amount_change_rate, 2),   # 为前端兼容性保留此字段
            
            # 添加前端表格需要的所有字段
            "current_amount": current_amount,
            "previous_amount": previous_amount,
            "amount_change_rate": round(amount_change_rate, 2),
            
            "current_volume": current_volume,
            "previous_volume": previous_volume,
            "volume_change_rate": round(volume_change_rate, 2),
            
            "current_orders": current_orders,
            "previous_orders": previous_orders,
            "orders_change_rate": round(orders_change_rate, 2),
            
            "current_profit_rate": current_profit_rate,
            "previous_profit_rate": previous_profit_rate,
            "profit_rate_change": profit_rate_change
        })
    
    # 按销售额排序
    salesperson_data.sort(key=lambda x: x["sales_amount"], reverse=True)
    
    return salesperson_data

@app.post("/ai/generate-analysis/")
async def ai_analysis(request: AnalysisRequest):
    """生成销售数据AI分析"""
    try:
        print("接收到AI分析请求，数据:", request)
        
        # 创建一个带超时的任务
        analysis_task = asyncio.create_task(
            generate_analysis_with_timeout(request)
        )
        
        try:
            # 设置60秒超时
            analysis = await asyncio.wait_for(analysis_task, timeout=180)
            return {"analysis": analysis}
        except asyncio.TimeoutError:
            # 如果超时，返回基本分析
            print("AI分析生成超时，返回基本分析")
            fallback_data = {
                "top_sales": request.top_sales_amount,
                "top_increased": request.top_increased,
                "top_decreased": request.top_decreased,
                "country_distribution": request.country_distribution,
                "platform_data": request.platform_comparison
            }
            return {"analysis": ai_service.generate_fallback_analysis(fallback_data)}
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"AI分析错误: {error_detail}")
        raise HTTPException(status_code=500, detail=f"生成AI分析失败: {str(e)}")

# 添加月度AI分析端点
@app.post("/analysis/generate-monthly-ai-analysis/")
async def monthly_ai_analysis(request: AnalysisRequest):
    """生成月度AI销售数据分析"""
    try:
        print(f"收到月度AI分析请求，数据: {request}")
        
        # 将请求数据转换为字典
        request_data = {
            "top_sales": request.top_sales_amount,
            "top_increased": request.top_increased,
            "top_decreased": request.top_decreased,
            "country_distribution": request.country_distribution,
            "platform_data": request.platform_comparison
        }
        
        # 调用AI服务生成月度分析
        analysis = ai_service.generate_monthly_analysis(request_data)
        return {"analysis": analysis}
    except Exception as e:
        print(f"生成月度AI分析时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成月度分析失败: {str(e)}")

async def generate_analysis_with_timeout(request: AnalysisRequest):
    # 将同步函数包装成异步执行
    return ai_service.generate_analysis(
        {
            "top_sales": request.top_sales_amount,
            "top_increased": request.top_increased,
            "top_decreased": request.top_decreased,
            "country_distribution": request.country_distribution,
            "platform_data": request.platform_comparison,
            "salesperson_data": getattr(request, 'salesperson_comparison', [])
        }
    )

@app.get("/analysis/platform-detail/")
def get_platform_detail(db: Session = Depends(get_db), week: Optional[str] = None):
    """获取各平台销售详情"""
    # 查询当前周期数据
    current_query = db.query(
        models.SalesData.platform,
        func.sum(models.SalesData.sales_amount).label("sales_amount"),
        func.sum(models.SalesData.sales_volume).label("sales_volume"),
        func.sum(models.SalesData.order_count).label("order_count")
    )
    
    # 如果指定了特定周期，按指定周期筛选，否则使用"本周"
    if week and week != 'all':
        # 这里可以添加逻辑来处理特定周期格式
        current_query = current_query.filter(models.SalesData.week == week)
    else:
        current_query = current_query.filter(models.SalesData.week == "本周")
    
    current_result = current_query.group_by(models.SalesData.platform).all()
    
    # 查询上一周期数据以计算环比
    prev_query = db.query(
        models.SalesData.platform,
        func.sum(models.SalesData.sales_amount).label("prev_sales_amount")
    )
    
    # 如果指定了特定周期，需要确定对应的上一周期
    # 简化处理：未指定周期时使用"上周"
    if week and week != 'all':
        # 如果是特定周期格式如"2024-W01"，可以添加逻辑计算上一周期
        # 目前简化为使用"上周"
        prev_query = prev_query.filter(models.SalesData.week == "上周")
    else:
        prev_query = prev_query.filter(models.SalesData.week == "上周")
    
    prev_result = {r.platform: float(r.prev_sales_amount) if r.prev_sales_amount else 0 for r in prev_query.group_by(models.SalesData.platform).all()}
    
    # 格式化结果
    platform_details = []
    for r in current_result:
        if not r.platform:
            continue
            
        prev_amount = prev_result.get(r.platform, 0)
        change_rate = 0
        if prev_amount > 0:
            change_rate = (float(r.sales_amount) - prev_amount) / prev_amount * 100
            
        platform_details.append({
            "platform": r.platform,
            "sales_amount": float(r.sales_amount) if r.sales_amount else 0,
            "sales_volume": float(r.sales_volume) if r.sales_volume else 0,
            "order_count": int(r.order_count) if r.order_count else 0,
            "previous_amount": prev_amount,
            "change_rate": round(change_rate, 2)
        })
    
    # 如果没有数据，返回一个空数组
    if not platform_details:
        return []
        
    # 按销售额排序
    platform_details.sort(key=lambda x: x["sales_amount"], reverse=True)
    
    return platform_details

@app.get("/analysis/platform-sales-distribution/")
def get_platform_sales_distribution(db: Session = Depends(get_db), week: Optional[str] = None):
    """获取各平台销售占比数据"""
    # 查询平台销售数据
    query = db.query(
        models.SalesData.platform,
        func.sum(models.SalesData.sales_amount).label("total_sales")
    )
    
    # 如果指定了周次，按周次筛选
    if week and week != 'all':
        query = query.filter(models.SalesData.week == week)
    else:
        # 默认使用本周数据
        query = query.filter(models.SalesData.week == "本周")
    
    result = query.group_by(models.SalesData.platform).all()
    
    # 转换为字典格式 {platform_name: sales_amount}
    platform_sales = {r.platform: float(r.total_sales) if r.total_sales else 0 for r in result if r.platform}
    
    # 如果没有数据，返回一个空字典
    if not platform_sales:
        return {}
        
    return platform_sales

@app.get("/analysis/no-orders-this-week/", response_model=List[schemas.ProductAnalysis])
def get_no_orders_this_week(db: Session = Depends(get_db)):
    """获取上周有出单但本周没有出单的SKU"""
    try:
        result = models.get_no_orders_this_week(db, limit=5)
        return result
    except Exception as e:
        print(f"获取上周有单本周无单SKU时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据查询错误: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "跨境电商销售数据分析系统 API 服务正在运行"}

# 获取可用月份列表
@app.get("/analysis/available-months/")
def get_months(db: Session = Depends(get_db)):
    """获取所有可用的月份"""
    try:
        months = models.get_available_months(db)
        return months
    except Exception as e:
        print(f"获取月份列表时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据查询错误: {str(e)}")

# 月度数据API端点
@app.get("/analysis/month-top-sales-volume/")
def get_month_top_sales_volume(month: Optional[str] = None, db: Session = Depends(get_db)):
    """获取月度销量Top10"""
    try:
        result = models.get_month_top_sales_volume(db, month=month, limit=10)
        return result
    except Exception as e:
        print(f"获取月度销量Top10时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据查询错误: {str(e)}")

@app.get("/analysis/month-top-sales-amount/")
def get_month_top_sales_amount(month: Optional[str] = None, db: Session = Depends(get_db)):
    """获取月度销售额Top10"""
    try:
        result = models.get_month_top_sales_amount(db, month=month, limit=10)
        return result
    except Exception as e:
        print(f"获取月度销售额Top10时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据查询错误: {str(e)}")

@app.get("/analysis/month-top-increased/")
def get_month_top_increased(current_month: Optional[str] = None, previous_month: Optional[str] = None, db: Session = Depends(get_db)):
    """获取月度环比销量上升Top10"""
    try:
        result = models.get_month_top_increased_sales_volume(db, current_month=current_month, previous_month=previous_month, limit=10)
        return result
    except Exception as e:
        print(f"获取月度环比销量上升Top10时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据查询错误: {str(e)}")

@app.get("/analysis/month-top-decreased/")
def get_month_top_decreased(current_month: Optional[str] = None, previous_month: Optional[str] = None, db: Session = Depends(get_db)):
    """获取月度环比销量下降Top10"""
    try:
        result = models.get_month_top_decreased_sales_volume(db, current_month=current_month, previous_month=previous_month, limit=10)
        return result
    except Exception as e:
        print(f"获取月度环比销量下降Top10时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据查询错误: {str(e)}")

@app.get("/analysis/month-country-distribution/")
def get_month_country_distribution(current_month: Optional[str] = None, previous_month: Optional[str] = None, db: Session = Depends(get_db)):
    """获取月度国家销售额分布"""
    try:
        result = models.get_month_country_sales_distribution(db, current_month=current_month, previous_month=previous_month)
        return result
    except Exception as e:
        print(f"获取月度国家销售额分布时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据查询错误: {str(e)}")

@app.get("/analysis/month-platform-comparison/")
def get_month_platform_comparison(current_month: Optional[str] = None, previous_month: Optional[str] = None, db: Session = Depends(get_db)):
    """获取月度平台销售数据环比"""
    try:
        result = models.get_month_platform_comparison(db, current_month=current_month, previous_month=previous_month)
        return result
    except Exception as e:
        print(f"获取月度平台销售数据环比时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据查询错误: {str(e)}")

@app.get("/analysis/month-salesperson-comparison/")
def get_month_salesperson_comparison(current_month: Optional[str] = None, previous_month: Optional[str] = None, db: Session = Depends(get_db)):
    """获取月度销售人员数据环比"""
    try:
        result = models.get_month_salesperson_comparison(db, current_month=current_month, previous_month=previous_month)
        return result
    except Exception as e:
        print(f"获取月度销售人员数据环比时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"数据查询错误: {str(e)}")

def process_data(df):
    """处理和清洗上传的数据"""
    # 表头映射
    column_mapping = {
        'sku': 'sku',
        'spu': 'spu',
        '名称': 'product_name',
        '店铺': 'shop',
        '站点': 'site',
        '仓库': 'warehouse',
        '销量': 'sales_volume',
        '销售额': 'sales_amount', 
        '买家国家': 'buyer_country',
        '平台': 'platform',
        '销售': 'sales_person',
        '订单数': 'order_count',
        '销售毛利额': 'profit',
        '毛利率': 'profit_rate',
        '周': 'week',
        '订单状态': 'order_status',
        '月': 'month'
    }
    
    # 重命名列
    df_renamed = df.rename(columns={original: mapped for original, mapped in column_mapping.items() if original in df.columns})
    
    # 确保所有必需的列都存在
    required_columns = ['sku', 'product_name', 'sales_volume', 'sales_amount', 'week']
    for col in required_columns:
        if col not in df_renamed.columns:
            print(f"缺少必要的列: {col}")
            raise ValueError(f"缺少必要的列: {col}")
    
    # 数据类型转换
    if 'sales_volume' in df_renamed.columns:
        df_renamed['sales_volume'] = pd.to_numeric(df_renamed['sales_volume'], errors='coerce')
    if 'sales_amount' in df_renamed.columns:
        df_renamed['sales_amount'] = pd.to_numeric(df_renamed['sales_amount'], errors='coerce')
    if 'profit' in df_renamed.columns:
        df_renamed['profit'] = pd.to_numeric(df_renamed['profit'], errors='coerce')
    if 'profit_rate' in df_renamed.columns:
        df_renamed['profit_rate'] = pd.to_numeric(df_renamed['profit_rate'], errors='coerce')
    if 'order_count' in df_renamed.columns:
        df_renamed['order_count'] = pd.to_numeric(df_renamed['order_count'], errors='coerce')
    
    # 处理空值
    df_renamed = df_renamed.fillna({
        'sales_volume': 0, 
        'sales_amount': 0, 
        'profit': 0, 
        'profit_rate': 0, 
        'order_count': 0,
        'shop': '',
        'site': '',
        'warehouse': '',
        'buyer_country': '',
        'platform': '',
        'sales_person': '',
        'order_status': '',
        'month': ''
    })
    
    # 确保字符串列不为NaN
    string_cols = ['sku', 'spu', 'product_name', 'shop', 'site', 'warehouse', 
                  'buyer_country', 'platform', 'sales_person', 'order_status', 'week', 'month']
    for col in string_cols:
        if col in df_renamed.columns:
            df_renamed[col] = df_renamed[col].fillna('').astype(str)
    
    # 检查数据类型转换后的结果
    print("数据类型转换后：")
    for col in df_renamed.columns:
        print(f"{col}: {df_renamed[col].dtype}")
    
    # 在返回前过滤掉不在模型字段中的列
    model_fields = [column.name for column in models.SalesData.__table__.columns]
    valid_columns = [col for col in df_renamed.columns if col in model_fields]
    
    # 返回只包含有效列的数据帧
    return df_renamed[valid_columns]

def save_to_database(df, db):
    """保存处理后的数据到数据库 - 使用批量插入提高性能"""
    try:
        # 首先清空现有数据
        print("清空现有数据...")
        db.query(models.SalesData).delete()
        db.commit()
        print("数据表已清空")

        # 获取模型中定义的字段列表
        model_fields = [column.name for column in models.SalesData.__table__.columns]
        print(f"模型字段: {model_fields}")
        
        # 过滤DataFrame，只保留模型中存在的列
        valid_df = df[[col for col in df.columns if col in model_fields]]
        
        # 打印前几行数据用于调试
        print(f"即将保存的数据预览(前5行):")
        print(valid_df.head())
        
        # 记录总行数
        total_rows = len(valid_df)
        
        # 批量大小 - 较大的批量可以提高性能，但不要太大以避免超时
        batch_size = 100
        
        # 批量处理
        for i in range(0, total_rows, batch_size):
            batch_df = valid_df.iloc[i:min(i+batch_size, total_rows)]
            
            # 创建批量对象
            batch_objects = []
            for _, row in batch_df.iterrows():
                data_dict = {k: v for k, v in row.to_dict().items() if k in model_fields}
                batch_objects.append(models.SalesData(**data_dict))
            
            # 批量添加到会话
            db.bulk_save_objects(batch_objects)
            
            # 每个批次都提交，避免事务过大
            db.commit()
            
            print(f"已处理 {min(i+batch_size, total_rows)}/{total_rows} 行数据")
        
        return total_rows
        
    except Exception as e:
        db.rollback()
        print(f"提交到数据库失败: {str(e)}")
        raise

def get_date_range_for_week(week: Optional[str] = None):
    """根据周次参数获取日期范围"""
    if not week or week == 'all':
        return None, None
        
    try:
        # 假设week格式为 "2023-W01" 表示2023年第1周
        if 'W' in week:
            year, week_num = week.split('-W')
            year = int(year)
            week_num = int(week_num)
            
            # 计算该周的开始日期（周一）
            start_date = datetime.strptime(f'{year}-{week_num}-1', '%Y-%W-%w')
            if start_date.year != year:
                start_date = datetime.strptime(f'{year}-{week_num}-0', '%Y-%W-%w')
                start_date += timedelta(days=1)
                
            end_date = start_date + timedelta(days=6)
            return start_date.date(), end_date.date()
        else:
            # 假设直接是日期范围 "2023-01-01_2023-01-07"
            dates = week.split('_')
            if len(dates) == 2:
                start_date = datetime.strptime(dates[0], '%Y-%m-%d').date()
                end_date = datetime.strptime(dates[1], '%Y-%m-%d').date()
                return start_date, end_date
            
    except Exception as e:
        print(f"解析日期时出错: {e}")
    
    # 默认返回最近7天
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    return start_date, end_date

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 