# 如何添加新的必需标签

**作者**: RJ.Wang  
**创建时间**: 2025-11-21  
**更新时间**: 2025-11-22

## 当前必需标签

| 标签键 | 说明 | 示例值 |
|--------|------|--------|
| `siteName` | 站点/环境名称 | production, staging, development |
| `businessCostType` | 成本类型 | compute, storage, network |
| `platform` | 平台标识 | web, api, data, infrastructure |

## 添加新标签完整步骤

假设要添加第 4 个标签 `owner`（资源所有者）

### 步骤 1: 修改 Config 规则配置

编辑 `config-rule.json`：

```json
{
  "ConfigRuleName": "required-tags-rule",
  "Description": "检查资源是否包含必需的标签：siteName, businessCostType, platform, owner",
  "Scope": {
    "ComplianceResourceTypes": [
      "AWS::EC2::Instance",
      "AWS::EC2::Volume",
      "AWS::S3::Bucket"
    ]
  },
  "Source": {
    "Owner": "AWS",
    "SourceIdentifier": "REQUIRED_TAGS"
  },
  "InputParameters": "{\"tag1Key\":\"siteName\",\"tag2Key\":\"businessCostType\",\"tag3Key\":\"platform\",\"tag4Key\":\"owner\"}"
}
```

同时修改 `config-rule-all-resources.json`（如果使用）。

### 步骤 2: 修改批量打标签脚本

#### 修改 auto-tag-batch.py

```python
def main():
    if len(sys.argv) < 7:  # 改为 7（增加 1 个参数）
        print("使用方法: python3 auto-tag-batch.py <profile> <region> <siteName> <businessCostType> <platform> <owner>")
        print("")
        print("示例:")
        print("  python3 auto-tag-batch.py c5611 cn-northwest-1 production compute web rj.wang")
        sys.exit(1)
    
    profile = sys.argv[1]
    region = sys.argv[2]
    tags = {
        'siteName': sys.argv[3],
        'businessCostType': sys.argv[4],
        'platform': sys.argv[5],
        'owner': sys.argv[6]  # 新增
    }
    
    # ... 其他代码保持不变
```

#### 修改 auto-tag-resources.py

在 `__init__()` 方法中：

```python
# 必需的标签
self.required_tags = {
    'siteName': '',
    'businessCostType': '',
    'platform': '',
    'owner': ''  # 新增
}
```

在 `get_tag_values()` 方法中：

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
    
    # owner（新增）
    owner = input("owner (资源所有者，如: rj.wang/team-name): ").strip()
    if not owner:
        print("  ✗ owner 不能为空")
        return None
    tags['owner'] = owner
    
    return tags
```

### 步骤 3: 重新部署规则

```bash
# 中国区
./manage-rule.sh deploy c5611 cn-northwest-1

# Global 区
./manage-rule.sh deploy g0603 ap-southeast-1
```

### 步骤 4: 为现有资源打标签

```bash
# 使用修改后的批量打标签脚本
# 中国区
python3 auto-tag-batch.py c5611 cn-northwest-1 production compute web rj.wang

# Global 区
python3 auto-tag-batch.py g0603 ap-southeast-1 staging storage api team-ops
```

### 步骤 5: 验证

```bash
# 查看合规性
./manage-rule.sh status c5611 cn-northwest-1

# 触发重新评估
aws --profile c5611 configservice start-config-rules-evaluation \
  --config-rule-names required-tags-rule

