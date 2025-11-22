#!/usr/bin/env python3
"""
AWS 资源批量打标签工具（非交互式版本）

作者: RJ.Wang
邮箱: wangrenjun@gmail.com
创建时间: 2025-11-22

功能: 批量为不合规资源添加指定的标签，无需交互式输入
"""

import boto3
import sys
from typing import List, Dict, Tuple


class BatchTagger:
    """批量标签管理器"""
    
    def __init__(self, profile: str, region: str, tags: Dict[str, str]):
        """初始化"""
        self.profile = profile
        self.region = region
        self.tags = tags
        self.session = boto3.Session(profile_name=profile, region_name=region)
        self.config_client = self.session.client('config')
        
        # 判断是否为中国区
        self.is_china = region.startswith('cn-')
        self.arn_partition = 'aws-cn' if self.is_china else 'aws'
        
        print(f"区域类型: {'中国区' if self.is_china else 'Global 区'}")
        print(f"ARN 前缀: arn:{self.arn_partition}:")

    
    def get_non_compliant_resources(self) -> List[Dict]:
        """获取不合规资源列表"""
        print("\n📋 正在获取不合规资源...")
        
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
                    'id': qualifier['ResourceId']
                })
            
            print(f"✓ 找到 {len(resources)} 个不合规资源")
            return resources
            
        except Exception as e:
            print(f"✗ 获取失败: {e}")
            sys.exit(1)
    
    def tag_resource(self, resource_type: str, resource_id: str) -> Tuple[bool, str]:
        """为单个资源打标签"""
        try:
            if resource_type == 'AWS::EC2::Instance':
                return self._tag_ec2_instance(resource_id)
            elif resource_type == 'AWS::EC2::Volume':
                return self._tag_ec2_volume(resource_id)
            elif resource_type == 'AWS::S3::Bucket':
                return self._tag_s3_bucket(resource_id)
            elif resource_type == 'AWS::Lambda::Function':
                return self._tag_lambda_function(resource_id)
            elif resource_type == 'AWS::RDS::DBInstance':
                return self._tag_rds_instance(resource_id)
            else:
                return False, f"不支持的资源类型"
        except Exception as e:
            return False, str(e)
    
    def _tag_ec2_instance(self, instance_id: str) -> Tuple[bool, str]:
        """EC2 实例打标签"""
        ec2 = self.session.client('ec2')
        tag_list = [{'Key': k, 'Value': v} for k, v in self.tags.items()]
        ec2.create_tags(Resources=[instance_id], Tags=tag_list)
        return True, "成功"
    
    def _tag_ec2_volume(self, volume_id: str) -> Tuple[bool, str]:
        """EBS 卷打标签"""
        ec2 = self.session.client('ec2')
        tag_list = [{'Key': k, 'Value': v} for k, v in self.tags.items()]
        ec2.create_tags(Resources=[volume_id], Tags=tag_list)
        return True, "成功"
    
    def _tag_s3_bucket(self, bucket_name: str) -> Tuple[bool, str]:
        """S3 存储桶打标签"""
        s3 = self.session.client('s3')
        
        # 获取现有标签
        try:
            response = s3.get_bucket_tagging(Bucket=bucket_name)
            existing_tags = {tag['Key']: tag['Value'] for tag in response.get('TagSet', [])}
        except:
            existing_tags = {}
        
        # 合并标签
        existing_tags.update(self.tags)
        tag_set = [{'Key': k, 'Value': v} for k, v in existing_tags.items()]
        
        s3.put_bucket_tagging(Bucket=bucket_name, Tagging={'TagSet': tag_set})
        return True, "成功"
    
    def _tag_lambda_function(self, function_name: str) -> Tuple[bool, str]:
        """Lambda 函数打标签"""
        lambda_client = self.session.client('lambda')
        response = lambda_client.get_function(FunctionName=function_name)
        function_arn = response['Configuration']['FunctionArn']
        lambda_client.tag_resource(Resource=function_arn, Tags=self.tags)
        return True, "成功"
    
    def _tag_rds_instance(self, db_instance_id: str) -> Tuple[bool, str]:
        """RDS 实例打标签"""
        rds = self.session.client('rds')
        account_id = self.session.client('sts').get_caller_identity()['Account']
        arn = f"arn:{self.arn_partition}:rds:{self.region}:{account_id}:db:{db_instance_id}"
        tag_list = [{'Key': k, 'Value': v} for k, v in self.tags.items()]
        rds.add_tags_to_resource(ResourceName=arn, Tags=tag_list)
        return True, "成功"
    
    def batch_tag(self, resources: List[Dict]):
        """批量打标签"""
        print("\n" + "=" * 80)
        print("开始批量打标签")
        print("=" * 80)
        
        success = 0
        failed = 0
        skipped = 0
        
        for idx, res in enumerate(resources, 1):
            print(f"\n[{idx}/{len(resources)}] {res['type']} - {res['id']}")
            
            ok, msg = self.tag_resource(res['type'], res['id'])
            
            if ok:
                print(f"  ✓ {msg}")
                success += 1
            elif "不支持" in msg:
                print(f"  ⊘ {msg}")
                skipped += 1
            else:
                print(f"  ✗ {msg}")
                failed += 1
        
        print("\n" + "=" * 80)
        print(f"完成: 成功 {success} | 跳过 {skipped} | 失败 {failed}")
        print("=" * 80)


def main():
    if len(sys.argv) < 6:
        print("使用方法: python3 auto-tag-batch.py <profile> <region> <siteName> <businessCostType> <platform>")
        print("")
        print("示例:")
        print("  python3 auto-tag-batch.py c5611 cn-northwest-1 production compute web")
        print("  python3 auto-tag-batch.py g0603 ap-southeast-1 staging storage api")
        sys.exit(1)
    
    profile = sys.argv[1]
    region = sys.argv[2]
    tags = {
        'siteName': sys.argv[3],
        'businessCostType': sys.argv[4],
        'platform': sys.argv[5]
    }
    
    print("=" * 80)
    print("AWS 资源批量打标签工具")
    print("=" * 80)
    print(f"Profile: {profile}")
    print(f"Region:  {region}")
    print(f"标签:")
    for k, v in tags.items():
        print(f"  {k}: {v}")
    print("=" * 80)
    
    tagger = BatchTagger(profile, region, tags)
    resources = tagger.get_non_compliant_resources()
    
    if not resources:
        print("\n✓ 没有不合规资源")
        sys.exit(0)
    
    tagger.batch_tag(resources)
    print("\n提示: 运行以下命令触发重新评估:")
    print(f"  aws --profile {profile} configservice start-config-rules-evaluation --config-rule-names required-tags-rule")


if __name__ == '__main__':
    main()
