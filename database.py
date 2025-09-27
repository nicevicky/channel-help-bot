from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

class Database:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    async def init_tables(self):
        """Initialize database tables"""
        try:
            # Users table
            self.supabase.table('users').select('*').limit(1).execute()
        except:
            # Create tables if they don't exist
            pass
    
    async def add_user(self, user_id: int, username: str = None, is_premium: bool = False):
        """Add or update user"""
        try:
            data = {
                'user_id': user_id,
                'username': username,
                'is_premium': is_premium,
                'created_at': 'now()'
            }
            result = self.supabase.table('users').upsert(data).execute()
            return result
        except Exception as e:
            logging.error(f"Error adding user: {e}")
            return None
    
    async def get_user(self, user_id: int):
        """Get user by ID"""
        try:
            result = self.supabase.table('users').select('*').eq('user_id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error getting user: {e}")
            return None
    
    async def upgrade_user(self, user_id: int):
        """Upgrade user to premium"""
        try:
            result = self.supabase.table('users').update({'is_premium': True}).eq('user_id', user_id).execute()
            return result
        except Exception as e:
            logging.error(f"Error upgrading user: {e}")
            return None
    
    async def add_channel(self, channel_id: int, channel_name: str, admin_id: int):
        """Add channel to database"""
        try:
            data = {
                'channel_id': channel_id,
                'channel_name': channel_name,
                'admin_id': admin_id,
                'created_at': 'now()'
            }
            result = self.supabase.table('channels').upsert(data).execute()
            return result
        except Exception as e:
            logging.error(f"Error adding channel: {e}")
            return None
    
    async def get_user_channels(self, user_id: int):
        """Get channels where user is admin"""
        try:
            result = self.supabase.table('channels').select('*').eq('admin_id', user_id).execute()
            return result.data
        except Exception as e:
            logging.error(f"Error getting channels: {e}")
            return []
    
    async def add_ad(self, title: str, description: str, media_url: str = None, button_text: str = None, button_url: str = None):
        """Add advertisement"""
        try:
            data = {
                'title': title,
                'description': description,
                'media_url': media_url,
                'button_text': button_text,
                'button_url': button_url,
                'is_active': True,
                'created_at': 'now()'
            }
            result = self.supabase.table('ads').insert(data).execute()
            return result
        except Exception as e:
            logging.error(f"Error adding ad: {e}")
            return None
    
    async def get_active_ad(self):
        """Get active advertisement"""
        try:
            result = self.supabase.table('ads').select('*').eq('is_active', True).order('created_at', desc=True).limit(1).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error getting ad: {e}")
            return None

db = Database()
