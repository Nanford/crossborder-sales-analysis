from models import Base, SalesData
from database import engine, test_db_connection
import time

def init_database():
    """初始化数据库表"""
    print("正在测试数据库连接...")
    
    # 尝试连接数据库
    if not test_db_connection():
        print("无法连接到数据库，请检查配置。")
        return False
    
    print("数据库连接正常，开始创建表...")
    try:
        # 创建数据表
        Base.metadata.create_all(bind=engine)
        print("数据库表创建成功！")
        return True
    except Exception as e:
        print(f"创建表时出错: {str(e)}")
        return False

if __name__ == "__main__":
    init_database() 