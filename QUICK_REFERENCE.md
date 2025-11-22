# AWS 标签合规性工具 - 快速参考

**作者**: RJ.Wang  
**创建时间**: 2025-11-22

## 一键命令

### 中国区

```bash
# 完整流程
./setup-config.sh c5611 cn-northwest-1 config-bucket-cn && \
./manage-rule.sh deploy c5611 cn-northwest-1 && \
python3 auto-tag-batch.py c5611 cn-northwest-1 production compute infrastructure

# 查看状态
./manage-rule.sh status c5611 cn-northwest-1

# 故障排查
./troubleshoot.sh c5611 cn-northwest-1
```

### Global 区

```bash
# 完整流程
./setup-config.sh g0603 ap-southeast-1 config-bucket-global && \
./manage-rule.sh deploy g0603 ap-southeast-1 && \
python3 auto-tag-batch.py g0603 ap-southeast-1 staging storage api

# 查看状态
./manage-rule.sh status g0603 ap-southeast-1

# 故障排查
./troubleshoot.sh g0603 ap-southeast-1
```

## 常用命令速查

### Config 记录器管理

```bash
# 检查状态
aws --profile c5611 configservice describe-configuration-recorder-status

# 启动记录器
aws --profile c5611 configservice start-configuration-recorder \
  --configuration-recorder-name default

# 停止记录器
aws --profile c5611 configservice stop-configuration-recorder \
  --configuration-recorder-name default
```

### 规则管理

```bash
# 部署规则
./manage-rule.sh deploy c5611 cn-northwest-1

# 查看状态
./manage-rule.sh status c5611 cn-northwest-1

# 删除规则
./manage-rule.sh delete c5611 cn-northwest-1

# 触发评估
aws --profile c5611 configservice start-config-rules-evaluation \
  --config-rule-names required-tags-rule
```

### 打标签

```bash
# 非交互式（推荐）
python3 auto-tag-batch.py c5611 cn-northwest-1 production compute infrastructure

# 交互式
python3 auto-tag-resources.py c5611 cn-northwest-1
```

### 查询资源

```bash
# 查看不合规资源
aws --profile c5611 configservice get-compliance-details-by-config-rule \
  --config-rule-name required-tags-rule \
  --compliance-types NON_COMPLIANT

# 查看 Config 发现的资源
aws --profile c5611 configservice list-discovered-resources \
  --resource-type AWS::EC2::Instance

# 查看实际资源
aws --profile c5611 ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key==`Name`].Value|[0]]' \
  --output table
```

### 手动打标签

```bash
# EC2 实例
aws --profile c5611 ec2 create-tags \
  --resources i-xxx \
  --tags Key=siteName,Value=production \
         Key=businessCostType,Value=compute \
         Key=platform,Value=web

# S3 存储桶
aws --profile c5611 s3api put-bucket-tagging \
  --bucket my-bucket \
  --tagging 'TagSet=[
    {Key=siteName,Value=production},
    {Key=businessCostType,Value=storage},
    {Key=platform,Value=data}
  ]'

# EBS 卷
aws --profile c5611 ec2 create-tags \
  --resources vol-xxx \
  --tags Key=siteName,Value=production \
         Key=businessCostType,Value=storage \
         Key=platform,Value=infrastructure
```

## 标签值参考

### siteName（环境）
- `production` - 生产环境
- `staging` - 预发布环境
- `development` - 开发环境
- `testing` - 测试环境
- `demo` - 演示环境

### businessCostType（成本类型）
- `compute` - 计算资源（EC2、Lambda、ECS）
- `storage` - 存储资源（S3、EBS、EFS）
- `network` - 网络资源（NAT、ALB、CloudFront）
- `database` - 数据库资源（RDS、DynamoDB）
- `analytics` - 分析资源（Kinesis、OpenSearch）

### platform（平台）
- `web` - Web 应用
- `api` - API 服务
- `data` - 数据平台
- `infrastructure` - 基础设施
- `serverless` - 无服务器应用
- `mobile` - 移动应用后端
- `iot` - 物联网平台

## 故障排查速查

### 问题：Config 记录器停止

```bash
# 检查
aws --profile c5611 configservice describe-configuration-recorder-status

# 修复
aws --profile c5611 configservice start-configuration-recorder \
  --configuration-recorder-name default
```

### 问题：资源未被发现

```bash
# 1. 检查记录器是否运行
./troubleshoot.sh c5611 cn-northwest-1

# 2. 等待 2-5 分钟

# 3. 触发评估
aws --profile c5611 configservice start-config-rules-evaluation \
  --config-rule-names required-tags-rule
```

