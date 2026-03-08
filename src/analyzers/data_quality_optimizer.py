"""
Data Quality Optimizer - 数据质量优化
数据验证、去重、增量更新
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import os


class DataQualityOptimizer:
    def __init__(self, github_db: str = "storage/data/github_activity.db",
                 twitter_db: str = "storage/data/twitter_posts_jina.db"):
        """
        初始化数据质量优化器

        Args:
            github_db: GitHub 数据库路径
            twitter_db: Twitter 数据库路径
        """
        self.github_db = github_db
        self.twitter_db = twitter_db

    def remove_duplicates_github(self) -> Dict:
        """
        移除 GitHub 数据中的重复项

        Returns:
            去重结果
        """
        print("\n🔍 正在检查 GitHub 数据重复...")

        conn = sqlite3.connect(self.github_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 获取所有记录
        cursor.execute('SELECT * FROM github_activity')
        all_records = [dict(row) for row in cursor.fetchall()]

        # 去重：根据 id 去重
        unique_ids = set()
        duplicates = []

        for record in all_records:
            record_id = record.get('id', '')
            if record_id in unique_ids:
                duplicates.append(record)
            else:
                unique_ids.add(record_id)

        # 删除重复项
        removed_count = 0
        for dup in duplicates:
            cursor.execute('DELETE FROM github_activity WHERE id = ?', (dup['id'],))
            removed_count += 1

        conn.commit()
        conn.close()

        result = {
            'total_records': len(all_records),
            'unique_records': len(unique_ids),
            'duplicates_removed': removed_count
        }

        print(f"✅ GitHub 去重完成：")
        print(f"   - 总记录数：{result['total_records']}")
        print(f"   - 唯一记录数：{result['unique_records']}")
        print(f"   - 移除重复数：{result['duplicates_removed']}")

        return result

    def remove_duplicates_twitter(self) -> Dict:
        """
        移除 Twitter 数据中的重复项

        Returns:
            去重结果
        """
        if not os.path.exists(self.twitter_db):
            print("⚠️  Twitter 数据库不存在")
            return {'total_records': 0, 'unique_records': 0, 'duplicates_removed': 0}

        print("\n🔍 正在检查 Twitter 数据重复...")

        conn = sqlite3.connect(self.twitter_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 获取所有记录
        cursor.execute('SELECT * FROM twitter_posts')
        all_records = [dict(row) for row in cursor.fetchall()]

        # 去重：根据 id 去重
        unique_ids = set()
        duplicates = []

        for record in all_records:
            record_id = record.get('id', '')
            if record_id in unique_ids:
                duplicates.append(record)
            else:
                unique_ids.add(record_id)

        # 删除重复项
        removed_count = 0
        for dup in duplicates:
            cursor.execute('DELETE FROM twitter_posts WHERE id = ?', (dup['id'],))
            removed_count += 1

        conn.commit()
        conn.close()

        result = {
            'total_records': len(all_records),
            'unique_records': len(unique_ids),
            'duplicates_removed': removed_count
        }

        print(f"✅ Twitter 去重完成：")
        print(f"   - 总记录数：{result['total_records']}")
        print(f"   - 唯一记录数：{result['unique_records']}")
        print(f"   - 移除重复数：{result['duplicates_removed']}")

        return result

    def validate_data_github(self) -> Dict:
        """
        验证 GitHub 数据质量

        Returns:
            验证结果
        """
        print("\n🔍 正在验证 GitHub 数据质量...")

        conn = sqlite3.connect(self.github_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 统计问题记录
        issues = {
            'missing_fields': 0,
            'null_values': 0,
            'invalid_dates': 0,
            'future_dates': 0
        }

        cursor.execute('SELECT * FROM github_activity')
        records = cursor.fetchall()

        for row in records:
            # Row 对象可以通过索引或 key 访问
            # 字段名：id, repo_name, repo_owner, author, activity_type, description, url, stars, timestamp, collected_at
            try:
                # 检查必填字段
                id_val = row['id']
                repo_name_val = row['repo_name']

                if not id_val or not repo_name_val:
                    issues['missing_fields'] += 1

                # 检查 null 值
                for field_name in ['id', 'repo_name', 'repo_owner', 'author', 'activity_type', 'description', 'url', 'stars', 'timestamp', 'collected_at']:
                    if row[field_name] is None:
                        issues['null_values'] += 1

                # 检查日期
                timestamp = row['timestamp']
                if timestamp:
                    try:
                        date_obj = datetime.fromisoformat(str(timestamp))
                        # 检查未来日期
                        if date_obj > datetime.now():
                            issues['future_dates'] += 1
                    except:
                        issues['invalid_dates'] += 1
            except Exception as e:
                # 如果访问失败，记录为错误
                issues['missing_fields'] += 1
                print(f"⚠️  处理记录失败: {e}")

        conn.close()

        result = {
            'total_records': len(records),
            'validation_issues': issues
        }

        print(f"✅ GitHub 数据验证完成：")
        print(f"   - 总记录数：{result['total_records']}")
        print(f"   - 缺少字段：{issues['missing_fields']}")
        print(f"   - 空值：{issues['null_values']}")
        print(f"   - 无效日期：{issues['invalid_dates']}")
        print(f"   - 未来日期：{issues['future_dates']}")

        return result

    def optimize_storage(self, compact: bool = False) -> Dict:
        """
        优化存储空间

        Args:
            compact: 是否压缩数据库

        Returns:
            优化结果
        """
        print("\n🔧 正在优化存储空间...")

        result = {
            'github_optimized': False,
            'twitter_optimized': False,
            'size_reduction': 0
        }

        # GitHub 数据库优化
        if os.path.exists(self.github_db):
            size_before = os.path.getsize(self.github_db)
            conn = sqlite3.connect(self.github_db)
            if compact:
                conn.execute('VACUUM')
                conn.execute('ANALYZE')
                conn.commit()
                print(f"   GitHub 数据库已压缩")
                result['github_optimized'] = True
            conn.close()

            if compact:
                size_after = os.path.getsize(self.github_db)
                result['size_reduction'] = size_before - size_after

        # Twitter 数据库优化
        if os.path.exists(self.twitter_db):
            size_before = os.path.getsize(self.twitter_db)
            conn = sqlite3.connect(self.twitter_db)
            if compact:
                conn.execute('VACUUM')
                conn.execute('ANALYZE')
                conn.commit()
                print(f"   Twitter 数据库已压缩")
                result['twitter_optimized'] = True
            conn.close()

            if compact:
                size_after = os.path.getsize(self.twitter_db)
                result['size_reduction'] += size_before - size_after

        print(f"✅ 存储优化完成！")

        return result

    def generate_quality_report(self) -> str:
        """
        生成数据质量报告

        Returns:
            Markdown 格式的报告
        """
        report_date = datetime.now().strftime("%Y年%m月%d日 %H:%M")

        # GitHub 数据验证
        github_result = self.validate_data_github()
        github_dup_result = self.remove_duplicates_github()

        # Twitter 数据验证
        twitter_dup_result = self.remove_duplicates_twitter()

        # 存储优化
        storage_result = self.optimize_storage(compact=False)

        report = f"""# 🧹 Silicon Valley Alpha Radar - 数据质量报告

