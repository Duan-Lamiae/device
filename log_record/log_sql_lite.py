import sqlite3
from pathlib import Path
from datetime import datetime

import uuid

# 获取程序根目录的绝对路径
ROOT_DIR = Path(__file__).parent.parent
LOG_DIR = ROOT_DIR / "log"
log_file = LOG_DIR / "douyin_bot.db"

class LogRecordSQLite:
    def __init__(self, db_path=log_file):
        """
        初始化 LogRecordSQLite，连接到 SQLite 数据库并初始化表结构。
        
        :param db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库和表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建操作日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    serial TEXT,
                    operation_type TEXT,
                    operation_result TEXT,
                    live_account TEXT,
                    details TEXT,
                    enter_type TEXT CHECK(enter_type IN ('l', 'v')),
                    created_at TEXT
                )
            ''')
            
            # 创建直播间信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS live_room_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    serial TEXT,
                    streamer_nickname TEXT,
                    streamer_account TEXT,
                    has_liked BOOLEAN DEFAULT FALSE,
                    has_commented BOOLEAN DEFAULT FALSE,
                    has_followed BOOLEAN DEFAULT FALSE,
                    has_nointerested BOOLEAN DEFAULT FALSE,
                    is_game BOOLEAN DEFAULT FALSE,
                    created_at TEXT,
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            ''')
            
            # 创建互动统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interaction_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    serial TEXT,
                    live_account TEXT,
                    likes_count INTEGER DEFAULT 0,
                    comments_count INTEGER DEFAULT 0,
                    has_followed BOOLEAN DEFAULT FALSE,
                    has_nointerested BOOLEAN DEFAULT FALSE,
                    enter_time TEXT,
                    leave_time TEXT,
                    created_at TEXT,
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            ''')
            
            # 创建视频信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS video_data_info (
                    video_id TEXT PRIMARY KEY,
                    serial TEXT,
                    streamer_account TEXT,
                    video_title TEXT,
                    has_followed BOOLEAN DEFAULT FALSE,
                    has_liked BOOLEAN DEFAULT FALSE,
                    has_collected BOOLEAN DEFAULT FALSE,
                    comment_count INTEGER DEFAULT 0,
                    has_nointerested BOOLEAN DEFAULT FALSE,
                    is_game BOOLEAN DEFAULT FALSE,
                    created_at TEXT,
                    updated_at TEXT DEFAULT (datetime('now'))
                )
            ''')
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"初始化数据库失败: {str(e)}")
        finally:
            conn.close()
    
    def log_operation(self, serial, operation_type, operation_result, live_account, details,enter_type):
        """记录操作日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            sql = '''INSERT INTO operation_logs 
                    (serial, operation_type, operation_result, live_account, details, enter_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''' 
            values = (serial, operation_type, operation_result, live_account, details, enter_type, datetime.now().isoformat())
            
            cursor.execute(sql, values)
            conn.commit()
            print(f"操作日志记录成功: {operation_type}")
            
        except sqlite3.Error as e:
            print(f"记录操作日志失败: {str(e)}")
        finally:
            conn.close()
    
    def update_interaction_stats(self, serial, live_account, interaction_type):
        """更新互动统计"""
        try:
            conn = sqlite3.connect(self.db_path)
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
            
            # 使用created_at的日期部分来判断是否是今天的记录
            today = datetime.now().date().isoformat()
            cursor.execute('''
                SELECT id FROM interaction_stats 
                WHERE serial = ? AND live_account = ? AND date(created_at) = ?
            ''', (serial, live_account, today))
            
            result = cursor.fetchone()
            
            if result:
                if column_name in ('has_nointerested', 'has_followed'):
                    sql = f'''UPDATE interaction_stats 
                              SET {column_name} = TRUE, updated_at = ?
                              WHERE serial = ? AND live_account = ? AND date(created_at) = ?'''
                    cursor.execute(sql, (datetime.now().isoformat(), serial, live_account, today))
                else:
                    sql = f'''UPDATE interaction_stats 
                              SET {column_name} = {column_name} + 1, updated_at = ?
                              WHERE serial = ? AND live_account = ? AND date(created_at) = ?'''
                    cursor.execute(sql, (datetime.now().isoformat(), serial, live_account, today))
            else:
                if column_name == 'has_followed':
                    sql = f'''INSERT INTO interaction_stats 
                              (serial, live_account, {column_name}, created_at, updated_at)
                              VALUES (?, ?, TRUE, ?, ?)'''
                    cursor.execute(sql, (serial, live_account, datetime.now().isoformat(), datetime.now().isoformat()))
                else:
                    sql = f'''INSERT INTO interaction_stats 
                              (serial, live_account, {column_name}, created_at, updated_at)
                              VALUES (?, ?, 1, ?, ?)'''
                    cursor.execute(sql, (serial, live_account, datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"更新互动统计失败: {str(e)}")
        finally:
            conn.close()
    
    def create_live_room_record(self, serial, nickname, account):
        """创建直播间记录"""
        try:
            # 确保表存在
            self.ensure_tables_exist()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查直播间记录
            cursor.execute('''
                SELECT id FROM live_room_records 
                WHERE streamer_account = ?
            ''', (account,))
            
            result = cursor.fetchone()
            current_time = datetime.now().isoformat()
            
            # 创建或更新直播间记录
            if not result:
                cursor.execute('''
                    INSERT INTO live_room_records 
                    (serial, streamer_nickname, streamer_account, 
                     has_liked, has_commented, has_followed,
                     created_at, updated_at)
                    VALUES (?, ?, ?, FALSE, FALSE, FALSE, ?, ?)
                ''', (serial, nickname, account, current_time, current_time))
                
                record_id = cursor.lastrowid
            else:
                record_id = result[0]
                cursor.execute('''
                    UPDATE live_room_records 
                    SET has_liked = FALSE,
                        has_commented = FALSE,
                        has_followed = FALSE,
                        updated_at = ?
                    WHERE id = ?
                ''', (current_time, record_id))

            # 创建或更新互动统计记录
            today = datetime.now().date().isoformat()
            cursor.execute('''
                SELECT id FROM interaction_stats 
                WHERE serial = ? AND live_account = ? AND created_at >= date(?) AND created_at < date(?, '+1 day')
            ''', (serial, account, today, today))
            
            stats_result = cursor.fetchone()
            
            if not stats_result:
                cursor.execute('''
                    INSERT INTO interaction_stats 
                    (serial, live_account, likes_count, comments_count, 
                     has_followed, enter_time, created_at, updated_at)
                    VALUES (?, ?, 0, 0, FALSE, ?, ?, ?)
                ''', (serial, account, current_time, current_time, current_time))
            else:
                cursor.execute('''
                    UPDATE interaction_stats 
                    SET enter_time = ?,
                        leave_time = NULL,
                        updated_at = ?
                    WHERE id = ?
                ''', (current_time, current_time, stats_result[0]))
            
            conn.commit()
            return record_id
            
        except sqlite3.Error as e:
            print(f"创建直播间记录失败: {str(e)}")
            return None
        finally:
            conn.close()
    
    def update_live_room_record(self, serial, streamer_account, action_type):
        """更新直播间记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            action_field = {
                'like': 'has_liked',
                'comment': 'has_commented',
                'follow': 'has_followed',
                'nointerested': 'has_nointerested'
            }.get(action_type)
            
            if action_field:
                cursor.execute('''
                    UPDATE live_room_records 
                    SET {action_field} = TRUE,
                        updated_at = ?
                    WHERE serial = ? AND streamer_account = ?
                '''.format(action_field=action_field), 
                (datetime.now().isoformat(), serial, streamer_account))
                
                conn.commit()
            
        except sqlite3.Error as e:
            print(f"更新直播间记录失败: {str(e)}")
        finally:
            conn.close()
    
    def close_live_room_record(self, serial, account):
        """关闭直播间记录（更新离开时间）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().date().isoformat()
            current_time = datetime.now().isoformat()
            
            # 更新互动统计表的离开时间
            cursor.execute('''
                UPDATE interaction_stats 
                SET leave_time = ?,
                    updated_at = ?
                WHERE serial = ? AND live_account = ? 
                AND created_at >= date(?) AND created_at < date(?, '+1 day')
                AND leave_time IS NULL
            ''', (current_time, current_time, serial, account, today, today))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"关闭直播间记录失败: {str(e)}")
        finally:
            conn.close()
    
    def get_latest_live_room_record(self, serial, streamer_account, nickname):
        """获取指定主播账号和昵称的最新直播间记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使cursor返回的行可以通过列名访问
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM live_room_records
                WHERE serial = ? AND streamer_account = ? AND streamer_nickname = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (serial, streamer_account, nickname))
            
            record = cursor.fetchone()
            if record:
                return dict(record)
            return None
        except sqlite3.Error as e:
            print(f"获取最新直播间记录失败: {str(e)}")
            return None
        finally:
            conn.close()
    
    def update_interaction_stats_by_counts(self, serial, live_account, likes, comments, follows, cursor):
        """根据当前流程中的点赞、评论、关注数更新互动统计表"""
        try:
            today = datetime.now().date().isoformat()
            
            cursor.execute('''
                SELECT id, likes_count, comments_count, has_followed 
                FROM interaction_stats
                WHERE serial = ? AND live_account = ? AND created_at >= date(?) AND created_at < date(?, '+1 day')
            ''', (serial, live_account, today, today))
            result = cursor.fetchone()

            if result:
                interaction_id, current_likes, current_comments, current_followed = result
                new_likes = current_likes + likes
                new_comments = current_comments + comments
                new_followed = current_followed or follows

                cursor.execute('''
                    UPDATE interaction_stats
                    SET likes_count = ?,
                        comments_count = ?,
                        has_followed = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (new_likes, new_comments, new_followed, datetime.now().isoformat(), interaction_id))
            else:
                cursor.execute('''
                    INSERT INTO interaction_stats
                    (serial, live_account, likes_count, comments_count, has_followed, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    serial,
                    live_account,
                    likes,
                    comments,
                    follows,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
        except sqlite3.Error as e:
            print(f"更新互动统计失败: {str(e)}")
            raise
    
    def update_live_room_records_by_counts(self, cursor, serial, record_id, likes, comments, follows):
        """根据当前流程中的点赞、评论、关注数更新直播间信息表"""
        try:
            has_liked = bool(likes)
            has_commented = bool(comments)
            has_followed = follows
    
            cursor.execute('''
                UPDATE live_room_records
                SET has_liked = ?,
                    has_commented = ?,
                    has_followed = ?,
                    updated_at = ?
                WHERE serial = ? AND id = ?
            ''', (has_liked, has_commented, has_followed, datetime.now().isoformat(), serial, record_id))
        except sqlite3.Error as e:
            print(f"更新直播间信息表失败: {str(e)}")
            raise
    
    def process_live_room_interactions(self, serial, streamer_account, nickname, likes, comments, follows, comment_count):
        """
        根据当前的点赞、评论、关注数更新互动统计表和直播间信息表。
        
        参数:
            serial (str): 设备或用户序列号
            streamer_account (str): 主播账号
            nickname (str): 主播昵称
            likes (int): 当前流程中的点赞数
            comments (int): 当前流程的评论数
            follows (bool): 当前流程中是否进行了关注操作
        """
        try:
            print(f"开始更新互动统计：likes={likes}, comments={comments}, follows={follows}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
    
            # 获取最新的直播间记录
            latest_record = self.get_latest_live_room_record(serial,streamer_account, nickname)
            if not latest_record:
                print(f"未找到{serial} 主播 {nickname} ({streamer_account}) 的直播间记录。")
                return
    
            record_id = latest_record['id']
    
            # 更新互动统计表
            self.update_interaction_stats_by_counts(serial, streamer_account, likes, comment_count, follows, cursor)
    
            # 更新直播间信息表
            self.update_live_room_records_by_counts(cursor, serial, record_id, likes, bool(comment_count), follows)
    
            conn.commit()
            print(f"已更新{serial} 主播 {nickname} ({streamer_account}) 的互动统计和直播间信息。")
        except sqlite3.Error as e:
            print(f"处理直播间互动失败: {str(e)}")
        finally:
            conn.close()
    
    def create_video_data_info(self, serial, streamer_account, video_title, is_game):
        """创建视频信息表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 先尝试插入新记录
            cursor.execute('''
                INSERT OR IGNORE INTO video_data_info 
                (video_id, serial, streamer_account, video_title, is_game, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), serial, streamer_account, video_title, is_game, datetime.now().isoformat()))
            
            # 如果记录已存在则更新
            cursor.execute('''
                UPDATE video_data_info
                SET video_title = ?,
                    is_game = ?,
                    updated_at = ?
                WHERE serial = ? AND streamer_account = ?
            ''', (video_title, is_game, datetime.now().isoformat(), serial, streamer_account))
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"更新视频信息表失败: {str(e)}")
        finally:
            conn.close()
    
    def ensure_tables_exist(self):
        """确保所有必需的表都存在"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查 interaction_stats 表是否存在
            cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='interaction_stats'
            ''')
            
            if not cursor.fetchone():
                # 如果表不存在，创建它
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interaction_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        serial TEXT,
                        live_account TEXT,
                        likes_count INTEGER DEFAULT 0,
                        comments_count INTEGER DEFAULT 0,
                        has_followed BOOLEAN DEFAULT FALSE,
                        has_nointerested BOOLEAN DEFAULT FALSE,
                        enter_time DATETIME,
                        leave_time DATETIME,
                        created_at DATETIME,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
            
        except sqlite3.Error as e:
            print(f"确保表存在时出错: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_all_operation_logs(self, serial, page=1, page_size=10):
        """
        获取指定设备的所有操作日志，支持分页
        
        Args:
            serial (str): 设备序列号
            page (int): 页码，从1开始
            page_size (int): 每页记录数
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使返回的结果可以通过列名访问
            cursor = conn.cursor()
            
            # 计算总记录数
            cursor.execute('''
                SELECT COUNT(*) as total
                FROM operation_logs
                WHERE serial = ?
            ''', (serial,))
            total = cursor.fetchone()['total']
            
            # 计算总页数
            total_pages = (total + page_size - 1) // page_size
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 查询指定设备的操作日志，带分页
            cursor.execute('''
                SELECT 
                    serial,
                    operation_type,
                    operation_result,
                    details,
                    created_at
                FROM operation_logs
                WHERE serial = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (serial, page_size, offset))
                
            # 获取所有记录并转换为字典列表
            logs = [dict(row) for row in cursor.fetchall()]
            
            # 返回分页信息和日志数据
            return {
                'total': total,
                'total_pages': total_pages,
                'current_page': page,
                'page_size': page_size,
                'logs': logs
            }
            
        except sqlite3.Error as e:
            print(f"获取操作日志失败: {str(e)}")
            return {
                'total': 0,
                'total_pages': 0,
                'current_page': page,
                'page_size': page_size,
                'logs': []
            }
        finally:
            if conn:
                conn.close()






# if __name__ == "__main__":
#     log_viewer = LogRecordSQLite()
#     logs = log_viewer.get_all_operation_logs("887444de", 2, 10)
#     print(logs)