### 问题：打标签失败

```bash
# 检查权限
aws --profile c5611 sts get-caller-identity

# 查看错误详情
python3 auto-tag-batch.py c5611 cn-northwest-1 production compute infrastructure 2>&1 | tee tag-errors.log
```

### 问题：评估结果不更新

```bash
# 等待 2-5 分钟，Config 有延迟

# 查看详细合规性
aws --profile c5611 configservice get-compliance-details-by-config-rule \
  --config-rule-name required-tags-rule \
  --compliance-types NON_COMPLIANT \
  --output json | jq '.EvaluationResults | length'
```

## 区域差异速查

| 操作 | 中国区 | Global 区 |
|------|--------|-----------|
| **Profile** | `c5611` | `g0603` |
| **Region** | `cn-northwest-1` | `ap-southeast-1` |
| **ARN** | `arn:aws-cn:...` | `arn:aws:...` |
| **初始化** | `./setup-config.sh c5611 cn-northwest-1 bucket` | `./setup-config.sh g0603 ap-southeast-1 bucket` |
| **部署** | `./manage-rule.sh deploy c5611 cn-northwest-1` | `./manage-rule.sh deploy g0603 ap-southeast-1` |
| **打标签** | `python3 auto-tag-batch.py c5611 cn-northwest-1 ...` | `python3 auto-tag-batch.py g0603 ap-southeast-1 ...` |

## 文件说明

| 文件 | 用途 | 使用频率 |
|------|------|----------|
| `setup-config.sh` | 初始化 Config | 一次性 |
| `manage-rule.sh` | 管理规则 | 经常 |
| `auto-tag-batch.py` | 批量打标签（非交互） | 经常 |
| `auto-tag-resources.py` | 批量打标签（交互） | 偶尔 |
| `troubleshoot.sh` | 故障排查 | 需要时 |
| `config-rule.json` | 规则配置（计费资源） | 默认 |
| `config-rule-all-resources.json` | 规则配置（所有资源） | 可选 |

## 最佳实践

### 1. 定期检查
```bash
# 每周检查一次合规性
./manage-rule.sh status c5611 cn-northwest-1
```

### 2. 新资源立即打标签
```bash
# 创建资源后立即打标签
aws ec2 run-instances ... --tag-specifications 'ResourceType=instance,Tags=[{Key=siteName,Value=production},{Key=businessCostType,Value=compute},{Key=platform,Value=web}]'
```

### 3. 自动化
```bash
# 使用 cron 定期检查和修复
0 2 * * * cd /path/to/aws-tagging-policy-config && python3 auto-tag-batch.py c5611 cn-northwest-1 production compute infrastructure
```

### 4. 监控 Config 记录器
```bash
# 每天检查记录器状态
aws --profile c5611 configservice describe-configuration-recorder-status | jq -r '.ConfigurationRecordersStatus[0].recording'
```

## 成本优化

### Config 费用
- 配置项记录：$0.003/项
- 规则评估：$0.001/评估
- S3 存储：标准费率

### 优化建议
1. 只记录计费资源（使用默认配置）
2. 定期清理 S3 历史数据
3. 合理设置评估频率

### 估算费用
```bash
# 假设 100 个资源，每天评估 1 次
# 配置项：100 * $0.003 = $0.30/月
# 评估：100 * 30 * $0.001 = $3.00/月
# 总计：约 $3.30/月
```

## 支持的资源类型

### 计算
- EC2 Instance, ECS Cluster, ECS Service, EKS Cluster
- Lambda Function, WorkSpaces Workspace, AppStream Fleet

### 存储
- S3 Bucket, EC2 Volume, EFS FileSystem, FSx FileSystem
- Backup BackupVault

### 数据库
- RDS DBInstance, RDS DBCluster, DynamoDB Table
- ElastiCache CacheCluster, ElastiCache ReplicationGroup
- Redshift Cluster, OpenSearch Domain

### 网络
- EC2 NatGateway, ELBv2 LoadBalancer, ELB LoadBalancer
- CloudFront Distribution, GlobalAccelerator Accelerator

### 其他
- SageMaker NotebookInstance, SageMaker Endpoint
- Kinesis Stream, MSK Cluster, Transfer Server

## 联系方式

- 作者：RJ.Wang
- 邮箱：wangrenjun@gmail.com
- 创建时间：2025-11-22