# 等待 2-5 分钟后再次查看
./manage-rule.sh status c5611 cn-northwest-1
```

## 限制和注意事项

### AWS Config 限制
- `REQUIRED_TAGS` 规则最多支持 **6 个标签**（tag1Key 到 tag6Key）
- 标签键区分大小写
- 标签键长度：最多 128 个字符
- 标签值长度：最多 256 个字符

### 资源标签限制
- 每个资源最多 50 个标签
- 不能使用 `aws:` 前缀（系统保留）
- 某些资源类型有特殊限制

### 向后兼容性
- 添加新标签后，所有现有资源会变为不合规
- 需要批量为现有资源添加新标签
- 建议在非高峰时段操作

## 删除标签

如果需要删除某个必需标签：

### 1. 修改配置文件
从 `InputParameters` 中移除对应的标签键：

```json
{
  "InputParameters": "{\"tag1Key\":\"siteName\",\"tag2Key\":\"businessCostType\"}"
}
```

### 2. 修改脚本
从 `auto-tag-batch.py` 和 `auto-tag-resources.py` 中移除相关代码。

### 3. 重新部署
```bash
./manage-rule.sh deploy c5611 cn-northwest-1
```

### 4. 清理资源标签（可选）
```bash
# EC2 实例
aws --profile c5611 ec2 delete-tags \
  --resources i-xxx \
  --tags Key=oldTag

# S3 存储桶需要重新设置所有标签
aws --profile c5611 s3api put-bucket-tagging \
  --bucket my-bucket \
  --tagging 'TagSet=[
    {Key=siteName,Value=production},
    {Key=businessCostType,Value=storage}
  ]'
```

## 标签命名最佳实践

### 推荐的命名规范
- 使用驼峰命名法（camelCase）：`siteName`, `businessCostType`
- 或使用短横线（kebab-case）：`site-name`, `business-cost-type`
- 保持一致性

### 推荐的标签类型

#### 1. 技术标签
- `environment` - 环境（prod/staging/dev）
- `application` - 应用名称
- `version` - 版本号
- `component` - 组件名称

#### 2. 业务标签
- `owner` - 所有者
- `team` - 团队
- `project` - 项目
- `costCenter` - 成本中心

#### 3. 安全标签
- `compliance` - 合规要求
- `dataClassification` - 数据分类
- `backup` - 备份策略

#### 4. 自动化标签
- `managedBy` - 管理方式（terraform/manual）
- `createdBy` - 创建者
- `createdDate` - 创建日期

## 常见问题

### Q: 添加新标签后，所有资源都不合规了？
**A**: 正常现象。需要为所有资源添加新标签。使用批量打标签脚本快速修复。

### Q: 可以为不同资源类型设置不同的必需标签吗？
**A**: 不可以。`REQUIRED_TAGS` 规则对所有资源类型使用相同的标签要求。如需不同要求，需要创建多个规则。

### Q: 标签值可以为空吗？
**A**: 可以，但不推荐。建议所有标签都有有意义的值。

### Q: 如何批量修改现有资源的标签值？
**A**: 使用批量打标签脚本，它会自动合并现有标签和新标签。

## 完整示例

假设要添加 `owner` 和 `team` 两个新标签：

### 1. 修改 config-rule.json
```json
{
  "InputParameters": "{\"tag1Key\":\"siteName\",\"tag2Key\":\"businessCostType\",\"tag3Key\":\"platform\",\"tag4Key\":\"owner\",\"tag5Key\":\"team\"}"
}
```

### 2. 修改 auto-tag-batch.py
```python
if len(sys.argv) < 8:  # 5 个标签 + profile + region = 8
    print("使用方法: python3 auto-tag-batch.py <profile> <region> <siteName> <businessCostType> <platform> <owner> <team>")
    sys.exit(1)

tags = {
    'siteName': sys.argv[3],
    'businessCostType': sys.argv[4],
    'platform': sys.argv[5],
    'owner': sys.argv[6],
    'team': sys.argv[7]
}
```

### 3. 部署和使用
```bash
# 部署规则
./manage-rule.sh deploy c5611 cn-northwest-1

# 批量打标签
python3 auto-tag-batch.py c5611 cn-northwest-1 production compute web rj.wang ops-team

# 验证
./manage-rule.sh status c5611 cn-northwest-1
```

## 相关资源

- [AWS 标签最佳实践](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
- [AWS Config REQUIRED_TAGS 规则](https://docs.aws.amazon.com/config/latest/developerguide/required-tags.html)
- [AWS 资源标签限制](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html#tag-conventions)
- [标签策略示例](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_tag-policies-examples.html)
