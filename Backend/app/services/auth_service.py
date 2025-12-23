from datetime import datetime
import logging
from app.database import execute_sql, fetch_one

def log_user_action(user_id, action_class, quantity, remain):
    """Log user action"""
    try:
        sql = """
        INSERT INTO user_log (user_id, time, class, quantity, remain)
        VALUES (%s, %s, %s, %s, %s)
        """
        execute_sql(sql, (user_id, datetime.now(), action_class, quantity, remain))
    except Exception as e:
        logging.error(f"Failed to log user action: {e}")

def log_admin_action(admin_id, log_message):
    """Log admin action"""
    try:
        sql = """
        INSERT INTO admin_log (user_id, time, log)
        VALUES (%s, %s, %s)
        """
        execute_sql(sql, (admin_id, datetime.now(), log_message))
    except Exception as e:
        logging.error(f"Failed to log admin action: {e}")

def update_user_limit(user_id, limit_type, delta):
    """Update user limit"""
    try:
        user = fetch_one("SELECT * FROM user WHERE id = %s", (user_id,))
        if not user:
            return False, "用户不存在"
        
        current_limit = user[limit_type]
        if current_limit == -1:
            return True, current_limit
        
        if current_limit + delta < 0:
            return False, "余量不足"
        
        new_limit = current_limit + delta
        sql = f"UPDATE user SET {limit_type} = %s WHERE id = %s"
        execute_sql(sql, (new_limit, user_id))
        
        return True, new_limit
    except Exception as e:
        logging.error(f"Failed to update user limit: {e}")
        return False, str(e)
