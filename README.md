# ZSXQ飞书机器人

自动抓取ZSXQ（知识星球）指定消息并发送到飞书群聊的Python脚本。

## 功能特性

- ✅ 自动抓取ZSXQ动态数据
- ✅ 智能过滤：按日期、群组ID、用户ID筛选
- ✅ 消息去重：避免重复发送相同消息
- ✅ GitHub Actions支持：云端自动运行
- ✅ 定时运行：北京时间8:30-22:00，每10分钟检测一次
- ✅ 跨运行会话持久化：去重记录自动保存和恢复

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

### 3. 权限设置
**重要**：如果是私有仓库，需要给GitHub Actions写入权限：

#### 方法1：代码中配置（推荐）
已在 `.github/workflows/zsxq-bot.yml` 中配置：
```yaml
permissions:
  contents: write  # 允许写入仓库内容
```

#### 方法2：仓库设置
如果方法1不工作，可手动设置：
1. 进入仓库 `Settings` → `Actions` → `General`
2. 找到 "Workflow permissions"
3. 选择 "Read and write permissions"
4. ✅ 勾选 "Allow GitHub Actions to create and approve pull requests"

### 4. 启用 Actions
1. 进入 `Actions` 标签页
2. 如果是首次使用，点击 "I understand my workflows, go ahead and enable them"

### 5. 测试运行
可以在 `Actions` 页面手动触发工作流进行测试。

## 工作原理

### 定时任务机制
- **UTC定时触发**: 每10分钟触发一次（`*/10 * * * *`）
- **北京时间判断**: 运行时转换为北京时间（UTC+8）进行判断
- **工作时间**: 北京时间 8:30-22:00（即UTC 0:30-14:00）
- **非工作时间**: 跳过检测，节省资源

**为什么这种设计更好？**
- ✅ 简单可靠：避免复杂的跨时区cron语法
- ✅ 容易维护：调整工作时间只需修改判断逻辑
- ✅ 行业标准：大多数云服务都采用这种模式

### 消息去重机制
- **稳定标识**: 使用消息内容的MD5哈希生成唯一标识
- **按天存储**: 每天的消息记录独立管理
- **自动清理**: 7天前的旧记录自动删除
- **跨会话持久化**: 通过GitHub提交保存去重记录

### 数据获取
- 使用完整的防爬虫cookies和headers
- 解析ZSXQ API返回的JSON数据
- 支持Unicode转义序列解码

## 文件说明

- `main.py`: 主程序（支持环境变量配置）
- `requirements.txt`: Python依赖包
- `README.md`: 项目说明
- `.gitignore`: Git忽略文件
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

4. **GitHub Actions权限问题**
   ```
   remote: Write access to repository not granted.
   fatal: unable to access 'https://github.com/...'
   ```
   - 确认已按照"权限设置"步骤配置
   - 检查仓库是否为私有仓库

5. **路径匹配错误**
   ```
   fatal: pathspec 'sent_messages.json' did not match any files
   ```
   - 这是正常情况，程序会自动处理
   - 可能原因：首次运行、没有新消息或程序异常退出
   - 解决方案：已优化代码，优雅处理文件不存在的情况

6. **时区问题**
   - 确认使用的是北京时间
   - 检查Actions日志中的"当前北京时间"输出
   - 工作时间判断逻辑已在代码中正确实现

### 监控建议

- **成功日志示例**:
  ```
  当前北京时间: 09:00
  在工作时间内，执行检测
  [2026-01-15 09:00:00] 开始抓取ZSXQ数据...
  找到 1 条符合条件的消息
  消息发送到飞书成功
  本次检测完成，共发送 1 条消息
  ```

- **非工作时间日志**:
  ```
  当前北京时间: 07:00
  不在工作时间内，不执行检测
  ```

## 开发和调试

### 本地运行
```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export ZSXQ_COOKIES="your_cookies"
export FEISHU_WEBHOOK_URL="your_webhook_url"
export FEISHU_SIGN_KEY="your_sign_key"
export TARGET_GROUP_ID="your_group_id"
export TARGET_USER_ID="your_user_id"

# 运行程序
python main.py
```

### 查看详细日志
在GitHub Actions的运行页面可以查看：
- 每次运行的详细日志
- 成功/失败状态
- 消息发送统计
- 去重记录提交情况

## 安全和隐私

- ✅ 敏感信息存储在GitHub Secrets中
- ✅ 去重记录只包含消息ID，不包含敏感内容
- ✅ 建议使用Private仓库
- ✅ 定期检查cookies有效性

## 注意事项

- 请妥善保管cookies等敏感信息
- 定期检查cookies是否仍然有效
- 遵守ZSXQ的使用条款
- 建议设置监控以便及时发现异常

## 许可证

MIT License