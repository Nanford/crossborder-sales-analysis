import pymysql
import time

def test_mysql_connection():
    """测试直接连接MySQL的不同凭据"""
    
    # 测试配置列表
    configs = [
        {"user": "root", "password": "DRsXT5ZJ6Oi55LPQ", "description": "当前配置"},
        {"user": "root", "password": "", "description": "空密码"},
        {"user": "root", "password": "root", "description": "默认密码"},
        {"user": "root", "password": "password", "description": "常用密码"}
    ]
    
    for config in configs:
        try:
            print(f"尝试连接配置: {config['description']}")
            connection = pymysql.connect(
                host='localhost',
                user=config['user'],
                password=config['password'],
                connect_timeout=5
            )
            
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            
            print(f"连接成功! MySQL版本: {version[0]}")
            
            # 检查sales_data数据库是否存在
            cursor.execute("SHOW DATABASES LIKE 'sales_data'")
            db_exists = cursor.fetchone()
            
            if db_exists:
                print("sales_data数据库已存在")
                
                # 检查sales_data表是否存在
                cursor.execute("USE sales_data")
                cursor.execute("SHOW TABLES LIKE 'sales_data'")
                table_exists = cursor.fetchone()
                
                if table_exists:
                    print("sales_data表已存在")
                    # 计算记录数
                    cursor.execute("SELECT COUNT(*) FROM sales_data")
                    count = cursor.fetchone()
                    print(f"表中有 {count[0]} 条记录")
                else:
                    print("sales_data表不存在")
            else:
                print("sales_data数据库不存在 - 需要创建")
            
            # 将成功的配置写入临时文件
            with open("working_db_config.txt", "w") as f:
                f.write(f"用户名: {config['user']}\n")
                f.write(f"密码: {config['password']}\n")
            
            connection.close()
            return config
        
        except Exception as e:
            print(f"连接失败: {str(e)}\n")
    
    print("所有配置均连接失败")
    return None

def create_database_if_needed(config):
    """如果需要，创建数据库和表"""
    if not config:
        return False
    
    try:
        # 连接MySQL服务器
        connection = pymysql.connect(
            host='localhost',
            user=config['user'],
            password=config['password'],
            connect_timeout=5
        )
        
        cursor = connection.cursor()
        
        # 检查数据库是否存在
        cursor.execute("SHOW DATABASES LIKE 'sales_data'")
        db_exists = cursor.fetchone()
        
        if not db_exists:
            print("创建 sales_data 数据库...")
            cursor.execute("CREATE DATABASE sales_data")
            print("数据库创建成功!")
        
        # 切换到sales_data数据库
        cursor.execute("USE sales_data")
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'sales_data'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("创建 sales_data 表...")
            create_table_sql = """
            CREATE TABLE sales_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sku VARCHAR(100) NOT NULL,
                spu VARCHAR(100),
                platform VARCHAR(100),
                shop VARCHAR(100),
                site VARCHAR(100),
                warehouse VARCHAR(100),
                buyer_country VARCHAR(100),
                sales_person VARCHAR(100),
                order_count INT DEFAULT 0,
                product_name VARCHAR(500) NOT NULL,
                sales_volume FLOAT DEFAULT 0,
                sales_amount FLOAT DEFAULT 0,
                cost FLOAT,
                profit FLOAT,
                profit_rate FLOAT DEFAULT 0,
                order_status VARCHAR(100),
                week VARCHAR(20) NOT NULL,
                month VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX (sku),
                INDEX (spu),
                INDEX (platform),
                INDEX (buyer_country),
                INDEX (sales_person),
                INDEX (week)
            )
            """
            cursor.execute(create_table_sql)
            print("表创建成功!")
        
        connection.close()
        return True
    
    except Exception as e:
        print(f"创建数据库/表失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试MySQL连接...")
    working_config = test_mysql_connection()
    
    if working_config:
        print(f"\n找到可用的数据库配置: user={working_config['user']}, password={working_config['password']}")
        
        # 尝试创建数据库和表
        if create_database_if_needed(working_config):
            print("\n数据库环境准备完成，可以使用以下连接字符串:")
            print(f"DATABASE_URL = \"mysql+pymysql://{working_config['user']}:{working_config['password']}@localhost/sales_data\"")
        else:
            print("\n数据库或表创建失败，请检查MySQL用户权限")
    else:
        print("\n所有测试的配置均失败，请提供正确的MySQL凭据")
        
        # 提供创建新用户的SQL命令
        print("\n您可以尝试在MySQL中创建新用户:")
        print("""
        1. 使用管理员权限登录MySQL:
           mysql -u root -p
           
        2. 创建新用户并授权:
           CREATE USER 'sales_user'@'localhost' IDENTIFIED BY 'your_password';
           GRANT ALL PRIVILEGES ON sales_data.* TO 'sales_user'@'localhost';
           FLUSH PRIVILEGES;
           
        3. 然后使用新凭据更新database.py中的连接字符串:
           DATABASE_URL = "mysql+pymysql://sales_user:your_password@localhost/sales_data"
        """) 