import requests
import json
import time
import hashlib
import base64
import hmac
import os
from datetime import datetime, date, timedelta

class ZSXQFeishuBot:
    def __init__(self):
        """从环境变量读取配置"""
        self.config = {
            "zsxq": {
                "cookies": os.getenv('ZSXQ_COOKIES'),
                "api_url": "https://api.zsxq.com/v2/dynamics?scope=general&count=30"
            },
            "feishu": {
                "webhook_url": os.getenv('FEISHU_WEBHOOK_URL'),
                "sign_key": os.getenv('FEISHU_SIGN_KEY')
            },
            "filter": {
                "target_group_id": os.getenv('TARGET_GROUP_ID'),
                "target_user_id": os.getenv('TARGET_USER_ID')
            }
        }
        
        # 消息去重文件路径
        self.sent_messages_file = 'sent_messages.json'
        self.load_sent_messages()
        
        self.session = requests.Session()
        self.session.headers.update({
            'Cookie': self.config['zsxq']['cookies'],
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://zsxq.com/',
            'Accept-Encoding': 'gzip, deflate, br'
        })
    
    def load_sent_messages(self):
        """加载已发送的消息记录"""
        try:
            if os.path.exists(self.sent_messages_file):
                with open(self.sent_messages_file, 'r', encoding='utf-8') as f:
                    self.sent_messages = json.load(f)
            else:
                self.sent_messages = {}
        except Exception as e:
            print(f"加载已发送消息记录失败: {e}")
            self.sent_messages = {}
    
    def save_sent_messages(self):
        """保存已发送的消息记录"""
        try:
            with open(self.sent_messages_file, 'w', encoding='utf-8') as f:
                json.dump(self.sent_messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存已发送消息记录失败: {e}")
    
    def get_message_id(self, msg):
        """生成稳定的消息ID"""
        text_hash = hashlib.md5(msg['text'].encode('utf-8')).hexdigest()[:16]
        return f"{msg['create_time']}_{msg['user_id']}_{text_hash}"
    
    def is_message_sent(self, msg):
        """检查消息是否已经发送过"""
        msg_identifier = self.get_message_id(msg)
        today_str = date.today().strftime('%Y-%m-%d')
        
        if today_str not in self.sent_messages:
            return False
        
        return msg_identifier in self.sent_messages[today_str]
    
    def mark_message_sent(self, msg):
        """标记消息为已发送"""
        msg_identifier = self.get_message_id(msg)
        today_str = date.today().strftime('%Y-%m-%d')
        
        if today_str not in self.sent_messages:
            self.sent_messages[today_str] = []
        
        self.sent_messages[today_str].append(msg_identifier)
        self.save_sent_messages()
    
    def clean_old_messages(self):
        """清理7天前的消息记录"""
        cutoff_date = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        keys_to_remove = [key for key in self.sent_messages.keys() if key < cutoff_date]
        
        for key in keys_to_remove:
            del self.sent_messages[key]
        
        if keys_to_remove:
            self.save_sent_messages()
            print(f"清理了 {len(keys_to_remove)} 天前的消息记录")
    
    def fetch_zsxq_data(self):
        try:
            response = self.session.get(self.config['zsxq']['api_url'])
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求ZSXQ API失败: {e}")
            return None
    
    def decode_unicode_text(self, text):
        if not text:
            return ""
        
        # 检查是否包含Unicode转义序列
        if '\\u' in text:
            try:
                return text.encode().decode('unicode_escape')
            except:
                return text
        else:
            # 如果不是Unicode转义序列，直接返回原文本
            return text
    
    def is_today(self, time_str):
        try:
            if 'T' in time_str:
                clean_time = time_str.split('.')[0]
                create_date = datetime.fromisoformat(clean_time).date()
                return create_date == date.today()
            else:
                timestamp = int(time_str)
                create_date = datetime.fromtimestamp(timestamp).date()
                return create_date == date.today()
        except Exception:
            return False
    
    def filter_messages(self, data):
        if not data or 'resp_data' not in data:
            return []
        
        dynamics = data['resp_data'].get('dynamics', [])
        filtered_messages = []
        target_group_id = self.config['filter']['target_group_id']
        target_user_id = self.config['filter']['target_user_id']
        
        for item in dynamics:
            try:
                create_time = item.get('create_time', '')
                topic = item.get('topic', {})
                group = topic.get('group', {})
                group_id = group.get('group_id', '')
                talk = topic.get('talk', {})
                text = talk.get('text', '')
                user_id = talk.get('owner', {}).get('user_id', '') if talk.get('owner') else ''
                
                if (self.is_today(create_time) and 
                    str(group_id) == str(target_group_id) and 
                    str(user_id) == str(target_user_id)):
                    
                    decoded_text = self.decode_unicode_text(text)
                    msg = {
                        'create_time': create_time,
                        'text': decoded_text,
                        'group_id': group_id,
                        'user_id': user_id
                    }
                    
                    # 检查是否已经发送过
                    if not self.is_message_sent(msg):
                        filtered_messages.append(msg)
                    else:
                        print(f"跳过已发送的消息: {create_time}")
                        
            except Exception:
                continue
        
        return filtered_messages
    
    def generate_signature(self, timestamp):
        sign_key = self.config['feishu']['sign_key']
        string_to_sign = '{}\n{}'.format(timestamp, sign_key)
        hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(hmac_code).decode('utf-8')
        return signature
    
    def send_to_feishu(self, message):
        timestamp = str(int(time.time()))
        signature = self.generate_signature(timestamp)
        
        payload = {
            "timestamp": timestamp,
            "sign": signature,
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        
        try:
            response = requests.post(
                self.config['feishu']['webhook_url'],
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    print("消息发送到飞书成功")
                    return True
                else:
                    print(f"飞书返回错误: {result.get('msg')}")
                    return False
            else:
                print(f"HTTP错误: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"发送到飞书失败: {e}")
            return False
    
    def format_single_message(self, msg):
        if 'T' in msg['create_time']:
            clean_time = msg['create_time'].split('.')[0]
            create_time_str = datetime.fromisoformat(clean_time).strftime('%Y-%m-%d %H:%M:%S')
        else:
            create_time_str = datetime.fromtimestamp(int(msg['create_time'])).strftime('%Y-%m-%d %H:%M:%S')
        
        formatted_text = f"时间: {create_time_str}\n"
        formatted_text += f"内容: {msg['text']}"
        
        return formatted_text
    
    def run_once(self):
        """执行一次检测和发送"""
        now = datetime.now()
        current_time_str = now.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{current_time_str}] 开始抓取ZSXQ数据...")
        
        data = self.fetch_zsxq_data()
        
        if not data:
            print("获取数据失败")
            return 0
        
        print("过滤消息...")
        filtered_messages = self.filter_messages(data)
        print(f"找到 {len(filtered_messages)} 条符合条件的消息")
        
        if not filtered_messages:
            print("没有找到符合条件的消息")
            return 0
        
        sent_count = 0
        for i, msg in enumerate(filtered_messages, 1):
            print(f"处理第 {i} 条消息...")
            message_text = self.format_single_message(msg)
            print(f"发送第 {i} 条消息到飞书...")
            if self.send_to_feishu(message_text):
                self.mark_message_sent(msg)
                sent_count += 1
            
            if i < len(filtered_messages):
                time.sleep(1)
        
        print(f"本次检测完成，共发送 {sent_count} 条消息")
        return sent_count

if __name__ == "__main__":
    bot = ZSXQFeishuBot()
    bot.run_once()