**生成时间：** {report_date}

---

## 📊 GitHub 数据质量

### 验证结果
- **总记录数：** {github_result['total_records']}
- **缺少字段：** {github_result['validation_issues']['missing_fields']}
- **空值：** {github_result['validation_issues']['null_values']}
- **无效日期：** {github_result['validation_issues']['invalid_dates']}
- **未来日期：** {github_result['validation_issues']['future_dates']}

### 去重结果
- **去重前：** {github_dup_result['total_records']} 条
- **去重后：** {github_dup_result['unique_records']} 条
- **移除重复：** {github_dup_result['duplicates_removed']} 条

---

## 📱 Twitter 数据质量

### 去重结果
- **去重前：** {twitter_dup_result['total_records']} 条
- **去重后：** {twitter_dup_result['unique_records']} 条
- **移除重复：** {twitter_dup_result['duplicates_removed']} 条

---

## 🔧 存储优化

### 优化状态
- **GitHub 数据库：** {'已优化' if storage_result['github_optimized'] else '未优化'}
- **Twitter 数据库：** {'已优化' if storage_result['twitter_optimized'] else '未优化'}
- **空间节省：** {storage_result['size_reduction']} 字节

---

## 💡 建议

### 数据质量
- ✅ 定期运行去重
- ✅ 检查必填字段完整性
- ✅ 验证日期格式
- ✅ 监控空值和无效值

### 存储优化
- ✅ 定期压缩数据库 (VACUUM)
- ✅ 定期分析统计信息 (ANALYZE)
- ✅ 考虑数据库分表（大量数据时）

### 自动化
- 🔄 创建定时任务自动运行优化
- 🔄 设置数据质量告警阈值
- 🔄 实现增量更新（只更新新数据）

---

**报告生成器：** Nina (你的猫耳娘 AI 秘书）🐱✨
**项目：** Silicon Valley Alpha Radar
**版本：** 0.1.0
"""

        return report


def main():
    """主程序"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Silicon Valley Alpha Radar - 数据质量优化"
    )
    parser.add_argument('--compact', action='store_true',
                    help='压缩数据库（VACUUM + ANALYZE）')
    parser.add_argument('--output', type=str, help='输出文件路径 (可选）')

    args = parser.parse_args()

    # 初始化优化器
    optimizer = DataQualityOptimizer()

    # 执行优化
    report = optimizer.generate_quality_report()

    # 保存或显示报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 质量报告已保存到: {args.output}")
    else:
        output_dir = "output/reports"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data_quality_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ 质量报告已保存到: {filepath}")

    return 0


if __name__ == "__main__":
    main()
