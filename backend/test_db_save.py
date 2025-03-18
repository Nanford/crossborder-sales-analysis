import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, test_db_connection
import models
from main import process_data, save_to_database

def test_save_function():
    # 验证数据库连接
    test_db_connection()
    
    # 创建测试数据
    test_data = {
        'sku': ['TEST001', 'TEST002'],
        'spu': ['TSPU001', 'TSPU002'],
        'product_name': ['测试商品1', '测试商品2'],
        'sales_volume': [10, 20],
        'sales_amount': [1000, 2000],
        'week': ['本周', '上周']
    }
    
    df = pd.DataFrame(test_data)
    
    # 处理数据
    try:
        processed_df = process_data(df)
        print("数据处理成功")
        print(processed_df.head())
    except Exception as e:
        print(f"数据处理错误: {str(e)}")
        return
    
    # 保存数据
    db = SessionLocal()
    try:
        rows_saved = save_to_database(processed_df, db)
        print(f"成功保存 {rows_saved} 行数据")
    except Exception as e:
        print(f"数据库保存错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_save_function() 