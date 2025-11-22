# AWS 资源标签合规性管理工具

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com  
**创建时间**: 2025-11-21  
**更新时间**: 2025-11-22

自动化管理 AWS 资源标签合规性的完整工具集，支持中国区和 Global 区。

## 功能特性

- ✅ 自动检测缺少必需标签的资源
- ✅ 批量为资源添加标签（交互式 + 非交互式）
- ✅ 支持 30+ 种 AWS 计费资源类型
- ✅ 完整支持中国区（cn-*）和 Global 区
- ✅ 自动识别 ARN 分区（aws-cn / aws）
- ✅ Config 记录器状态检查和管理
- ✅ 实时检测 + 定期扫描

## 必需标签

所有资源必须包含以下三个标签：

| 标签键 | 说明 | 示例值 |
|--------|------|--------|
| `siteName` | 站点/环境名称 | production, staging, development |
| `businessCostType` | 成本类型 | compute, storage, network |
| `platform` | 平台标识 | web, api, data, infrastructure |

## 支持的资源类型

### 计费资源（默认配置）
- **计算**: EC2 实例、ECS/EKS 集群、Lambda 函数、WorkSpaces
- **存储**: S3 存储桶、EBS 卷、EFS/FSx 文件系统、Backup 保管库
- **数据库**: RDS 实例/集群、DynamoDB 表、ElastiCache、Redshift、OpenSearch
- **网络**: NAT 网关、负载均衡器（ALB/NLB/CLB）、CloudFront、Global Accelerator
- **其他**: SageMaker、Kinesis、MSK、AppStream、Transfer Family

共 30+ 种资源类型

## 快速开始

### 1. 初始化 AWS Config（首次使用）

```bash
# 中国区
./setup-config.sh c5611 cn-northwest-1 my-config-bucket-cn

# Global 区
./setup-config.sh g0603 ap-southeast-1 my-config-bucket-global
```

### 2. 部署标签规则

```bash
# 中国区（默认）
./manage-rule.sh deploy

# 中国区（指定 region）
./manage-rule.sh deploy c5611 cn-northwest-1

# Global 区
./manage-rule.sh deploy g0603 ap-southeast-1
```

### 3. 批量打标签

#### 方式 A：非交互式（推荐，适合自动化）

```bash
# 中国区
python3 auto-tag-batch.py c5611 cn-northwest-1 production compute infrastructure

# Global 区
python3 auto-tag-batch.py g0603 ap-southeast-1 staging storage api

# 参数说明
# python3 auto-tag-batch.py <profile> <region> <siteName> <businessCostType> <platform>
```

#### 方式 B：交互式（需要手动输入标签值）

```bash
# 中国区
python3 auto-tag-resources.py c5611 cn-northwest-1

# Global 区
python3 auto-tag-resources.py g0603 ap-southeast-1
```

### 4. 查看合规状态

```bash
# 中国区（默认）
./manage-rule.sh status

# 中国区（指定 region）
./manage-rule.sh status c5611 cn-northwest-1

# Global 区
./manage-rule.sh status g0603 ap-southeast-1
```

## 中国区 vs Global 区

### 自动识别机制

工具会根据 region 参数自动识别区域类型：
- `cn-*` 开头 → 中国区 → 使用 `arn:aws-cn:` 前缀
- 其他 → Global 区 → 使用 `arn:aws:` 前缀

### 配置对比

| 项目 | 中国区 | Global 区 |
|------|--------|-----------|
| **Profile** | c5611 | g0603 |
| **Region** | cn-north-1, cn-northwest-1 | us-east-1, ap-southeast-1 等 |
| **ARN 前缀** | arn:aws-cn: | arn:aws: |
| **Config 服务** | config.amazonaws.com.cn | config.amazonaws.com |
| **IAM 策略** | arn:aws-cn:iam::aws:policy/... | arn:aws:iam::aws:policy/... |

### 使用示例

```bash
# 中国区完整流程
./setup-config.sh c5611 cn-northwest-1 config-bucket-cn
./manage-rule.sh deploy c5611 cn-northwest-1
python3 auto-tag-batch.py c5611 cn-northwest-1 production compute web
./manage-rule.sh status c5611 cn-northwest-1

# Global 区完整流程
./setup-config.sh g0603 ap-southeast-1 config-bucket-global
./manage-rule.sh deploy g0603 ap-southeast-1
python3 auto-tag-batch.py g0603 ap-southeast-1 staging storage api
./manage-rule.sh status g0603 ap-southeast-1
```

## 常见问题

### Q1: Config 记录器停止了怎么办？

**症状**: 新创建的资源没有被 Config 发现

**检查状态**:
```bash
aws --profile c5611 configservice describe-configuration-recorder-status
```

**解决方案**:
```bash
# 启动记录器
aws --profile c5611 configservice start-configuration-recorder \
  --configuration-recorder-name default
```

### Q2: 为什么有些资源没被扫描到？

**可能原因**:
1. Config 记录器未运行
2. 资源是在记录器停止期间创建的
3. 资源类型不在规则范围内

**解决方案**:
1. 检查并启动 Config 记录器（见 Q1）
2. 等待 2-5 分钟让 Config 发现资源
3. 手动触发重新评估（见 Q3）

### Q3: 如何触发重新评估？

```bash
# 中国区
aws --profile c5611 configservice start-config-rules-evaluation \
  --config-rule-names required-tags-rule

# Global 区
aws --profile g0603 configservice start-config-rules-evaluation \
  --config-rule-names required-tags-rule
```

**注意**: 避免频繁触发，AWS 有速率限制（LimitExceededException）

