# AWS 资源标签合规性检查

## 需求

所有 AWS 资源必须包含三个标签：`siteName`、`businessCostType`、`platform`

## 实现

使用 AWS Config 托管规则 `REQUIRED_TAGS` 自动检查资源标签合规性。

- 默认检查计费资源（30 种）
- 可选检查所有资源（100+ 种）
- 实时检测 + 每 24 小时扫描

## 快速开始

### 1. 部署规则

```bash
# 默认（中国区）
./manage-rule.sh deploy

# 中国区 - 指定 region
./manage-rule.sh deploy susermt cn-northwest-1

# Global 区
./manage-rule.sh deploy terraform_0603 ap-southeast-1

# 检查所有资源
./manage-rule.sh deploy susermt cn-northwest-1 config-rule-all-resources.json
```

### 2. 查看合规性

```bash
# 默认（中国区）
./manage-rule.sh status

# 中国区 - 指定 region
./manage-rule.sh status susermt cn-northwest-1

# Global 区
./manage-rule.sh status terraform_0603 ap-southeast-1
```

### 3. 删除规则

```bash
# 默认（中国区）
./manage-rule.sh delete

# Global 区
./manage-rule.sh delete terraform_0603 ap-southeast-1
```

## 配置

- `config-rule.json` - 默认（计费资源）
- `config-rule-all-resources.json` - 完整（所有资源）

## 修复不合规资源

### EC2 实例
```bash
aws --profile susermt ec2 create-tags \
  --resources i-xxx \
  --tags Key=siteName,Value=production \
         Key=businessCostType,Value=compute \
         Key=platform,Value=web \
  --region cn-northwest-1
```

### S3 存储桶
```bash
aws --profile susermt s3api put-bucket-tagging \
  --bucket my-bucket \
  --tagging 'TagSet=[
    {Key=siteName,Value=production},
    {Key=businessCostType,Value=storage},
    {Key=platform,Value=data}
  ]' \
  --region cn-northwest-1
```

### Lambda 函数
```bash
aws --profile susermt lambda tag-resource \
  --resource arn:aws:lambda:region:account:function:name \
  --tags siteName=production,businessCostType=compute,platform=serverless \
  --region cn-northwest-1
```

## 首次使用

如果 AWS Config 未启用，需要先初始化：

```bash
# 中国区
./setup-config.sh susermt cn-northwest-1 my-config-bucket-cn

# Global 区
./setup-config.sh terraform_0603 ap-southeast-1 my-config-bucket-global
```

## 自动打标签

```bash
# 中国区
python3 auto-tag-resources.py susermt cn-northwest-1

# Global 区
python3 auto-tag-resources.py terraform_0603 ap-southeast-1
```

支持：EC2、S3、Lambda、RDS、DynamoDB、ELB

## 添加新标签

查看 `HOW_TO_ADD_TAGS.md`

## 文件

- `manage-rule.sh` - 规则管理
- `auto-tag-resources.py` - 自动打标签
- `setup-config.sh` - 初始化（首次使用）
- `config-rule.json` - 默认配置
- `config-rule-all-resources.json` - 完整配置
- `HOW_TO_ADD_TAGS.md` - 添加新标签说明
