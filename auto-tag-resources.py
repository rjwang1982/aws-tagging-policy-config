#!/usr/bin/env python3
"""
AWS 资源自动打标签工具

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-21

功能:
1. 读取 AWS Config 不合规资源列表
2. 显示资源详情供用户确认
3. 批量为资源添加必需的标签
"""

import boto3
import sys
import json
from typing import List, Dict, Tuple


class ResourceTagger:
    """资源标签管理器"""
    
    def __init__(self, profile: str, region: str):
        """初始化"""
        self.profile = profile
        self.region = region
        self.session = boto3.Session(profile_name=profile, region_name=region)
        self.config_client = self.session.client('config')
        
        # 判断是否为中国区
        self.is_china = region.startswith('cn-')
        self.arn_partition = 'aws-cn' if self.is_china else 'aws'
        
        # 必需的标签
        self.required_tags = {
            'siteName': '',
            'businessCostType': '',
            'platform': ''
        }
    
    def get_non_compliant_resources(self) -> List[Dict]:
        """获取不合规资源列表"""
        print("📋 正在获取不合规资源列表...")
        
        try:
            response = self.config_client.get_compliance_details_by_config_rule(
                ConfigRuleName='required-tags-rule',
                ComplianceTypes=['NON_COMPLIANT']
            )
            
            resources = []
            for result in response.get('EvaluationResults', []):
                qualifier = result['EvaluationResultIdentifier']['EvaluationResultQualifier']
                resources.append({
                    'type': qualifier['ResourceType'],
                    'id': qualifier['ResourceId'],
                    'annotation': result.get('Annotation', '缺少必需标签')
                })
            
            print(f"✓ 找到 {len(resources)} 个不合规资源\n")
            return resources
            
        except Exception as e:
            print(f"✗ 获取资源列表失败: {e}")
            sys.exit(1)
    
    def display_resources(self, resources: List[Dict]):
        """显示资源列表"""
        print("=" * 80)
        print("不合规资源列表")
        print("=" * 80)
        
        # 按资源类型分组统计
        type_count = {}
        for res in resources:
            res_type = res['type']
            type_count[res_type] = type_count.get(res_type, 0) + 1
        
        print("\n资源类型统计:")
        for res_type, count in sorted(type_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {res_type}: {count} 个")
        
        print("\n详细列表:")
        for idx, res in enumerate(resources, 1):
            print(f"\n{idx}. {res['type']}")
            print(f"   资源ID: {res['id']}")
            print(f"   问题: {res['annotation']}")
        
        print("\n" + "=" * 80)
    
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
        
        return tags
    
    def resource_exists(self, resource_type: str, resource_id: str) -> bool:
        """检查资源是否存在"""
        try:
            if resource_type == 'AWS::EC2::Instance':
                ec2 = self.session.client('ec2')
                response = ec2.describe_instances(InstanceIds=[resource_id])
                return len(response['Reservations']) > 0
            elif resource_type == 'AWS::EC2::Volume':
                ec2 = self.session.client('ec2')
                response = ec2.describe_volumes(VolumeIds=[resource_id])
                return len(response['Volumes']) > 0
            elif resource_type == 'AWS::S3::Bucket':
                s3 = self.session.client('s3')
                s3.head_bucket(Bucket=resource_id)
                return True
            else:
                # 其他资源类型假设存在
                return True
        except:
            return False
    
    def tag_resource(self, resource_type: str, resource_id: str, tags: Dict[str, str]) -> Tuple[bool, str]:
        """为单个资源打标签"""
        try:
            if resource_type == 'AWS::EC2::Instance':
                return self._tag_ec2_instance(resource_id, tags)
            elif resource_type == 'AWS::EC2::Volume':
                return self._tag_ec2_volume(resource_id, tags)
            elif resource_type == 'AWS::S3::Bucket':
                return self._tag_s3_bucket(resource_id, tags)
            elif resource_type == 'AWS::Lambda::Function':
                return self._tag_lambda_function(resource_id, tags)
            elif resource_type == 'AWS::RDS::DBInstance':
                return self._tag_rds_instance(resource_id, tags)
            elif resource_type == 'AWS::DynamoDB::Table':
                return self._tag_dynamodb_table(resource_id, tags)
            elif resource_type == 'AWS::ElasticLoadBalancingV2::LoadBalancer':
                return self._tag_elb(resource_id, tags)
            else:
                return False, f"不支持的资源类型: {resource_type}"
        except Exception as e:
            return False, str(e)
    
    def _tag_ec2_instance(self, instance_id: str, tags: Dict[str, str]) -> Tuple[bool, str]:
        """EC2 实例打标签"""
        ec2 = self.session.client('ec2')
        tag_list = [{'Key': k, 'Value': v} for k, v in tags.items()]
        ec2.create_tags(Resources=[instance_id], Tags=tag_list)
        return True, "成功"
    
    def _tag_ec2_volume(self, volume_id: str, tags: Dict[str, str]) -> Tuple[bool, str]:
        """EBS 卷打标签"""
        ec2 = self.session.client('ec2')
        tag_list = [{'Key': k, 'Value': v} for k, v in tags.items()]
        ec2.create_tags(Resources=[volume_id], Tags=tag_list)
        return True, "成功"
    
    def _tag_s3_bucket(self, bucket_name: str, tags: Dict[str, str]) -> Tuple[bool, str]:
        """S3 存储桶打标签"""
        s3 = self.session.client('s3')
        
        # 获取现有标签
        try:
            response = s3.get_bucket_tagging(Bucket=bucket_name)
            existing_tags = {tag['Key']: tag['Value'] for tag in response.get('TagSet', [])}
        except:
            existing_tags = {}
        
        # 合并标签
        existing_tags.update(tags)
        tag_set = [{'Key': k, 'Value': v} for k, v in existing_tags.items()]
        
        s3.put_bucket_tagging(Bucket=bucket_name, Tagging={'TagSet': tag_set})
        return True, "成功"
    
    def _tag_lambda_function(self, function_name: str, tags: Dict[str, str]) -> Tuple[bool, str]:
        """Lambda 函数打标签"""
        lambda_client = self.session.client('lambda')
        
        # 获取函数 ARN
        response = lambda_client.get_function(FunctionName=function_name)
        function_arn = response['Configuration']['FunctionArn']
        
        lambda_client.tag_resource(Resource=function_arn, Tags=tags)
        return True, "成功"
    
    def _tag_rds_instance(self, db_instance_id: str, tags: Dict[str, str]) -> Tuple[bool, str]:
        """RDS 实例打标签"""
        rds = self.session.client('rds')
        
        # 构建 ARN（支持中国区和 Global 区）
        account_id = self.session.client('sts').get_caller_identity()['Account']
        arn = f"arn:{self.arn_partition}:rds:{self.region}:{account_id}:db:{db_instance_id}"
        
        tag_list = [{'Key': k, 'Value': v} for k, v in tags.items()]
        rds.add_tags_to_resource(ResourceName=arn, Tags=tag_list)
        return True, "成功"
    
    def _tag_dynamodb_table(self, table_name: str, tags: Dict[str, str]) -> Tuple[bool, str]:
        """DynamoDB 表打标签"""
        dynamodb = self.session.client('dynamodb')
        
        # 获取表 ARN
        response = dynamodb.describe_table(TableName=table_name)
        table_arn = response['Table']['TableArn']
        
        tag_list = [{'Key': k, 'Value': v} for k, v in tags.items()]
        dynamodb.tag_resource(ResourceArn=table_arn, Tags=tag_list)
        return True, "成功"
    
    def _tag_elb(self, lb_arn: str, tags: Dict[str, str]) -> Tuple[bool, str]:
        """负载均衡器打标签"""
        elbv2 = self.session.client('elbv2')
        tag_list = [{'Key': k, 'Value': v} for k, v in tags.items()]
        elbv2.add_tags(ResourceArns=[lb_arn], Tags=tag_list)
        return True, "成功"
    
    def batch_tag_resources(self, resources: List[Dict], tags: Dict[str, str]):
        """批量打标签"""
        print("\n" + "=" * 80)
        print("开始批量打标签")
        print("=" * 80)
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for idx, res in enumerate(resources, 1):
            print(f"\n[{idx}/{len(resources)}] {res['type']}")
            print(f"  资源ID: {res['id']}")
            
            # 检查资源是否存在
            if not self.resource_exists(res['type'], res['id']):
                print(f"  ⊘ 跳过（资源不存在，可能已删除）")
                skipped_count += 1
                continue
            
            success, message = self.tag_resource(res['type'], res['id'], tags)
            
            if success:
                print(f"  ✓ {message}")
                success_count += 1
            elif "不支持" in message:
                print(f"  ⊘ {message}")
                skipped_count += 1
            else:
                print(f"  ✗ 失败: {message}")
                failed_count += 1
        
        print("\n" + "=" * 80)
        print("批量打标签完成")
        print("=" * 80)
        print(f"成功: {success_count} 个")
        print(f"跳过: {skipped_count} 个（不支持的资源类型）")
        print(f"失败: {failed_count} 个")
        print("=" * 80)


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("使用方法: python3 auto-tag-resources.py <profile> <region>")
        print("")
        print("示例:")
        print("  python3 auto-tag-resources.py c5611 cn-northwest-1")
        print("  python3 auto-tag-resources.py g0603 ap-southeast-1")
        sys.exit(1)
    
    profile = sys.argv[1]
    region = sys.argv[2]
    
    print("=" * 80)
    print("AWS 资源自动打标签工具")
    print("=" * 80)
    print(f"Profile: {profile}")
    print(f"Region:  {region}")
    print("=" * 80)
    print("")
    
    # 初始化
    tagger = ResourceTagger(profile, region)
    
    # 获取不合规资源
    resources = tagger.get_non_compliant_resources()
    
    if not resources:
        print("✓ 没有不合规资源，无需打标签")
        sys.exit(0)
    
    # 显示资源列表
    tagger.display_resources(resources)
    
    # 确认是否继续
    print("\n是否要为这些资源打标签？")
    confirm = input("输入 'yes' 继续，其他任意键取消: ").strip().lower()
    
    if confirm != 'yes':
        print("\n已取消操作")
        sys.exit(0)
    
    # 获取标签值
    print("")
    tags = tagger.get_tag_values()
    
    if not tags:
        print("\n✗ 标签值无效，操作已取消")
        sys.exit(1)
    
    # 确认标签值
    print("\n将使用以下标签:")
    for key, value in tags.items():
        print(f"  {key}: {value}")
    
    final_confirm = input("\n确认无误？输入 'yes' 开始打标签: ").strip().lower()
    
    if final_confirm != 'yes':
        print("\n已取消操作")
        sys.exit(0)
    
    # 批量打标签
    tagger.batch_tag_resources(resources, tags)
    
    print("\n提示: 运行 ./manage-rule.sh status 查看更新后的合规性状态")


if __name__ == '__main__':
    main()
