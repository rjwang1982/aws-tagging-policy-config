# AWS 资源标签合规性检查

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com

## 需求

所有 AWS 资源必须包含以下三个标签：
- `siteName` - 站点名称
- `businessCostType` - 业务成本类型
- `platform` - 平台标识

## 实现方案

使用 AWS Config 托管规则 `REQUIRED_TAGS` 自动检查资源标签合规性。

**特性**：
- 默认只检查会产生费用的资源（30 种）
- 可选检查所有支持标签的资源（100+ 种）
- 实时检测新建资源 + 每 24 小时扫描现有资源

## 快速开始

### 1. 部署规则

```bash
# 默认：只检查计费资源（推荐）
./manage-rule.sh deploy

# 指定 profile 和 region
./manage-rule.sh deploy susermt cn-northwest-1

# 检查所有资源
./manage-rule.sh deploy susermt cn-northwest-1 config-rule-all-resources.json
```

### 2. 查看合规性

```bash
# 查看状态和合规性摘要
./manage-rule.sh status

# 指定配置
./manage-rule.sh status terraform_0603 ap-southeast-1
```

### 3. 删除规则

```bash
./manage-rule.sh delete
```

## 配置文件

- `config-rule.json` - 默认配置，只检查计费资源（EC2、RDS、S3、Lambda 等 30 种）
- `config-rule-all-resources.json` - 检查所有支持标签的资源（包括 VPC、Subnet 等基础设施）

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
./setup-config.sh susermt cn-northwest-1 my-config-bucket
```

## 自动打标签

使用 Python 脚本批量为不合规资源添加标签：

```bash
python3 auto-tag-resources.py susermt cn-northwest-1
```

**功能**：
1. 自动读取不合规资源列表
2. 显示资源详情和统计
3. 交互式输入标签值
4. 批量为资源打标签

**支持的资源类型**：
- EC2 实例和卷
- S3 存储桶
- Lambda 函数
- RDS 数据库
- DynamoDB 表
- 负载均衡器

## 添加新标签

查看 `HOW_TO_ADD_TAGS.md` 了解如何添加新的必需标签。

**快速步骤**：
1. 编辑 `config-rule.json` 添加新标签键（如 `tag4Key`）
2. 编辑 `auto-tag-resources.py` 更新标签字典和输入逻辑
3. 重新部署规则：`./manage-rule.sh delete && ./manage-rule.sh deploy`

## 文件说明

- `manage-rule.sh` - 规则管理脚本（deploy/delete/status）
- `auto-tag-resources.py` - 自动打标签脚本
- `setup-config.sh` - AWS Config 初始化脚本
- `config-rule.json` - 默认配置（计费资源）
- `config-rule-all-resources.json` - 完整配置（所有资源）
- `tags-config.json` - 标签配置文件（参考）
- `HOW_TO_ADD_TAGS.md` - 添加新标签的详细说明

## 注意事项

1. **默认参数**：profile=susermt, region=cn-northwest-1
2. **评估延迟**：新建资源通常 5-10 分钟内完成评估
3. **成本**：AWS Config 按配置项和评估次数收费
4. **权限**：需要 `config:PutConfigRule` 等权限

## 查看详细报告

访问 AWS Config 控制台：https://console.aws.amazon.com/config/
