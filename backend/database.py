from sqlalchemy import create_engine, func, exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import time
import pymysql

# MySQL数据库连接信息
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "your password"
DB_NAME = "sales_data"  # 默认数据库名

# 尝试连接并检查或创建数据库
def setup_database():
    try:
        # 先不指定数据库名，连接到MySQL服务器
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS
        )
        
        with connection.cursor() as cursor:
            # 检查数据库是否存在
            cursor.execute(f"SHOW DATABASES LIKE '{DB_NAME}'")
            if not cursor.fetchone():
                print(f"创建数据库 {DB_NAME}...")
                cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"数据库 {DB_NAME} 创建成功!")
            else:
                print(f"数据库 {DB_NAME} 已存在")
                
        connection.close()
        return True
    except Exception as e:
        print(f"数据库设置错误: {str(e)}")
        return False

# 如果数据库设置成功，配置SQLAlchemy引擎
if setup_database():
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
    
    # 创建带有连接池和自动重连的引擎
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # 30分钟后回收连接
        pool_pre_ping=True,  # 自动检查连接是否可用
    )
else:
    print("无法设置数据库，切换到SQLite作为备用...")
    # 备用SQLite配置
    DATABASE_URL = "sqlite:///./sales_data.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类
Base = declarative_base()

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_db_connection():
    """测试数据库连接 - 兼容 SQLAlchemy 1.x 和 2.x"""
    max_retries = 3
    retry_delay = 1  # 秒
    
    for attempt in range(max_retries):
        try:
            # 尝试连接数据库
            with engine.connect() as conn:
                # 兼容 SQLAlchemy 2.0+
                try:
                    # SQLAlchemy 2.0+ 方式
                    from sqlalchemy import text
                    result = conn.execute(text("SELECT 1"))
                    print("数据库连接测试成功! (SQLAlchemy 2.0+)")
                except (ImportError, AttributeError):
                    try:
                        # SQLAlchemy 1.4+ 方式
                        result = conn.execute("SELECT 1")
                        print("数据库连接测试成功! (SQLAlchemy 1.4+)")
                    except:
                        # 最后尝试直接查询
                        conn.scalar("SELECT 1")
                        print("数据库连接测试成功! (基本模式)")
                return True
        except Exception as e:
            print(f"数据库连接错误 (尝试 {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                print(f"正在等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避策略
            else:
                print("达到最大重试次数，数据库连接失败。")
                return False

# 在文件末尾添加
if __name__ == "__main__":
    test_db_connection() 
