#!/bin/bash

# AWS Config 规则部署脚本
# 作者: RJ.Wang
# 邮箱: wangrenjun@gmail.com
# 创建时间: 2025-11-21

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 使用说明
usage() {
    echo "使用方法: $0 <profile> <region>"
    echo ""
    echo "参数说明:"
    echo "  profile  - AWS CLI profile 名称 (例如: susermt, terraform_0603)"
    echo "  region   - AWS 区域 (例如: cn-northwest-1, us-east-1)"
    echo ""
    echo "示例:"
    echo "  $0 susermt cn-northwest-1          # 中国区部署"
    echo "  $0 terraform_0603 us-east-1        # Global 区部署"
    exit 1
}

# 检查参数
if [ $# -ne 2 ]; then
    usage
fi

PROFILE=$1
REGION=$2

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AWS Config 规则部署${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Profile: $PROFILE"
echo "Region:  $REGION"
echo ""

# 验证 AWS 认证
echo -e "${YELLOW}[1/3] 验证 AWS 认证...${NC}"
ACCOUNT_INFO=$(aws --profile $PROFILE sts get-caller-identity --region $REGION 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}错误: AWS 认证失败${NC}"
    echo "$ACCOUNT_INFO"
    exit 1
fi

ACCOUNT_ID=$(echo $ACCOUNT_INFO | jq -r '.Account')
USER_ARN=$(echo $ACCOUNT_INFO | jq -r '.Arn')
echo -e "${GREEN}✓ 认证成功${NC}"
echo "  账号ID: $ACCOUNT_ID"
echo "  用户ARN: $USER_ARN"
echo ""

# 检查 AWS Config 是否启用
echo -e "${YELLOW}[2/3] 检查 AWS Config 状态...${NC}"
CONFIG_STATUS=$(aws --profile $PROFILE configservice describe-configuration-recorder-status --region $REGION 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}警告: AWS Config 可能未启用${NC}"
    echo "请先启用 AWS Config 服务，或运行 setup-config.sh 脚本"
    echo ""
    read -p "是否继续部署规则? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ AWS Config 已启用${NC}"
fi
echo ""

# 部署 Config 规则
echo -e "${YELLOW}[3/3] 部署 Config 规则...${NC}"
aws --profile $PROFILE configservice put-config-rule \
    --config-rule file://config-rule.json \
    --region $REGION

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 规则部署成功${NC}"
else
    echo -e "${RED}✗ 规则部署失败${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "后续操作:"
echo "1. 运行合规性检查: ./check-compliance.sh $PROFILE $REGION"
echo "2. 查看 AWS Config 控制台: https://console.aws.amazon.com/config/"
echo "3. 查看不合规资源并添加标签"
echo ""
