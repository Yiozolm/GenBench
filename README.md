# GenBench 🚀

GenBench 是一个用于从 GitHub Issues 生成编程练习题的工具链，能够自动收集、分析、分类和转换 GitHub Issues 为结构化的编程题目。

## 功能特性 ✨

- **自动 Issue 收集**: 从指定 GitHub 仓库批量获取 Issues
- **智能分类**: 使用机器学习算法将 Issues 自动分类为 Bug、功能增强或其他类型
- **适用性分析**: 通过关键词匹配和 LLM 分析识别适合作为编程练习的 Issues
- **题目生成**: 将合适的 Issues 转换为结构化的编程题目
- **去重处理**: 避免重复处理已生成的题目

## 项目结构 📁

```
GenBench/
├── README.md                    # 项目说明文档
├── analyze.py                   # Issue 分析工具
├── generate.py                  # 编程题目生成工具
├── issue_classifier.py          # Issue 分类器
├── Scratch.py                   # GitHub Issues 爬取工具
├── github_issues_output/        # 爬取的 Issues 存储目录
├── generated_problems/          # 生成的编程题目目录
└── suitable_programming_issues_llm.json  # 分析结果文件
```

## 核心模块 🔧

### 1. `Scratch.py` - GitHub Issues 爬取工具
- 从指定 GitHub 仓库获取 Issues
- 支持按状态（open/closed）和日期筛选
- 使用智能分类器对 Issues 进行分类存储
- 自动去重，避免重复下载

### 2. `issue_classifier.py` - Issue 智能分类器
- 基于关键词权重的分类算法
- 支持中英文关键词识别
- 提供分类置信度评估
- 支持模板匹配和排除词过滤

### 3. `analyze.py` - Issue 适用性分析工具
- **关键词分析**: 基于规则的方法快速筛选
- **LLM 分析**: 使用智谱 AI 进行深度分析
- **混合模式**: 结合两种方法的优势
- 支持参考示例对比分析

### 4. `generate.py` - 编程题目生成工具
- 将合适的 Issues 转换为标准化的编程题目格式
- 使用 AI 生成题目描述和验收标准
- 支持批量处理和增量更新

## 依赖要求 📦

### Python 包依赖
- `zai-sdk>=0.0.4` - 智谱 AI SDK
- `requests>=2.32.3` - HTTP 请求库
- `pathlib` - 路径处理（Python 标准库）
- `typing` - 类型提示（Python 标准库）

### 环境变量
```bash
# 必需的环境变量
export ZHIPU_API_KEY="your_zhipu_api_key"        # 智谱 AI API 密钥
export GITHUB_TOKEN="your_github_token"          # GitHub Personal Access Token
```

## 安装与配置 🛠️

### 1. 克隆项目
```bash
git clone <repository_url>
cd GenBench
```

### 2. 安装依赖
```bash
pip install zai-sdk requests
```

### 3. 配置环境变量
创建 `.env` 文件或直接设置环境变量：
```bash
export ZHIPU_API_KEY="your_zhipu_api_key"
export GITHUB_TOKEN="your_github_personal_access_token"
```

## 使用指南 📖

### 步骤 1: 爬取 GitHub Issues

修改 `Scratch.py` 中的配置：
```python
REPO_OWNER = 'Microsoft'    # 仓库所有者
REPO_NAME = 'vscode'        # 仓库名称
SINCE_DATE = '2025-09-01'   # 起始日期
```

运行爬虫：
```bash
python Scratch.py
```

Issues 将按以下结构存储：
```
github_issues_output/
├── open_issues/
│   ├── bug/
│   ├── enhancement/
│   └── other/
└── closed_issues/
    ├── bug/
    ├── enhancement/
    └── other/
```

### 步骤 2: 分析 Issues 适用性

使用关键词分析：
```bash
python analyze.py --input github_issues_output --method keyword
```

使用 LLM 分析（推荐）：
```bash
python analyze.py --input github_issues_output --method llm --reference ./existbench
```

使用混合分析：
```bash
python analyze.py --input github_issues_output --method hybrid
```

### 步骤 3: 生成编程题目

确保配置文件中设置了正确的路径：
```python
BASE_DIR = 'github_issues_output'
PROBLEMS_OUTPUT_DIR = 'generated_problems'
SUITABLE_ISSUES_FILE = 'suitable_programming_issues_llm.json'
```

运行题目生成：
```bash
python generate.py
```

生成的题目将按以下结构组织：
```
generated_problems/
├── open_bug/
├── open_enhancement/
├── closed_bug/
└── closed_enhancement/
```

## 输出格式 📄

### 生成的编程题目格式

每个生成的题目包含以下结构：

```markdown
题目: [任务类型]: [Issue 标题]
source: Issue #[Issue 编号]
url: [GitHub Issue 链接]

prompt = """
[AI 生成的任务描述]
"""

AC = [
    "验收标准 1",
    "验收标准 2",
    "验收标准 3"
]
```

### 分析结果格式

分析结果保存在 JSON 文件中：
```json
{
  "metadata": {
    "generated_at": "2025-01-01 12:00:00",
    "total_issues": 100,
    "suitable_issues": 25,
    "analysis_method": "llm"
  },
  "12345": {
    "title": "Issue 标题",
    "suitable": true,
    "reason": "LLM analysis: Clear implementation task with appropriate complexity",
    "labels": ["enhancement", "feature"]
  }
}
```

## 配置选项 ⚙️

### `analyze.py` 参数
- `--input, -i`: 输入路径（文件或目录）
- `--output, -o`: 输出文件基础名称
- `--method, -m`: 分析方法（keyword/llm/hybrid）
- `--reference, -r`: 参考示例目录

### 智能分类器配置
可以在 `issue_classifier.py` 中调整：
- 关键词权重
- 排除词列表
- 分类阈值
- 置信度计算方式


## 更新日志 📋

### v0.1
- 初始版本发布
- 支持 GitHub Issues 爬取
- 实现智能分类和适用性分析
- 支持编程题目自动生成


**GenBench** - 让 GitHub Issues 变成有价值的编程练习题！ 🎯