# ZSXQ飞书机器人 (Ubuntu服务器部署版)

自动抓取ZSXQ（知识星球）指定消息并发送到飞书群聊的Python脚本。

## 🌟 主要优势

- ✅ **Ubuntu服务器部署**：24/7稳定运行，响应速度快
- ✅ **自动定时检测**：北京时间8:30-22:00，每10分钟检测
- ✅ **智能消息去重**：避免重复发送，支持跨重启持久化
- ✅ **故障自动恢复**：程序异常时5秒后自动重启
- ✅ **systemd服务管理**：标准的Linux服务，易于管理
- ✅ **多组监控配置**：支持同时监控多个目标群组和用户，转发到不同的飞书机器人

## 📋 快速部署

### 1. 上传文件到Ubuntu服务器
将以下6个文件上传到 `/home/ubuntu/zsxq-bot/`：
- `main.py` - 主程序
- `requirements.txt` - Python依赖
- `.env.example` - 环境变量模板
- `.gitignore` - Git忽略文件
- `zsxq-bot.service` - systemd服务配置
- `README.md` - 本文档

### 2. 服务器环境准备
```bash
# 创建项目目录
mkdir -p /home/ubuntu/zsxq-bot
cd /home/ubuntu/zsxq-bot

# 安装Python环境
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
# 复制模板并配置
cp .env.example .env
nano .env  # 填入你的实际配置
```

### 4. 测试运行
```bash
# 单次测试
python main.py --once

# 循环测试（Ctrl+C停止）
python main.py --loop
```

### 5. 设置系统服务
```bash
# 安装服务
sudo cp zsxq-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable zsxq-bot.service
sudo systemctl start zsxq-bot.service

# 检查状态
sudo systemctl status zsxq-bot
```

## 🔧 配置说明

### 环境变量配置 (.env)

#### 单组监控配置（兼容旧版）
```bash
# ZSXQ配置
ZSXQ_COOKIES=""

# 飞书配置
FEISHU_WEBHOOK_URL=""
FEISHU_SIGN_KEY=""

# 过滤配置
TARGET_GROUP_ID=""
TARGET_USER_ID=""
```

#### 多组监控配置（新版推荐）
```bash
# ZSXQ配置（所有监控组共享）
ZSXQ_COOKIES=""

# 监控组1配置
FEISHU_WEBHOOK_URL_1=""
FEISHU_SIGN_KEY_1=""
TARGET_GROUP_ID_1=""
TARGET_USER_ID_1=""

# 监控组2配置
FEISHU_WEBHOOK_URL_2=""
FEISHU_SIGN_KEY_2=""
TARGET_GROUP_ID_2=""
TARGET_USER_ID_2=""

# 可以根据需要添加更多监控组
# FEISHU_WEBHOOK_URL_3="..."
# FEISHU_SIGN_KEY_3="..."
# TARGET_GROUP_ID_3="..."
# TARGET_USER_ID_3="..."
```

### 配置说明

- **ZSXQ_COOKIES**：知识星球的登录凭证，所有监控组共享
- **FEISHU_WEBHOOK_URL_{n}**：第n个飞书机器人的Webhook URL
- **FEISHU_SIGN_KEY_{n}**：第n个飞书机器人的签名密钥
- **TARGET_GROUP_ID_{n}**：第n个监控组的目标群组ID
- **TARGET_USER_ID_{n}**：第n个监控组的目标用户ID

### 多组监控的优势

- **独立配置**：每组监控可以有不同的目标群组、用户和飞书机器人
- **独立去重**：每组监控有独立的消息去重文件，避免交叉影响
- **灵活扩展**：可以根据需要添加任意多个监控组
- **统一管理**：所有监控组在一个程序中运行，便于管理和维护

## 🎮 运行管理

### 命令行运行
```bash
# 单次运行（测试用）
python main.py --once

# 循环运行（生产用）
python main.py --loop
```

