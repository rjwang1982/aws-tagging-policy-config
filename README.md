# AWS 资源标签合规性管理工具

**作者**: RJ.Wang  
**邮箱**: wangrenjun@gmail.com

自动化管理 AWS 资源标签合规性，支持中国区和 Global 区。

## 功能

- ✅ 自动检测缺少必需标签的资源
- ✅ 批量为资源添加标签
- ✅ 支持 30+ 种 AWS 计费资源类型
- ✅ 自动识别中国区/Global 区（ARN 分区：aws-cn / aws）

## 必需标签

| 标签键 | 说明 | 示例值 |
|--------|------|--------|
| `siteName` | 站点/环境名称 | production, staging, development |
| `businessCostType` | 成本类型 | compute, storage, network, infrastructure |
| `platform` | 平台标识 | web, api, data, general |

## 快速开始

### 1. 初始化 AWS Config（首次使用）

```bash
# 中国区
./setup-config.sh c5611 cn-northwest-1 config-bucket-cn

# Global 区
./setup-config.sh g0603 ap-southeast-1 config-bucket-global
```

### 2. 部署标签规则

```bash
# 中国区
./manage-rule.sh deploy c5611 cn-northwest-1

# Global 区
./manage-rule.sh deploy g0603 ap-southeast-1
```

### 3. 批量打标签

```bash
# 方式 1: 使用默认配置（在脚本首部修改 DEFAULT_TAGS）
python3 auto-tag-batch.py c5611 cn-northwest-1

# 方式 2: 使用配置文件（复制 tag-config.json.example 为 tag-config.json）
python3 auto-tag-batch.py c5611 cn-northwest-1 --config

# 方式 3: 命令行指定
python3 auto-tag-batch.py c5611 cn-northwest-1 production compute web
```

### 4. 查看合规状态

```bash
./manage-rule.sh status c5611 cn-northwest-1
```

## 配置说明

### Profile 配置

| 区域 | Profile | Region | ARN 前缀 |
|------|---------|--------|----------|
| 中国区 | c5611 | cn-northwest-1 | arn:aws-cn: |
| Global 区 | g0603 | ap-southeast-1 | arn:aws: |

### 标签配置

**方式 1**: 修改 `auto-tag-batch.py` 首部的 `DEFAULT_TAGS`

```python
DEFAULT_TAGS = {
    'siteName': 'production',
    'businessCostType': 'infrastructure',
    'platform': 'general'
}
```

**方式 2**: 使用配置文件

```bash
# 复制示例文件
cp tag-config.json.example tag-config.json

# 编辑配置
vim tag-config.json

# 使用配置文件
python3 auto-tag-batch.py c5611 cn-northwest-1 --config
```

## 支持的资源类型

- **计算**: EC2 实例、ECS/EKS 集群、Lambda 函数
- **存储**: S3 存储桶、EBS 卷、EFS/FSx 文件系统
- **数据库**: RDS 实例/集群、DynamoDB 表、ElastiCache、Redshift
- **网络**: NAT 网关、负载均衡器、CloudFront
- **其他**: 共 30+ 种计费资源类型

## 常用命令

### Config 记录器管理

```bash
# 检查状态
aws --profile c5611 configservice describe-configuration-recorder-status

# 启动记录器
aws --profile c5611 configservice start-configuration-recorder \
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
```

### 触发评估

```bash
aws --profile c5611 configservice start-config-rules-evaluation \
  --config-rule-names required-tags-rule
```

## 常见问题

### Q: Config 记录器停止了怎么办？

```bash
# 启动记录器
aws --profile c5611 configservice start-configuration-recorder \
  --configuration-recorder-name default
```

### Q: 为什么有些资源没被扫描到？

可能原因：
1. Config 记录器未运行
2. 资源是在记录器停止期间创建的

解决方案：启动记录器，等待 2-5 分钟让 Config 发现资源。

### Q: 打标签后多久能看到合规？

通常 2-5 分钟。AWS Config 评估有延迟。

### Q: 如何添加新的必需标签？

1. 修改 `config-rule.json` 的 `InputParameters`
2. 修改 `auto-tag-batch.py` 的 `DEFAULT_TAGS`
3. 重新部署规则：`./manage-rule.sh deploy c5611 cn-northwest-1`

**注意**: AWS Config `REQUIRED_TAGS` 规则最多支持 6 个标签。

## 文件说明

| 文件 | 用途 |
|------|------|
| `setup-config.sh` | 初始化 AWS Config（首次使用） |
| `manage-rule.sh` | 管理 Config 规则（部署/删除/查看状态） |
| `auto-tag-batch.py` | 批量打标签工具 |
| `config-rule.json` | 规则配置（计费资源） |
| `config-rule-all-resources.json` | 规则配置（所有资源，可选） |
| `tag-config.json.example` | 标签配置示例 |

## 手动打标签

### EC2 实例

```bash
aws --profile c5611 ec2 create-tags \
  --resources i-xxx \
  --tags Key=siteName,Value=production \
         Key=businessCostType,Value=compute \
         Key=platform,Value=web
```

### S3 存储桶

```bash
aws --profile c5611 s3api put-bucket-tagging \
  --bucket my-bucket \
  --tagging 'TagSet=[
    {Key=siteName,Value=production},
    {Key=businessCostType,Value=storage},
    {Key=platform,Value=data}
  ]'
```

## 成本估算

假设 100 个资源，每天评估 1 次：

| 项目 | 单价 | 月费用 |
|------|------|--------|
| 配置项记录 | $0.003/项 | $0.30 |
| 规则评估 | $0.001/评估 | $3.00 |
| S3 存储 | 标准费率 | $0.02 |
| **总计** | | **$3.32/月** |

## 许可证

MIT License
