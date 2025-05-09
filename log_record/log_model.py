import mysql.connector
from datetime import datetime
from .base import configs
class LogRecord:
    def __init__(self):
        # MySQL连接配置
        if not configs.has_section('database_config'):
            raise ValueError("数据库配置节点 'database_config' 未找到，请检查配置文件")
        
        self.db_config = {
            'host': configs.get('database_config', 'host'),
            'user': configs.get('database_config', 'user'),
            'password': configs.get('database_config', 'password'),
            'database': configs.get('database_config', 'database'),
            'port': configs.getint('database_config', 'port')
        }
        self.init_database()
    
    def init_database(self):
        """初始化数据库和表结构"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 创建操作日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    serial VARCHAR(50),
                    operation_type VARCHAR(50),
                    operation_result VARCHAR(50),
                    live_account VARCHAR(100),
                    details TEXT,
                    enter_type CHAR(1) CHECK(enter_type IN ('l', 'v')),
                    created_at DATETIME
                )
            ''')
            
            # 创建直播间信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS live_room_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    serial VARCHAR(50),
                    streamer_nickname VARCHAR(100),
                    streamer_account VARCHAR(100),
                    has_liked BOOLEAN DEFAULT FALSE,
                    has_commented BOOLEAN DEFAULT FALSE,
                    has_followed BOOLEAN DEFAULT FALSE,
                    has_nointerested BOOLEAN DEFAULT FALSE,
                    is_game BOOLEAN DEFAULT FALSE,
                    created_at DATETIME,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建互动统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interaction_stats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    serial VARCHAR(50),
                    live_account VARCHAR(100),
                    likes_count INT DEFAULT 0,
                    comments_count INT DEFAULT 0,
                    has_followed BOOLEAN DEFAULT FALSE,
                    has_nointerested BOOLEAN DEFAULT FALSE,
                    enter_time DATETIME,
                    leave_time DATETIME,
                    created_at DATETIME,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建视频信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS video_data_info (
                    video_id VARCHAR(100) PRIMARY KEY,
                    serial VARCHAR(50),
                    streamer_account VARCHAR(100),
                    video_title TEXT,
                    has_followed BOOLEAN DEFAULT FALSE,
                    has_liked BOOLEAN DEFAULT FALSE,
                    has_collected BOOLEAN DEFAULT FALSE,
                    comment_count INT DEFAULT 0,
                    has_nointerested BOOLEAN DEFAULT FALSE,
                    is_game BOOLEAN DEFAULT FALSE,
                    created_at DATETIME,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_streamer_account (streamer_account),
                    INDEX idx_serial (serial)
                )
            ''')
            
            conn.commit()
            
        except Exception as e:
            print(f"初始化数据库失败: {str(e)}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def log_operation(self, serial, operation_type, operation_result, live_account, details):
        """记录操作日志"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 修改 SQL 语句，确保 VALUES 的占位符数量与参数数量一致
            sql = '''INSERT INTO operation_logs 
                    (serial, operation_type, operation_result, live_account, details, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)'''  # 添加了 %s 占位符
            
            # 确保参数数量与占位符一致
            values = (serial, operation_type, operation_result, live_account, details, datetime.now())
            
            cursor.execute(sql, values)
            conn.commit()
            print(f"操作日志记录成功: {operation_type}")
            
        except Exception as e:
            print(f"记录操作日志失败: {str(e)}")
            # 打印更详细的错误信息
            import traceback
            traceback.print_exc()
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def update_interaction_stats(self, serial, live_account, interaction_type):
        """更新互动统计"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            column_mapping = {
                'like': 'likes_count',
                'comment': 'comments_count',
                'follow': 'has_followed',
                'nointerested': 'has_nointerested'
            }
            
            column_name = column_mapping.get(interaction_type)
            if not column_name:
                raise ValueError(f"未知的互动类型: {interaction_type}")
            
            # 检查今天是否已有记录
            today = datetime.now().date()
            cursor.execute('''
                SELECT id FROM interaction_stats 
                WHERE serial = %s AND live_account = %s AND DATE(created_at) = %s
            ''', (serial, live_account, today))
            
            result = cursor.fetchone()
            
            if result:
                if column_name in ('has_nointerested', 'has_followed'):
                    sql = f'''UPDATE interaction_stats 
                              SET {column_name} = TRUE, updated_at = %s
                              WHERE serial = %s AND live_account = %s AND DATE(created_at) = %s'''
                    cursor.execute(sql, (datetime.now(), serial, live_account, today))
                else:
                    sql = f'''UPDATE interaction_stats 
                              SET {column_name} = {column_name} + 1, updated_at = %s
                              WHERE serial = %s AND live_account = %s AND DATE(created_at) = %s'''
                    cursor.execute(sql, (datetime.now(), serial, live_account, today))
            else:
                if column_name == 'has_followed':
                    sql = f'''INSERT INTO interaction_stats 
                              (serial, live_account, {column_name}, created_at, updated_at)
                              VALUES (%s, %s, TRUE, %s, %s)'''
                    cursor.execute(sql, (serial, live_account, datetime.now(), datetime.now()))
                else:
                    sql = f'''INSERT INTO interaction_stats 
                              (serial, live_account, {column_name}, created_at, updated_at)
                              VALUES (%s, %s, 1, %s, %s)'''
                    cursor.execute(sql, (serial, live_account, datetime.now(), datetime.now()))
            
            conn.commit()
            
        except Exception as e:
            print(f"更新互动统计失败: {str(e)}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def create_live_room_record(self, serial, nickname, account):
        """创建直播间记录"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 检查直播间记录
            cursor.execute('''
                SELECT id FROM live_room_records 
                WHERE streamer_account = %s
            ''', (account,))
            
            result = cursor.fetchone()
            current_time = datetime.now()
            
            # 创建或更新直播间记录
            if not result:
                cursor.execute('''
                    INSERT INTO live_room_records 
                    (serial, streamer_nickname, streamer_account, 
                     has_liked, has_commented, has_followed,
                     created_at, updated_at)
                    VALUES (%s, %s, %s, FALSE, FALSE, FALSE, %s, %s)
                ''', (serial, nickname, account, current_time, current_time))
                
                record_id = cursor.lastrowid
            else:
                record_id = result[0]
                cursor.execute('''
                    UPDATE live_room_records 
                    SET has_liked = FALSE,
                        has_commented = FALSE,
                        has_followed = FALSE,
                        updated_at = %s
                    WHERE id = %s
                ''', (current_time, record_id))

            # 创建或更新互动统计记录
            today = datetime.now().date()
            cursor.execute('''
                SELECT id FROM interaction_stats 
                WHERE serial = %s AND live_account = %s AND DATE(created_at) = %s
            ''', (serial, account, today))
            
            stats_result = cursor.fetchone()
            
            if not stats_result:
                cursor.execute('''
                    INSERT INTO interaction_stats 
                    (serial, live_account, likes_count, comments_count, 
                     has_followed, enter_time, created_at, updated_at)
                    VALUES (%s, %s, 0, 0, FALSE, %s, %s, %s)
                ''', (serial, account, current_time, current_time, current_time))
            else:
                cursor.execute('''
                    UPDATE interaction_stats 
                    SET enter_time = %s,
                        leave_time = NULL,
                        updated_at = %s
                    WHERE id = %s
                ''', (current_time, current_time, stats_result[0]))
            
            conn.commit()
            return record_id
            
        except Exception as e:
            print(f"创建直播间记录失败: {str(e)}")
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def update_live_room_record(self, streamer_account, action_type):
        """更新直播间互动记录"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # 更新对应的布尔字段
            action_field = {
                'like': 'has_liked',
                'comment': 'has_commented',
                'follow': 'has_followed'
            }.get(action_type)
            
            if action_field:
                if action_field == 'has_followed':
                    sql = f'''UPDATE live_room_records 
                              SET {action_field} = TRUE,
                                  updated_at = %s
                              WHERE streamer_account = %s
                              AND leave_time IS NULL'''
                    cursor.execute(sql, (datetime.now(), streamer_account))
                else:
                    sql = f'''UPDATE live_room_records 
                              SET {action_field} = TRUE,
                                  updated_at = %s
                              WHERE streamer_account = %s
                              AND leave_time IS NULL'''
                    cursor.execute(sql, (datetime.now(), streamer_account))
                
            conn.commit()
            
        except Exception as e:
            print(f"更新直播间记录失败: {str(e)}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def close_live_room_record(self, account):
        """关闭直播间记录（记录离开时间）"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE live_room_records 
                SET leave_time = %s,
                    updated_at = %s
                WHERE streamer_account = %s
                AND leave_time IS NULL
            ''', (datetime.now(), datetime.now(), account))
            
            conn.commit()
            
        except Exception as e:
            print(f"关闭直播间记录失败: {str(e)}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    def get_latest_live_room_record(self, streamer_account, nickname):
        """获取指定主播账号和昵称的最新直播间记录"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute('''
                SELECT * FROM live_room_records
                WHERE streamer_account = %s AND streamer_nickname = %s
                ORDER BY enter_time DESC
                LIMIT 1
            ''', (streamer_account, nickname))
            
            record = cursor.fetchone()
            return record
        except Exception as e:
            print(f"获取最新直播间记录失败: {str(e)}")
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def update_interaction_stats_by_counts(self, serial, live_account, likes, comments, follows, cursor):
        """根据当前流程中的点赞、评论、关注数更新互动统计表"""
        try:
            today = datetime.now().date()
            
            cursor.execute('''
                SELECT id, likes_count, comments_count, has_followed 
                FROM interaction_stats
                WHERE serial = %s AND live_account = %s AND DATE(created_at) = %s
            ''', (serial, live_account, today))
            result = cursor.fetchone()

            if result:
                interaction_id, current_likes, current_comments, current_followed = result
                new_likes = current_likes + likes
                new_comments = current_comments + comments
                new_followed = current_followed or follows

                cursor.execute('''
                    UPDATE interaction_stats
                    SET likes_count = %s,
                        comments_count = %s,
                        has_followed = %s,
                        updated_at = %s
                    WHERE id = %s
                ''', (new_likes, new_comments, new_followed, datetime.now(), interaction_id))
            else:
                cursor.execute('''
                    INSERT INTO interaction_stats
                    (serial, live_account, likes_count, comments_count, has_followed, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    serial,
                    live_account,
                    likes,
                    comments,
                    follows,
                    datetime.now(),
                    datetime.now()
                ))
        except Exception as e:
            print(f"更新互动统计表失败: {str(e)}")
            raise
    
    def update_live_room_records_by_counts(self, cursor, record_id, likes, comments, follows):
        """根据当前流程中的点赞、评论、关注数更新直播间信息表"""
        try:
            has_liked = bool(likes)
            has_commented = bool(comments)
            has_followed = follows
    
            cursor.execute('''
                UPDATE live_room_records
                SET has_liked = %s,
                    has_commented = %s,
                    has_followed = %s,
                    updated_at = %s
                WHERE id = %s
            ''', (has_liked, has_commented, has_followed, datetime.now(), record_id))
        except Exception as e:
            print(f"更新直播间信息表失败: {str(e)}")
            raise
    
    def process_live_room_interactions(self, serial, streamer_account, nickname, likes, comments, follows):
        """
        根据当前的点赞、评论、关注数更新互动统计表和直播间信息表。
        
        参数:
            serial (str): 设备或用户序列号
            streamer_account (str): 主播账号
            nickname (str): 主播昵称
            likes (int): 当前流程中的点赞数
            comments (int): 当前流程中的评论数
            follows (bool): 当前流程中是否进行了关注操作
        """
        try:
            print(f"开始更新互动统计：likes={likes}, comments={comments}, follows={follows}")
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
    
            # 获取最新的直播间记录
            latest_record = self.get_latest_live_room_record(streamer_account, nickname)
            if not latest_record:
                print(f"未找到主播 {nickname} ({streamer_account}) 的直播间记录。")
                return
    
            record_id = latest_record['id']
    
            # 更新互动统计表
            self.update_interaction_stats_by_counts(serial, streamer_account, likes, comments, follows, cursor)
    
            # 更新直播间信息表
            self.update_live_room_records_by_counts(cursor, record_id, likes, comments, follows)
    
            conn.commit()
            print(f"已更新主播 {nickname} ({streamer_account}) 的互动统计和直播间信息。")
        except Exception as e:
            print(f"处理直播间互动失败: {str(e)}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

   