### 系统服务管理
```bash
# 服务控制
sudo systemctl start zsxq-bot      # 启动
sudo systemctl stop zsxq-bot       # 停止
sudo systemctl restart zsxq-bot     # 重启
sudo systemctl status zsxq-bot      # 状态

# 日志查看
sudo journalctl -u zsxq-bot -f     # 实时日志
sudo journalctl -u zsxq-bot -n 100 # 最近100行
```

## 📊 监控和维护

### 日志分析
```bash
# 查看实时日志
sudo journalctl -u zsxq-bot -f

# 统计成功发送次数
sudo journalctl -u zsxq-bot | grep "消息发送到飞书成功" | wc -l

# 统计错误次数
sudo journalctl -u zsxq-bot | grep "失败|错误" | wc -l

# 查看今天的日志
sudo journalctl -u zsxq-bot --since today
```

### 状态检查
```bash
# 服务状态
sudo systemctl status zsxq-bot

# 资源使用
htop
free -h
df -h
```

## 🚨 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   # 检查文件和权限
   ls -la /home/ubuntu/zsxq-bot/
   sudo chown -R ubuntu:ubuntu /home/ubuntu/zsxq-bot/
   
   # 手动测试
   source venv/bin/activate
   python main.py --once
   ```

2. **cookies失效**
   - 重新获取ZSXQ cookies
   - 更新 `.env` 中的 `ZSXQ_COOKIES`

3. **飞书发送失败**
   - 检查 `FEISHU_WEBHOOK_URL` 和 `FEISHU_SIGN_KEY`
   - 重新配置飞书机器人

4. **没有找到消息**
   - 检查目标群组ID和用户ID
   - 确认今天有符合条件的消息
   - 测试ZSXQ API连接

## 🔄 工作原理

### 定时检测机制
- **频率**：每10分钟检查一次
- **工作时间**：北京时间 8:30-22:00
- **自动重启**：异常时5秒后自动恢复

### 去重持久化
- **稳定标识**：MD5哈希生成消息唯一ID
- **按天存储**：每日独立的消息记录
- **自动清理**：7天后自动删除旧记录

### 故障恢复
- **自动重启**：程序崩溃自动恢复
- **错误处理**：网络和API异常处理
- **状态检查**：启动前验证配置

## 💾 备份和维护

### 配置备份
```bash
# 备份配置文件
cp .env .env.backup.$(date +%Y%m%d)
cp sent_messages.json sent_messages.json.backup.$(date +%Y%m%d)

# 备份整个项目
tar -czf zsxq-bot-backup-$(date +%Y%m%d).tar.gz .
```

### 定期维护
```bash
# 清理日志（保留30天）
sudo journalctl --vacuum-time=30d

# 检查磁盘空间
df -h

# 更新系统（可选）
sudo apt update && sudo apt upgrade -y
```

## 🔒 安全建议

- 🔐 定期更新ZSXQ cookies
- 🔐 使用SSH密钥登录服务器
- 🔐 定期备份数据和配置
- 🔐 监控异常访问和日志
- 🔐 及时更新系统补丁

## 📂 文件说明

- `main.py` - 主程序（支持环境变量和配置文件）
- `requirements.txt` - Python依赖包
- `.env.example` - 环境变量配置模板
- `.gitignore` - Git忽略文件
- `zsxq-bot.service` - systemd服务配置
- `README.md` - 项目文档

## 📝 版本信息

### v3.0 (多组监控版)
- ✅ 多组监控配置支持
- ✅ 独立的消息去重机制
- ✅ 灵活的监控组扩展
- ✅ Ubuntu服务器部署支持
- ✅ systemd服务管理
- ✅ 自动重启机制
- ✅ 环境变量配置
- ✅ 详细的日志和监控

### v2.0 (Ubuntu服务器版)
- ✅ Ubuntu服务器部署支持
- ✅ systemd服务管理
- ✅ 自动重启机制
- ✅ 环境变量配置
- ✅ 详细的日志和监控

## 📄 许可证

MIT License