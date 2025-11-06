import os
import re
import sys
import json
from dotenv import load_dotenv
from zai import ZhipuAiClient

# 加载环境变量
load_dotenv()

# --- 1. 配置区域 ---
# GitHub Issue 文件夹
BASE_DIR = os.getenv('BASE_DIR', 'github_issues_output')
PROBLEMS_OUTPUT_DIR = os.getenv('PROBLEMS_OUTPUT_DIR', 'generated_problems')
SUITABLE_ISSUES_FILE = os.getenv('SUITABLE_ISSUES_FILE', 'suitable_programming_issues_llm.json')

ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
AI_MODEL = os.getenv("GEN_MODEL", "glm-4.6")  # 您可以根据需要更改模型，例如 glm-4v, glm-3-turbo 等

def get_suitable_issue_ids(json_file):
    suitable_ids = set()

    if not os.path.exists(json_file):
        print(f"警告: 未找到适合的 issue 分析文件 '{json_file}'")
        return suitable_ids

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 遍历所有 issue（除了 metadata）
        for key, value in data.items():
            if key == 'metadata':
                continue

            if value.get('suitable', False):
                # 从 title 中提取 issue 号码
                title = value.get('title', '')
                # 使用正则表达式从 "Issue #3886: ..." 中提取 3886
                match = re.search(r'Issue #(\d+):', title)
                if match:
                    issue_id = match.group(1)
                    suitable_ids.add(issue_id)

        print(f"从 JSON 文件中找到 {len(suitable_ids)} 个适合的 issues")
        return suitable_ids

    except json.JSONDecodeError as e:
        print(f"错误: 无法解析 JSON 文件 '{json_file}': {e}")
        return suitable_ids
    except Exception as e:
        print(f"错误: 读取 JSON 文件时发生错误: {e}")
        return suitable_ids

def get_generated_problem_ids(directory):
    if not os.path.exists(directory):
        return set()

    generated_ids = set()
    # 正则表达式用于从 "source: Issue #12345" 中提取 "12345"
    id_pattern = re.compile(r'source: Issue #(\d+)')
    # 新的正则表达式用于匹配纯数字文件名
    numeric_filename_pattern = re.compile(r'^(\d+)\.md$')

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.md'):
                filepath = os.path.join(root, filename)

                # 首先检查是否是新的数字命名方式
                numeric_match = numeric_filename_pattern.match(filename)
                if numeric_match:
                    # 新的命名方式：直接从文件名提取issue ID
                    generated_ids.add(numeric_match.group(1))
                    continue

                # 旧的命名方式：从文件内容中读取issue ID
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        # 只读取文件的前几行来提高效率
                        content_head = f.read(200)
                        match = id_pattern.search(content_head)
                        if match:
                            generated_ids.add(match.group(1))
                except IOError:
                    continue # 忽略读取失败的文件
    return generated_ids

def sanitize_filename(name):
    sanitized = re.sub(r'[\\/*?:"<>|]', "", name)
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    return sanitized[:150]

def find_feature_and_bug_files(base_dir):
    md_files = []
    if not os.path.exists(base_dir):
        return None
    # 只查找 open_issues 目录，因为目前只爬取了开放的 issues
    state = 'open_issues'
    categories = ['feature', 'bug']
    print(f"正在扫描 '{base_dir}' 下的 '{state}/feature' 和 '{state}/bug' 文件夹...")
    for category in categories:
        target_dir = os.path.join(base_dir, state, category)
        if os.path.exists(target_dir):
            for filename in os.listdir(target_dir):
                if filename.endswith('.md'):
                    md_files.append(os.path.join(target_dir, filename))
    return md_files

def parse_issue_md(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return None
    issue_data = {}
    title_match = re.search(r'# Issue #(\d+): (.*)', content)
    url_match = re.search(r'- \*\*GitHub 链接\*\*: \[View on GitHub\]\((.*)\)', content)
    body_match = re.search(r'## 描述 \(Description\)\n\n(.*)', content, re.S)
    if title_match:
        issue_data['number'] = title_match.group(1)
        issue_data['title'] = title_match.group(2).strip()
    if url_match:
        issue_data['url'] = url_match.group(1).strip()
    if body_match:
        issue_data['body'] = body_match.group(1).strip()
    return issue_data

# --- 3. AI 交互与解析函数 (全新) ---

def generate_problem_with_ai(client, issue_data, task_type_cn, repo_name):
    # 构造给 AI 的系统指令 (System Prompt)
    system_prompt = """
你是一个专业的编程挑战创建者。你的任务是将一个 GitHub Issue 的原始信息，转换成一个结构清晰、内容具体的编程题目。
你必须严格按照以下格式输出中文，不要添加任何额外的解释或开场白。

格式如下:
prompt = \"\"\"
[这里是你生成的、面向开发者的任务描述]
\"\"\"

AC = [
    "这里是第一条验收标准",
    "这里是第二条验收标准",
    "依此类推..."
]
"""

    # 构造给 AI 的用户输入 (User Prompt)
    user_prompt = f"""
请根据以下 GitHub Issue 信息，为开发者创建一个编程挑战。

- **仓库名称**: {repo_name}
- **任务类型**: {task_type_cn}
- **Issue 标题**: {issue_data.get('title')}
- **Issue 详细描述**:
---
{issue_data.get('body')}
---
"""

    print("\n正在调用 AI 生成编程题目，请稍候...")
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5 # 较低的温度确保输出更稳定和结构化
        )
        ai_content = response.choices[0].message.content
        return ai_content # 直接返回AI生成的完整字符串
    except zai.core.APIStatusError as e:
        print(f"AI API 错误: {e}")
    except zai.core.APITimeoutError as err:
        return f"请求超时: {err}"
    except Exception as e:
        print(f"调用 AI 时发生未知错误: {e}")
    return None


