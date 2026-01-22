import requests
import json
import time
import hashlib
import base64
import hmac
import os
from datetime import datetime, date, timedelta

# 尝试加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 手动加载.env文件
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # 移除引号
                        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        os.environ[key] = value

class ZSXQFeishuBot:
    def __init__(self):
        """优先从环境变量读取配置，回退到配置文件"""
        # 从环境变量读取基础配置
        base_config = {
            "zsxq": {
                "cookies": os.getenv('ZSXQ_COOKIES'),
                "api_url": "https://api.zsxq.com/v2/dynamics?scope=general&count=30"
            }
        }
        
        # 读取监控组配置
        self.monitor_groups = []
        group_index = 1
        
        # 尝试读取多组监控配置
        while True:
            webhook_url = os.getenv(f'FEISHU_WEBHOOK_URL_{group_index}')
            sign_key = os.getenv(f'FEISHU_SIGN_KEY_{group_index}')
            target_group_id = os.getenv(f'TARGET_GROUP_ID_{group_index}')
            target_user_id = os.getenv(f'TARGET_USER_ID_{group_index}')
            
            # 如果没有更多配置，跳出循环
            if not all([webhook_url, sign_key, target_group_id, target_user_id]):
                break
            
            # 添加监控组
            self.monitor_groups.append({
                "feishu": {
                    "webhook_url": webhook_url,
                    "sign_key": sign_key
                },
                "filter": {
                    "target_group_id": target_group_id,
                    "target_user_id": target_user_id
                },
                "sent_messages_file": f'sent_messages_group_{group_index}.json'
            })
            
            group_index += 1
        
        # 兼容旧的单组配置
        if not self.monitor_groups:
            webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
            sign_key = os.getenv('FEISHU_SIGN_KEY')
            target_group_id = os.getenv('TARGET_GROUP_ID')
            target_user_id = os.getenv('TARGET_USER_ID')
            
            if all([webhook_url, sign_key, target_group_id, target_user_id]):
                self.monitor_groups.append({
                    "feishu": {
                        "webhook_url": webhook_url,
                        "sign_key": sign_key
                    },
                    "filter": {
                        "target_group_id": target_group_id,
                        "target_user_id": target_user_id
                    },
                    "sent_messages_file": 'sent_messages.json'
                })
        
        # 如果环境变量为空，尝试从配置文件读取
        if not self.monitor_groups:
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # 检查是否有多组配置
                    if 'monitor_groups' in file_config:
                        for i, group_config in enumerate(file_config['monitor_groups'], 1):
                            if all([group_config.get('feishu', {}).get('webhook_url'),
                                    group_config.get('feishu', {}).get('sign_key'),
                                    group_config.get('filter', {}).get('target_group_id'),
                                    group_config.get('filter', {}).get('target_user_id')]):
                                group_config['sent_messages_file'] = f'sent_messages_group_{i}.json'
                                self.monitor_groups.append(group_config)
                    else:
                        # 兼容旧的单组配置格式
                        webhook_url = file_config.get('feishu', {}).get('webhook_url')
                        sign_key = file_config.get('feishu', {}).get('sign_key')
                        target_group_id = file_config.get('filter', {}).get('target_group_id')
                        target_user_id = file_config.get('filter', {}).get('target_user_id')
                        
                        if all([webhook_url, sign_key, target_group_id, target_user_id]):
                            self.monitor_groups.append({
                                "feishu": {
                                    "webhook_url": webhook_url,
                                    "sign_key": sign_key
                                },
                                "filter": {
                                    "target_group_id": target_group_id,
                                    "target_user_id": target_user_id
                                },
                                "sent_messages_file": 'sent_messages.json'
                            })
            except FileNotFoundError:
                print("警告: 配置文件不存在，请确保环境变量配置正确")
        
        # 保存基础配置
        self.base_config = base_config
        
        # 加载各监控组的已发送消息记录
        self.sent_messages = {}
        for group in self.monitor_groups:
            group_file = group['sent_messages_file']
            self.sent_messages[group_file] = {}
            try:
                if os.path.exists(group_file):
                    with open(group_file, 'r', encoding='utf-8') as f:
                        self.sent_messages[group_file] = json.load(f)
            except Exception as e:
                print(f"加载已发送消息记录失败 ({group_file}): {e}")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Cookie': self.base_config['zsxq']['cookies'],
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://zsxq.com/',
            'Accept-Encoding': 'gzip, deflate, br'
        })
    
    def get_message_id(self, msg):
        """生成稳定的消息ID"""
        # 使用MD5哈希确保稳定性
        text_hash = hashlib.md5(msg['text'].encode('utf-8')).hexdigest()[:16]
        return f"{msg['create_time']}_{msg['user_id']}_{text_hash}"
    
    def save_sent_messages(self, group_file):
        """保存已发送的消息记录"""
        try:
            with open(group_file, 'w', encoding='utf-8') as f:
                json.dump(self.sent_messages[group_file], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存已发送消息记录失败 ({group_file}): {e}")
    
    def is_message_sent(self, msg, group_file):
        """检查消息是否已经发送过"""
        msg_identifier = self.get_message_id(msg)
        today_str = date.today().strftime('%Y-%m-%d')
        
        if group_file not in self.sent_messages:
            self.sent_messages[group_file] = {}
        
        if today_str not in self.sent_messages[group_file]:
            return False
        
        return msg_identifier in self.sent_messages[group_file][today_str]
    
    def mark_message_sent(self, msg, group_file):
        """标记消息为已发送"""
        msg_identifier = self.get_message_id(msg)
        today_str = date.today().strftime('%Y-%m-%d')
        
        if group_file not in self.sent_messages:
            self.sent_messages[group_file] = {}
        
        if today_str not in self.sent_messages[group_file]:
            self.sent_messages[group_file][today_str] = []
        
        self.sent_messages[group_file][today_str].append(msg_identifier)
        self.save_sent_messages(group_file)
    
    def clean_old_messages(self):
        """清理7天前的消息记录"""
        cutoff_date = (date.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        for group_file in self.sent_messages:
            keys_to_remove = [key for key in self.sent_messages[group_file].keys() if key < cutoff_date]
            
            for key in keys_to_remove:
                del self.sent_messages[group_file][key]
            
            if keys_to_remove:
                self.save_sent_messages(group_file)
                print(f"清理了 {group_file} 中 {len(keys_to_remove)} 天前的消息记录")
    
    def is_work_time(self):
        """检查是否在工作时间 (8:00-22:00)"""
        now = datetime.now()
        current_time = now.time()
        
        # 8:00 到 22:00
        work_start = datetime.strptime('08:00', '%H:%M').time()
        work_end = datetime.strptime('22:00', '%H:%M').time()
        
        return work_start <= current_time <= work_end
    
    def fetch_zsxq_data(self):
        try:
            response = self.session.get(self.base_config['zsxq']['api_url'])
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
    
    def filter_messages(self, data, target_group_id, target_user_id, group_file):
        if not data or 'resp_data' not in data:
            return []
        
        dynamics = data['resp_data'].get('dynamics', [])
        filtered_messages = []
        
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
                    if not self.is_message_sent(msg, group_file):
                        filtered_messages.append(msg)
                    else:
                        print(f"跳过已发送的消息: {create_time}")
                        
            except Exception:
                continue
        
        return filtered_messages
    
    def generate_signature(self, timestamp, sign_key):
        string_to_sign = '{}\n{}'.format(timestamp, sign_key)
        hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(hmac_code).decode('utf-8')
        return signature
    
    def send_to_feishu(self, message, webhook_url, sign_key):
        timestamp = str(int(time.time()))
        signature = self.generate_signature(timestamp, sign_key)
        
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
                webhook_url,
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
        
        total_sent_count = 0
        
        # 为每个监控组单独执行检测和发送
        for i, group in enumerate(self.monitor_groups, 1):
            print(f"\n处理监控组 {i}...")
            print(f"目标群组: {group['filter']['target_group_id']}")
            print(f"目标用户: {group['filter']['target_user_id']}")
            
            print("过滤消息...")
            filtered_messages = self.filter_messages(
                data, 
                group['filter']['target_group_id'], 
                group['filter']['target_user_id'],
                group['sent_messages_file']
            )
            print(f"找到 {len(filtered_messages)} 条符合条件的消息")
            
            if not filtered_messages:
                print("没有找到符合条件的消息")
                continue
            
            sent_count = 0
            for j, msg in enumerate(filtered_messages, 1):
                print(f"处理第 {j} 条消息...")
                message_text = self.format_single_message(msg)
                print(f"发送第 {j} 条消息到飞书...")
                if self.send_to_feishu(
                    message_text, 
                    group['feishu']['webhook_url'], 
                    group['feishu']['sign_key']
                ):
                    self.mark_message_sent(msg, group['sent_messages_file'])
                    sent_count += 1
                
                if j < len(filtered_messages):
                    time.sleep(1)
            
            total_sent_count += sent_count
            print(f"监控组 {i} 处理完成，共发送 {sent_count} 条消息")
        
        print(f"\n本次检测完成，共发送 {total_sent_count} 条消息")
        return total_sent_count
    
    def run_loop(self):
        """主运行循环"""
        print("ZSXQ飞书机器人启动 (Ubuntu服务器版)")
        print("工作时间: 8:30-22:00")
        print("检测间隔: 10分钟")
        print("去重机制: 已启用")
        print(f"监控组数量: {len(self.monitor_groups)}")
        print("按 Ctrl+C 停止程序")
        
        # 检查是否有监控组配置
        if not self.monitor_groups:
            print("错误: 没有配置监控组，请检查.env文件中的配置")
            return
        
        # 清理旧消息记录
        self.clean_old_messages()
        
        try:
            while True:
                now = datetime.now()
                current_time_str = now.strftime('%H:%M')
                
                if self.is_work_time():
                    print(f"\n[{current_time_str}] 在工作时间内，开始检测...")
                    self.run_once()
                else:
                    print(f"[{current_time_str}] 不在工作时间内，等待下次检测...")
                
                # 等待10分钟
                print("等待10分钟...")
                time.sleep(600)  # 10分钟 = 600秒
                
        except KeyboardInterrupt:
            print("\n程序被用户中断，安全退出")
        except Exception as e:
            print(f"程序运行出错: {e}")
            print("5秒后重启...")
            time.sleep(5)
            self.run_loop()  # 自动重启

if __name__ == "__main__":
    import sys
    
    bot = ZSXQFeishuBot()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--loop':
        # 循环模式（默认用于服务器部署）
        bot.run_loop()
    elif len(sys.argv) > 1 and sys.argv[1] == '--once':
        # 单次运行模式
        bot.run_once()
    else:
        print("使用方法:")
        print("  python main.py --loop    # 循环运行（服务器部署）")
        print("  python main.py --once    # 单次运行（测试用）")
        print("  python main.py            # 显示帮助")