### Q4: 打标签后多久能看到合规？

通常 **2-5 分钟**。AWS Config 评估有延迟，耐心等待。

### Q5: 如何查看 Config 发现了哪些资源？

```bash
# 查看 EC2 实例
aws --profile c5611 configservice list-discovered-resources \
  --resource-type AWS::EC2::Instance

# 查看 S3 存储桶
aws --profile c5611 configservice list-discovered-resources \
  --resource-type AWS::S3::Bucket
```

### Q6: 打标签失败怎么办？

**常见错误**:
- `InvalidInstanceID.NotFound` - 资源已删除
- `InvalidVolume.NotFound` - 卷已删除
- `NoSuchBucket` - 存储桶已删除

**解决**: 这些资源会被自动跳过，不影响其他资源

## 工具说明

### setup-config.sh
**用途**: 初始化 AWS Config 服务（首次使用）

**功能**:
- 创建 S3 存储桶存储 Config 数据
- 创建 IAM 角色授权 Config 服务
- 创建并启动 Configuration Recorder
- 创建 Delivery Channel
- 自动识别中国区/Global 区

**使用**:
```bash
./setup-config.sh <profile> <region> <s3-bucket-name>
```

### manage-rule.sh
**用途**: 管理 Config 规则的生命周期

**功能**:
- `deploy` - 部署规则
- `delete` - 删除规则
- `status` - 查看规则状态和合规性

**使用**:
```bash
./manage-rule.sh <action> [profile] [region] [config-file]
```

### auto-tag-batch.py
**用途**: 非交互式批量打标签（推荐）

**特点**:
- 无需交互，适合自动化
- 支持中国区和 Global 区
- 自动识别 ARN 分区
- 显示详细进度

**使用**:
```bash
python3 auto-tag-batch.py <profile> <region> <siteName> <businessCostType> <platform>
```

### auto-tag-resources.py
**用途**: 交互式打标签工具

**特点**:
- 需要手动输入标签值
- 显示资源详情供确认
- 支持中国区和 Global 区
- 更安全（需要多次确认）

**使用**:
```bash
python3 auto-tag-resources.py <profile> <region>
```

## 手动修复不合规资源

### EC2 实例
```bash
aws --profile c5611 ec2 create-tags \
  --resources i-xxx \
  --tags Key=siteName,Value=production \
         Key=businessCostType,Value=compute \
         Key=platform,Value=web \
  --region cn-northwest-1
```

### S3 存储桶
```bash
aws --profile c5611 s3api put-bucket-tagging \
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
# 中国区
aws --profile c5611 lambda tag-resource \
  --resource arn:aws-cn:lambda:cn-northwest-1:account:function:name \
  --tags siteName=production,businessCostType=compute,platform=serverless \
  --region cn-northwest-1

# Global 区
aws --profile g0603 lambda tag-resource \
  --resource arn:aws:lambda:ap-southeast-1:account:function:name \
  --tags siteName=production,businessCostType=compute,platform=serverless \
  --region ap-southeast-1
```

## 配置文件

### config-rule.json
默认配置，检查 30+ 种计费资源类型。

### config-rule-all-resources.json
完整配置，检查 100+ 种所有可打标签的资源类型。

**使用完整配置**:
```bash
./manage-rule.sh deploy c5611 cn-northwest-1 config-rule-all-resources.json
```

## 最佳实践

### 1. 定期检查 Config 记录器状态
```bash
# 添加到 cron 或定时任务
aws --profile c5611 configservice describe-configuration-recorder-status
```

### 2. 新资源创建后自动打标签
使用 Lambda + EventBridge 监听资源创建事件，自动打标签。

### 3. 成本优化
- Config 记录器会产生费用
- 可以选择只记录计费资源
- 定期清理 S3 中的历史数据

### 4. 多区域部署
每个区域需要独立部署 Config 规则：
```bash
# 中国区 - 北京
./manage-rule.sh deploy c5611 cn-north-1

# 中国区 - 宁夏
./manage-rule.sh deploy c5611 cn-northwest-1
```

## 故障排查

### 问题：规则部署失败
```bash
# 检查 Config 是否启用
aws --profile c5611 configservice describe-configuration-recorder-status

# 如果未启用，运行初始化
./setup-config.sh c5611 cn-northwest-1 my-bucket
```

### 问题：打标签失败
```bash
# 检查 IAM 权限
aws --profile c5611 sts get-caller-identity

# 确保有以下权限：
# - ec2:CreateTags
# - s3:PutBucketTagging
# - lambda:TagResource
# - rds:AddTagsToResource
```

### 问题：评估结果不更新
```bash
# 等待 2-5 分钟
# 或手动触发评估
aws --profile c5611 configservice start-config-rules-evaluation \
  --config-rule-names required-tags-rule
```

## 相关文档

- [HOW_TO_ADD_TAGS.md](HOW_TO_ADD_TAGS.md) - 如何添加新的必需标签
- [AWS Config 文档](https://docs.aws.amazon.com/config/)
- [REQUIRED_TAGS 规则](https://docs.aws.amazon.com/config/latest/developerguide/required-tags.html)

## 许可证

MIT License

## 更新日志

### 2025-11-22
- ✅ 完整支持中国区和 Global 区
- ✅ 自动识别 ARN 分区
- ✅ 新增非交互式批量打标签工具
- ✅ 修复 Config 记录器状态检查
- ✅ 完善文档和故障排查指南

### 2025-11-21
- ✅ 初始版本发布
- ✅ 支持基本的标签合规性检查
- ✅ 交互式打标签工具