if __name__ == '__main__':
    if not ZHIPU_API_KEY:
        print("错误: 请在 .env 文件中设置 ZHIPU_API_KEY！")
        sys.exit(1)

    ai_client = ZhipuAiClient(api_key=ZHIPU_API_KEY)

    # 首先读取适合的 issue ID
    suitable_issue_ids = get_suitable_issue_ids(SUITABLE_ISSUES_FILE)

    issue_files = find_feature_and_bug_files(BASE_DIR)

    if not issue_files:
        print(f"在 '{BASE_DIR}' 的 feature/bug 目录中没有找到任何 .md 文件。")
    else:
        existing_problem_ids = get_generated_problem_ids(PROBLEMS_OUTPUT_DIR)
        print(f"发现 {len(existing_problem_ids)} 个已生成的题目，将基于 Issue ID 进行去重。\n")

        # 过滤只包含适合的 issue 文件
        filtered_files = []
        for file_path in issue_files:
            issue_data = parse_issue_md(file_path)
            if issue_data and 'number' in issue_data:
                issue_id = issue_data['number']
                if issue_id in suitable_issue_ids:
                    filtered_files.append(file_path)
                else:
                    print(f"⏩ 跳过 (不适合作为题目): Issue #{issue_id} - {issue_data.get('title', '')[:40]}...")
            else:
                print(f"❌ 解析文件失败，已跳过: {file_path}")

        issue_files = filtered_files
        print(f"\n从 {len(issue_files)} 个适合的 issues 中生成题目\n")

        issue_files.sort()

        for selected_file in issue_files:
            # 由于已经在过滤阶段解析过，这里可以直接从路径中获取 issue ID
            # 但为了保持代码一致性，我们重新解析一次
            issue_data = parse_issue_md(selected_file)
            if not issue_data or 'number' not in issue_data:
                print(f"❌ 解析文件失败，已跳过: {selected_file}")
                continue

            if issue_data['number'] in existing_problem_ids:
                print(f"⏩ 已跳过 (题目已存在): Issue #{issue_data['number']} - {issue_data['title'][:40]}...")
                continue

            print(f"--- 正在处理新 Issue: #{issue_data['number']} ---")

            # 由于只处理 open_issues，所以状态固定为 'open'
            state = 'open'
            category = 'bug' if os.sep + 'bug' + os.sep in selected_file else 'feature'
            repo_name = selected_file.split(os.sep)[-4] if len(selected_file.split(os.sep)) > 3 else "开源项目"
            
            task_type_cn = "Bug 修复" if category == 'bug' else "新功能开发"
            problem_title_for_content = f"{task_type_cn}: {issue_data.get('title')}"
            
            problem_statement = generate_problem_with_ai(ai_client, issue_data, task_type_cn, repo_name)
            
            if problem_statement:
                final_output = f"""题目: {problem_title_for_content}
source: Issue #{issue_data.get('number')}
url: {issue_data.get('url')}

{problem_statement.strip()}
"""
                # 【更新】新的文件名和文件夹路径
                # 使用 issue ID 作为文件名，避免特殊字符问题
                issue_id = issue_data.get('number')
                filename = f"{issue_id}.md"

                output_folder_name = f"{state}_{category}"
                output_sub_dir = os.path.join(PROBLEMS_OUTPUT_DIR, output_folder_name)
                os.makedirs(output_sub_dir, exist_ok=True)

                filepath = os.path.join(output_sub_dir, filename)

                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(final_output)
                    print(f"✅ 题目已成功保存到: {filepath}\n")
                except IOError as e:
                    print(f"❌ 保存文件失败: {e}\n")
            else:
                print("❌ AI 未能成功生成题目内容。\n")
        
        print("--- 所有任务处理完毕 ---")