import os
import requests
import re
from datetime import datetime
from issue_classifier import classify_issue_with_confidence

# --- 1. 配置区域 ---
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', 'YOUR_PERSONAL_ACCESS_TOKEN') 
REPO_OWNER = 'Microsoft'
REPO_NAME = 'vscode'
SINCE_DATE = '2025-09-01'
BASE_OUTPUT_DIR = 'github_issues_output'

# --- 脚本主要逻辑 ---

def get_existing_issue_map(directory):
    if not os.path.exists(directory):
        return {}
    
    issue_map = {}
    id_pattern = re.compile(r'issue_(\d+)_.*\.md')
    
    for root, _, files in os.walk(directory):
        for filename in files:
            match = id_pattern.match(filename)
            if match:
                issue_id = match.group(1)
                issue_map[issue_id] = os.path.join(root, filename)
            
    return issue_map

def fetch_and_process_issues(existing_issue_map):
    all_issues = []
    # 先获取 open，再获取 closed
    for state in ['open']: # , 'closed'
        print(f"--- 开始获取 '{state}' 状态的 Issues ---")
        api_url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues'
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        params = {
            'state': state,
            'since': SINCE_DATE,
            'direction': 'desc',
            'sort': 'updated', # 按更新时间排序，更容易捕获状态变化
            'per_page': 100
        }
        page = 1
        
        while api_url:
            print(f"正在获取 '{state}' Issues, 第 {page} 页...")
            try:
                response = requests.get(api_url, headers=headers, params=params)
                response.raise_for_status()
            except requests.exceptions.RequestException as err:
                print(f"网络或API请求失败: {err}")
                break

            issues_page = response.json()
            if not issues_page:
                break
            
            all_issues.extend(issues_page)
            
            if 'next' in response.links:
                api_url = response.links['next']['url']
                params = {} 
            else:
                api_url = None
            page += 1

    print(f"\n--- 获取完成，共 {len(all_issues)} 条 issues。开始处理和保存... ---")
    
    # 统一处理所有获取到的 issues
    new_count = 0
    skipped_count = 0
    for issue in all_issues:
        issue_id_str = str(issue['number'])

        # 检查 issue 是否已存在，如果存在则跳过
        if issue_id_str in existing_issue_map:
            print(f"⏭️  跳过已存在的 Issue #{issue_id_str}")
            skipped_count += 1
            continue
        else:
            # 如果是全新的 issue，直接保存
            save_issue_as_markdown(issue)
            new_count += 1
            
    print(f"\n--- 处理完毕 ---")
    print(f"新增 Issue: {new_count} 个")
    print(f"跳过已存在 Issue: {skipped_count} 个")


def save_issue_as_markdown(issue):
    state_dir = 'open_issues' if issue['state'] == 'open' else 'closed_issues'

    # 使用增强分类器
    title = issue.get('title', '')
    body = issue.get('body', '')
    labels = [label.get('name', '') for label in issue.get('labels', [])] if issue.get('labels') else []

    category, confidence = classify_issue_with_confidence(title, body, labels)
    category_dir = category

    # 可选：输出分类信息用于调试
    print(f"  📊 Issue #{issue['number']} 分类为: {category_dir} (置信度: {confidence:.2f})")
    
    output_dir = os.path.join(BASE_OUTPUT_DIR, state_dir, category_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    safe_title = "".join(c for c in issue['title'] if c.isalnum() or c in (' ', '_', '-')).rstrip()
    filename = f"issue_{issue['number']}_{safe_title[:50]}.md"
    filepath = os.path.join(output_dir, filename)

    md_content = f"""# Issue #{issue['number']}: {issue['title']}
- **状态 (State)**: {issue['state']}
- **创建者 (Author)**: [{issue['user']['login']}]({issue['user']['html_url']})
- **创建时间 (Created at)**: {datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')}
- **GitHub 链接**: [View on GitHub]({issue['html_url']})
---
## 描述 (Description)

{issue['body'] if issue['body'] else "此 Issue 没有提供描述。"}
"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
    except IOError as e:
        print(f"保存文件失败: {filepath}. 错误: {e}")

if __name__ == '__main__':
    if 'YOUR_PERSONAL_ACCESS_TOKEN' in GITHUB_TOKEN or not GITHUB_TOKEN:
        print("错误: 请在脚本的配置区域填入您的 GitHub Personal Access Token！")
    else:
        # 1. 先获取本地所有已存在的 issue
        existing_map = get_existing_issue_map(BASE_OUTPUT_DIR)
        print(f"扫描本地，发现 {len(existing_map)} 个已存在的 issues。")
        # 2. 获取并处理
        fetch_and_process_issues(existing_map)
        print("\n所有操作完成！")