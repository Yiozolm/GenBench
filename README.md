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
├── pyproject.toml               # 项目配置和依赖管理
├── .env.example                 # 环境变量模板
├── analyze.py                   # Issue 分析工具
├── generate.py                  # 编程题目生成工具
├── issue_classifier.py          # Issue 分类器
├── Scratch.py                   # GitHub Issues 爬取工具
├── scripts/                     # 工具脚本目录
│   ├── setup.sh                # 环境初始化脚本
│   ├── run.sh                  # 便捷运行脚本
│   └── Makefile                # Make 构建文件
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

### 系统要求
- Python 3.8+
- [uv](https://docs.astral.sh/uv/) - 现代化的 Python 包管理器

### Python 包依赖
- `zai-sdk>=0.0.4` - 智谱 AI SDK
- `requests>=2.32.3` - HTTP 请求库
- `python-dotenv>=1.0.0` - 环境变量管理

### 开发依赖（可选）
- `black` - 代码格式化
- `ruff` - 代码检查和格式化
- `mypy` - 静态类型检查
- `pytest` - 测试框架

## 安装与配置 🛠️

### 方法一：使用 uv（推荐）

#### 1. 安装 uv
```bash
# macOS 和 Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 其他系统请参考：https://docs.astral.sh/uv/getting-started/installation/
```

#### 2. 克隆项目
```bash
git clone <repository_url>
cd GenBench
```

#### 3. 自动环境设置
```bash
# 使用自动设置脚本
chmod +x scripts/setup.sh
./scripts/setup.sh

# 或手动设置
uv venv                    # 创建虚拟环境
uv pip install -e .       # 安装生产依赖
uv pip install -e ".[dev]" # 安装开发依赖（可选）
cp .env.example .env       # 复制环境变量模板
```

**注意**：`setup.sh` 脚本会：
- 自动创建虚拟环境
- 安装所有依赖
- 根据 `.env` 文件中的配置创建输出目录
- 复制环境变量模板

#### 4. 配置环境变量
编辑 `.env` 文件：
```bash
# GitHub API 配置
GITHUB_TOKEN=your_github_personal_access_token_here

# 智谱 AI 配置
ZHIPU_API_KEY=your_zhipu_api_key_here

# 仓库配置
REPO_OWNER=Microsoft
REPO_NAME=vscode
SINCE_DATE=2025-09-01

# AI 模型配置
EVAL_MODEL=glm-4.5-air  # 用于分析 Issues 的模型
GEN_MODEL=glm-4.6        # 用于生成题目的模型

# 输出目录配置
BASE_OUTPUT_DIR=github_issues_output
PROBLEMS_OUTPUT_DIR=generated_problems
SUITABLE_ISSUES_FILE=suitable_programming_issues_llm.json
```

### 方法二：传统 pip 安装

```bash
# 1. 克隆项目
git clone <repository_url>
cd GenBench

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt  # 如果存在
# 或手动安装
pip install zai-sdk requests python-dotenv

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件填入 API 密钥
```

## 使用指南 📖

### 快速开始（推荐方式）

使用便捷脚本，自动处理环境变量和依赖：

```bash
# 1. 环境设置（仅需一次）
./scripts/setup.sh

# 2. 运行完整流程
./scripts/run.sh full --method llm

# 3. 或单独运行各个步骤
./scripts/run.sh crawl                    # 爬取 Issues
./scripts/run.sh analyze --method llm     # 分析 Issues
./scripts/run.sh generate                 # 生成题目
```


### 使用 uv 直接运行

```bash
# 1. 爬取 GitHub Issues
uv run python Scratch.py

# 2. 分析 Issues 适用性
uv run python analyze.py --input github_issues_output --method llm

# 3. 生成编程题目
uv run python generate.py
```

### 传统方式（激活虚拟环境）

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行脚本
python Scratch.py
python analyze.py --input github_issues_output --method llm
python generate.py
```

### 步骤 1: 爬取 GitHub Issues

在 `.env` 文件中配置仓库信息（可选，有默认值）：
```bash
REPO_OWNER=Microsoft    # 仓库所有者
REPO_NAME=vscode        # 仓库名称
SINCE_DATE=2025-09-01   # 起始日期
```

运行爬虫：
```bash
# 使用便捷脚本
./scripts/run.sh crawl

# 或直接运行
uv run python Scratch.py
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
./scripts/run.sh analyze --method keyword
```

使用 LLM 分析（推荐）：
```bash
./scripts/run.sh analyze --method llm
```

使用混合分析：
```bash
./scripts/run.sh analyze --method hybrid
```


### 步骤 3: 生成编程题目

确保 `.env` 文件中配置了正确的路径（可选，有默认值）：
```bash
# 输出目录配置
BASE_OUTPUT_DIR=github_issues_output
PROBLEMS_OUTPUT_DIR=generated_problems
SUITABLE_ISSUES_FILE=suitable_programming_issues_llm.json

# AI 模型配置
GEN_MODEL=glm-4.6  # 用于生成题目的模型
```

运行题目生成：
```bash
./scripts/run.sh generate
# 或
uv run python generate.py
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

## 环境变量配置 ⚙️

### 必需配置
```bash
# GitHub API 访问令牌
GITHUB_TOKEN=your_github_personal_access_token

# 智谱 AI API 密钥
ZHIPU_API_KEY=your_zhipu_api_key
```

### 仓库配置
```bash
REPO_OWNER=Microsoft          # 仓库所有者
REPO_NAME=vscode              # 仓库名称
SINCE_DATE=2025-09-01         # 爬取起始日期
```

### AI 模型配置
```bash
EVAL_MODEL=glm-4.5-air        # 分析 Issues 使用的模型
GEN_MODEL=glm-4.6             # 生成题目使用的模型
```

### 输出目录配置
```bash
BASE_OUTPUT_DIR=github_issues_output                    # Issues 输出目录
PROBLEMS_OUTPUT_DIR=generated_problems                  # 题目输出目录
SUITABLE_ISSUES_FILE=suitable_programming_issues_llm.json # 分析结果文件
REFERENCE_DIR=./existbench                              # 参考示例目录
```

## 开发指南 🛠️

### 环境管理
```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 运行测试
uv run pytest

# 代码检查
uv run ruff check .
uv run mypy .

# 代码格式化
uv run black .
uv run ruff check --fix .
```

### 项目结构说明
- `pyproject.toml`: 项目配置、依赖管理和工具配置
- `.env.example`: 环境变量模板
- `scripts/`: 便捷脚本目录
  - `setup.sh`: 一键环境初始化
  - `run.sh`: 统一的任务运行脚本

### 代码规范
项目使用以下工具保证代码质量：
- **Black**: 代码格式化
- **Ruff**: 快速的 Python linter 和 formatter
- **MyPy**: 静态类型检查
- **pytest**: 测试框架

### 配置文件管理
- 所有配置项都通过环境变量管理，支持 `.env` 文件
- 无需修改代码即可调整所有参数
- 支持不同环境使用不同的配置

### 添加新功能
1. 在 `pyproject.toml` 中添加新的依赖
2. 在相应的 Python 文件中使用 `os.getenv()` 获取新配置
3. 在 `.env.example` 中添加新的配置项模板
4. 更新 README.md 中的配置说明
5. 添加测试用例
6. 更新 CHANGELOG

## 更新日志 📋

### v0.2.0
- ✨ 现代化环境管理：全面采用 uv 和 pyproject.toml
- ✨ 环境变量配置：所有硬编码常量改为环境变量管理
- ✨ 分离 AI 模型配置：EVAL_MODEL 和 GEN_MODEL 独立配置
- ✨ 便捷脚本工具：提供 setup.sh 和 run.sh 自动化脚本
- ✨ 灵活的配置管理：支持 .env 文件和默认值
- 🛠️ 智能目录创建：setup.sh 根据用户配置自动创建输出目录

### v0.1.0
- ✨ 初始版本发布
- ✨ 支持 GitHub Issues 爬取
- ✨ 实现智能分类和适用性分析
- ✨ 支持编程题目自动生成


**GenBench** - 让 GitHub Issues 变成有价值的编程练习题！ 🎯