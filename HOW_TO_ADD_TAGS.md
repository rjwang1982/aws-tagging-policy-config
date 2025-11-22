# 添加新标签

## 步骤

假设添加第 4 个标签 `environment`

### 1. 修改配置文件

编辑 `config-rule.json`：

```json
{
  "InputParameters": "{\"tag1Key\":\"siteName\",\"tag2Key\":\"businessCostType\",\"tag3Key\":\"platform\",\"tag4Key\":\"environment\"}"
}
```

### 2. 修改 Python 脚本

编辑 `auto-tag-resources.py`：

```python
# 更新标签字典
self.required_tags = {
    'siteName': '',
    'businessCostType': '',
    'platform': '',
    'environment': ''  # 新增
}

# 在 get_tag_values() 中添加输入
environment = input("environment (环境，如: prod/dev): ").strip()
if not environment:
    return None
tags['environment'] = environment
```

### 3. 重新部署

```bash
./manage-rule.sh delete
./manage-rule.sh deploy
```

## 限制

- AWS Config REQUIRED_TAGS 规则最多支持 6 个标签（tag1Key 到 tag6Key）
- 添加新标签后，现有资源会变为不合规
- 使用 `auto-tag-resources.py` 批量更新现有资源
