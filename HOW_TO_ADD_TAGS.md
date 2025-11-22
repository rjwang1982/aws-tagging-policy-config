# 如何添加新的必需标签

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com

## 📋 添加新标签的步骤

假设要添加第 4 个必需标签 `environment`（环境标识）

### 1. 更新配置文件

编辑 `tags-config.json`，添加新标签：

```json
{
  "requiredTags": [
    {
      "key": "siteName",
      "description": "站点名称",
      "examples": ["production", "staging", "development"]
    },
    {
      "key": "businessCostType",
      "description": "业务成本类型",
      "examples": ["compute", "storage", "network", "database"]
    },
    {
      "key": "platform",
      "description": "平台标识",
      "examples": ["web", "api", "data", "ml"]
    },
    {
      "key": "environment",
      "description": "环境标识",
      "examples": ["prod", "staging", "dev", "test"]
    }
  ]
}
```

### 2. 更新 Config 规则配置

#### 方法 A: 修改 config-rule.json（计费资源）

```json
{
  "ConfigRuleName": "required-tags-rule",
  "Description": "检查会产生费用的资源是否包含必需的标签：siteName, businessCostType, platform, environment",
  "Source": {
    "Owner": "AWS",
    "SourceIdentifier": "REQUIRED_TAGS"
  },
  "InputParameters": "{\"tag1Key\":\"siteName\",\"tag2Key\":\"businessCostType\",\"tag3Key\":\"platform\",\"tag4Key\":\"environment\"}",
  "Scope": {
    "ComplianceResourceTypes": [
      ...
    ]
  },
  "ConfigRuleState": "ACTIVE"
}
```

#### 方法 B: 修改 config-rule-all-resources.json（所有资源）

```json
{
  "ConfigRuleName": "required-tags-rule",
  "Description": "检查所有资源是否包含必需的标签：siteName, businessCostType, platform, environment",
  "Source": {
    "Owner": "AWS",
    "SourceIdentifier": "REQUIRED_TAGS"
  },
  "InputParameters": "{\"tag1Key\":\"siteName\",\"tag2Key\":\"businessCostType\",\"tag3Key\":\"platform\",\"tag4Key\":\"environment\"}",
  "ConfigRuleState": "ACTIVE"
}
```

**注意**: AWS Config 的 REQUIRED_TAGS 规则最多支持 6 个标签（tag1Key 到 tag6Key）

### 3. 更新自动打标签脚本

编辑 `auto-tag-resources.py`，修改两处：

#### 3.1 更新必需标签字典

```python
# 必需的标签
self.required_tags = {
    'siteName': '',
    'businessCostType': '',
    'platform': '',
    'environment': ''  # 新增
}
```

#### 3.2 更新交互式输入

```python
def get_tag_values(self) -> Dict[str, str]:
    """交互式获取标签值"""
    print("\n请输入标签值（留空使用默认值）:")
    print("-" * 80)
    
    tags = {}
    
    # siteName
    site_name = input("siteName (站点名称，如: production/staging/development): ").strip()
    if not site_name:
        print("  ✗ siteName 不能为空")
        return None
    tags['siteName'] = site_name
    
    # businessCostType
    cost_type = input("businessCostType (成本类型，如: compute/storage/network): ").strip()
    if not cost_type:
        print("  ✗ businessCostType 不能为空")
        return None
    tags['businessCostType'] = cost_type
    
    # platform
    platform = input("platform (平台标识，如: web/api/data): ").strip()
    if not platform:
        print("  ✗ platform 不能为空")
        return None
    tags['platform'] = platform
    
    # environment (新增)
    environment = input("environment (环境标识，如: prod/staging/dev): ").strip()
    if not environment:
        print("  ✗ environment 不能为空")
        return None
    tags['environment'] = environment
    
    return tags
```

### 4. 重新部署规则

```bash
# 删除旧规则
./manage-rule.sh delete

# 部署新规则
./manage-rule.sh deploy

# 触发评估
aws --profile susermt configservice start-config-rules-evaluation \
  --config-rule-names required-tags-rule \
  --region cn-northwest-1
```

### 5. 测试

```bash
# 查看合规性状态
./manage-rule.sh status

# 使用自动打标签脚本
python3 auto-tag-resources.py susermt cn-northwest-1
```

## 📝 完整示例

### 添加 2 个新标签：environment 和 owner

#### 1. 更新 config-rule.json

```json
{
  "InputParameters": "{\"tag1Key\":\"siteName\",\"tag2Key\":\"businessCostType\",\"tag3Key\":\"platform\",\"tag4Key\":\"environment\",\"tag5Key\":\"owner\"}"
}
```

#### 2. 更新 auto-tag-resources.py

```python
self.required_tags = {
    'siteName': '',
    'businessCostType': '',
    'platform': '',
    'environment': '',
    'owner': ''
}

# 在 get_tag_values() 中添加
environment = input("environment (环境，如: prod/dev): ").strip()
if not environment:
    return None
tags['environment'] = environment

owner = input("owner (负责人，如: team-name): ").strip()
if not owner:
    return None
tags['owner'] = owner
```

## ⚠️ 注意事项

1. **标签数量限制**: AWS Config REQUIRED_TAGS 规则最多支持 6 个标签
2. **命名规范**: 标签键建议使用驼峰命名（camelCase）
3. **向后兼容**: 添加新标签后，现有资源会变为不合规
4. **批量更新**: 使用 `auto-tag-resources.py` 批量为现有资源添加新标签
5. **重新部署**: 修改配置后必须重新部署规则才能生效

## 🔄 回滚

如果需要回滚到 3 个标签：

```bash
# 1. 恢复配置文件
git checkout config-rule.json auto-tag-resources.py

# 2. 重新部署
./manage-rule.sh delete
./manage-rule.sh deploy
```

## 📚 参考

- [AWS Config REQUIRED_TAGS 规则文档](https://docs.aws.amazon.com/config/latest/developerguide/required-tags.html)
- [AWS 标签最佳实践](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
