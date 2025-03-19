import sqlalchemy

print(f"SQLAlchemy version: {sqlalchemy.__version__}")

# 测试正确的查询方式
from sqlalchemy import create_engine, text

# 创建一个临时的 SQLite 引擎用于测试
engine = create_engine("sqlite:///:memory:")

with engine.connect() as conn:
    # 尝试不同的查询方式
    print("\n尝试不同的查询执行方式:")
    
    try:
        result = conn.execute(text("SELECT 1"))
        print("方式 1 成功: conn.execute(text('SELECT 1'))")
    except Exception as e:
        print(f"方式 1 失败: {str(e)}")
    
    try:
        result = conn.execute("SELECT 1")
        print("方式 2 成功: conn.execute('SELECT 1')")
    except Exception as e:
        print(f"方式 2 失败: {str(e)}")
    
    try:
        result = conn.scalar("SELECT 1")
        print("方式 3 成功: conn.scalar('SELECT 1')")
    except Exception as e:
        print(f"方式 3 失败: {str(e)}") 