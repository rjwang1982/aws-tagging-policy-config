#!/bin/bash

# AWS Config 故障排查脚本
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-22

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

usage() {
    echo "使用方法: $0 <profile> <region>"
    echo ""
    echo "示例:"
    echo "  $0 susermt cn-northwest-1"
    echo "  $0 terraform_0603 ap-southeast-1"
    exit 1
}

if [ $# -ne 2 ]; then
    usage
fi

PROFILE=$1
REGION=$2

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}AWS Config 故障排查${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Profile: $PROFILE"
echo "Region:  $REGION"
echo ""

# 1. 检查 AWS 认证
echo -e "${YELLOW}[1/6] 检查 AWS 认证...${NC}"
ACCOUNT_INFO=$(aws --profile $PROFILE sts get-caller-identity --region $REGION --output json 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ AWS 认证失败${NC}"
    echo "$ACCOUNT_INFO"
    exit 1
fi

ACCOUNT_ID=$(echo $ACCOUNT_INFO | jq -r '.Account')
USER_ARN=$(echo $ACCOUNT_INFO | jq -r '.Arn')
echo -e "${GREEN}✓ 认证成功${NC}"
echo "  账号ID: $ACCOUNT_ID"
echo "  用户ARN: $USER_ARN"
echo ""

# 判断区域类型
if [[ $REGION == cn-* ]]; then
    REGION_TYPE="中国区"
    ARN_PARTITION="aws-cn"
else
    REGION_TYPE="Global 区"
    ARN_PARTITION="aws"
fi
echo "  区域类型: $REGION_TYPE"
echo "  ARN 前缀: arn:$ARN_PARTITION:"
echo ""

# 2. 检查 Config 记录器
echo -e "${YELLOW}[2/6] 检查 Config 记录器...${NC}"
RECORDER_STATUS=$(aws --profile $PROFILE configservice describe-configuration-recorder-status --region $REGION --output json 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Config 记录器不存在${NC}"
    echo "  解决方案: ./setup-config.sh $PROFILE $REGION <bucket-name>"
    echo ""
else
    RECORDING=$(echo $RECORDER_STATUS | jq -r '.ConfigurationRecordersStatus[0].recording')
    LAST_START=$(echo $RECORDER_STATUS | jq -r '.ConfigurationRecordersStatus[0].lastStartTime')
    LAST_STOP=$(echo $RECORDER_STATUS | jq -r '.ConfigurationRecordersStatus[0].lastStopTime // "从未停止"')
    
    if [ "$RECORDING" == "true" ]; then
        echo -e "${GREEN}✓ Config 记录器正在运行${NC}"
        echo "  最后启动: $LAST_START"
    else
        echo -e "${RED}✗ Config 记录器已停止${NC}"
        echo "  最后启动: $LAST_START"
        echo "  最后停止: $LAST_STOP"
        echo ""
        echo "  解决方案:"
        echo "  aws --profile $PROFILE configservice start-configuration-recorder --configuration-recorder-name default --region $REGION"
    fi
    echo ""
fi

# 3. 检查 Config 规则
echo -e "${YELLOW}[3/6] 检查 Config 规则...${NC}"
RULE_INFO=$(aws --profile $PROFILE configservice describe-config-rules --config-rule-names required-tags-rule --region $REGION --output json 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Config 规则不存在${NC}"
    echo "  解决方案: ./manage-rule.sh deploy $PROFILE $REGION"
    echo ""
else
    RULE_STATE=$(echo $RULE_INFO | jq -r '.ConfigRules[0].ConfigRuleState')
    echo -e "${GREEN}✓ Config 规则存在${NC}"
    echo "  规则名称: required-tags-rule"
    echo "  规则状态: $RULE_STATE"
    echo ""
fi

# 4. 检查合规性状态
echo -e "${YELLOW}[4/6] 检查合规性状态...${NC}"
COMPLIANCE=$(aws --profile $PROFILE configservice describe-compliance-by-config-rule --config-rule-names required-tags-rule --region $REGION --output json 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ 暂无合规性数据${NC}"
    echo ""
else
    COMPLIANCE_TYPE=$(echo $COMPLIANCE | jq -r '.ComplianceByConfigRules[0].Compliance.ComplianceType')
    
    if [ "$COMPLIANCE_TYPE" == "COMPLIANT" ]; then
        echo -e "${GREEN}✓ 所有资源已合规${NC}"
    else
        NON_COMPLIANT_COUNT=$(echo $COMPLIANCE | jq -r '.ComplianceByConfigRules[0].Compliance.ComplianceContributorCount.CappedCount // 0')
        echo -e "${YELLOW}⚠ 存在不合规资源${NC}"
        echo "  不合规资源数: $NON_COMPLIANT_COUNT"
        echo ""
        echo "  解决方案:"
        echo "  python3 auto-tag-batch.py $PROFILE $REGION production compute infrastructure"
    fi
    echo ""
fi

# 5. 检查发现的资源
echo -e "${YELLOW}[5/6] 检查发现的资源...${NC}"
EC2_COUNT=$(aws --profile $PROFILE configservice list-discovered-resources --resource-type AWS::EC2::Instance --region $REGION --output json 2>&1 | jq -r '.resourceIdentifiers | length')
S3_COUNT=$(aws --profile $PROFILE configservice list-discovered-resources --resource-type AWS::S3::Bucket --region $REGION --output json 2>&1 | jq -r '.resourceIdentifiers | length')
VOLUME_COUNT=$(aws --profile $PROFILE configservice list-discovered-resources --resource-type AWS::EC2::Volume --region $REGION --output json 2>&1 | jq -r '.resourceIdentifiers | length')

echo "  EC2 实例: $EC2_COUNT 个"
echo "  S3 存储桶: $S3_COUNT 个"
echo "  EBS 卷: $VOLUME_COUNT 个"
echo ""

# 6. 检查实际资源数量
echo -e "${YELLOW}[6/6] 检查实际资源数量...${NC}"
ACTUAL_EC2=$(aws --profile $PROFILE ec2 describe-instances --region $REGION --output json 2>&1 | jq -r '[.Reservations[].Instances[]] | length')
ACTUAL_S3=$(aws --profile $PROFILE s3api list-buckets --output json 2>&1 | jq -r '.Buckets | length')

echo "  实际 EC2 实例: $ACTUAL_EC2 个"
echo "  实际 S3 存储桶: $ACTUAL_S3 个"
echo ""

if [ "$EC2_COUNT" != "$ACTUAL_EC2" ]; then
    echo -e "${YELLOW}⚠ Config 发现的 EC2 数量与实际不符${NC}"
    echo "  可能原因: Config 记录器停止期间创建的资源"
    echo "  解决方案: 等待 2-5 分钟让 Config 发现新资源"
    echo ""
fi

# 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}故障排查完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "常用命令:"
echo "  查看状态: ./manage-rule.sh status $PROFILE $REGION"
echo "  打标签:   python3 auto-tag-batch.py $PROFILE $REGION production compute infrastructure"
echo "  触发评估: aws --profile $PROFILE configservice start-config-rules-evaluation --config-rule-names required-tags-rule --region $REGION"
echo ""
