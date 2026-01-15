# ZSXQ飞书机器人

自动抓取ZSXQ（知识星球）指定消息并发送到飞书群聊的Python脚本。

## 功能特性

- ✅ 自动抓取ZSXQ动态数据
- ✅ 智能过滤：按日期、群组ID、用户ID筛选
- ✅ 消息去重：避免重复发送相同消息
- ✅ GitHub Actions支持：云端自动运行
- ✅ 定时运行：北京时间8:30-22:00，每10分钟检测一次

## GitHub Actions 部署

### 1. Fork 此仓库
点击右上角 "Fork" 按钮将仓库复制到你的账号下。

### 2. 配置 Secrets
在你的GitHub仓库中设置以下Secrets：
- `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

需要添加的Secrets：
- `ZSXQ_COOKIES`: ZSXQ网站的完整cookies字符串
- `FEISHU_WEBHOOK_URL`: 飞书机器人的webhook地址
- `FEISHU_SIGN_KEY`: 飞书机器人的签名密钥
- `TARGET_GROUP_ID`: 目标群组ID
- `TARGET_USER_ID`: 目标用户ID

### 3. 启用 Actions
1. 进入 `Actions` 标签页
2. 如果是首次使用，点击 "I understand my workflows, go ahead and enable them"

### 4. 测试运行
可以在 `Actions` 页面手动触发工作流进行测试。

## 工作原理

### 定时任务
- **频率**: 每10分钟检查一次
- **工作时间**: 北京时间 8:30-22:00
- **非工作时间**: 跳过检测，节省资源

### 消息去重
- 使用消息内容的MD5哈希生成唯一标识
- 按天存储已发送消息记录
- 7天后自动清理旧记录

### 数据获取
- 使用完整的防爬虫cookies和headers
- 解析ZSXQ API返回的JSON数据
- 支持Unicode转义序列解码

## 文件说明

- `main.py`: 主程序
- `requirements.txt`: Python依赖包
- `README.md`: 项目说明
- `.github/workflows/zsxq-bot.yml`: GitHub Actions配置文件

## 故障排除

### 常见问题

1. **cookies失效**
   - 重新获取ZSXQ网站的cookies
   - 更新 `ZSXQ_COOKIES` secret

2. **飞书签名错误**
   - 检查 `FEISHU_SIGN_KEY` 是否正确
   - 确认飞书机器人开启了签名验证

3. **没有找到消息**
   - 检查目标群组ID和用户ID是否正确
   - 确认今天有符合条件的消息

4. **GitHub Actions运行失败**
   - 检查所有Secrets是否配置正确
   - 查看Actions日志中的具体错误信息

## 注意事项

- 请妥善保管cookies等敏感信息
- 定期检查cookies是否仍然有效
- 遵守ZSXQ的使用条款
- 建议设置监控以便及时发现异常

## 许可证

MIT License