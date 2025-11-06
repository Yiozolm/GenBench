#!/bin/bash

# GenBench 环境设置脚本
# 使用 uv 管理 Python 环境

set -e

echo "🚀 设置 GenBench 开发环境..."

# 检查是否安装了 uv
if ! command -v uv &> /dev/null; then
    echo "❌ 未找到 uv，正在安装..."
    # macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    # Linux
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    else
        echo "❌ 不支持的操作系统，请手动安装 uv: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi

    # 重新加载 PATH
    export PATH="$HOME/.cargo/bin:$PATH"

    # 检查安装是否成功
    if ! command -v uv &> /dev/null; then
        echo "❌ uv 安装失败，请手动安装"
        exit 1
    fi
fi

echo "✅ uv 已安装: $(uv --version)"

# 创建虚拟环境
echo "📦 创建 Python 虚拟环境..."
uv venv

# 激活虚拟环境（在脚本中主要用于后续命令）
source .venv/bin/activate

# 安装依赖
echo "📥 安装项目依赖..."
uv pip install -e .

# 安装开发依赖（可选）
read -p "是否安装开发依赖？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🛠️ 安装开发依赖..."
    uv pip install -e ".[dev]"
fi

# 复制环境变量模板
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件，填入您的 API 密钥："
    echo "   - GITHUB_TOKEN: GitHub Personal Access Token"
    echo "   - ZHIPU_API_KEY: 智谱 AI API 密钥"
else
    echo "✅ 环境变量文件已存在"
fi

# 创建必要的目录
echo "📁 创建输出目录..."

# 加载环境变量
if [ -f .env ]; then
    # 安全地加载环境变量，忽略注释和空行
    while IFS= read -r line; do
        # 跳过注释和空行
        [[ $line =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue

        # 导出有效的环境变量
        if [[ $line == *"="* ]]; then
            export "$line"
        fi
    done < .env
fi

# 获取配置的目录名
BASE_DIR="${BASE_OUTPUT_DIR:-github_issues_output}"
PROBLEMS_DIR="${PROBLEMS_OUTPUT_DIR:-generated_problems}"

echo "   - Issues 输出目录: $BASE_DIR"
echo "   - 题目输出目录: $PROBLEMS_DIR"

# 创建 Issues 输出目录结构
mkdir -p "$BASE_DIR"/{open_issues,closed_issues}/{bug,enhancement,other}

# 创建题目输出目录结构
mkdir -p "$PROBLEMS_DIR"/{open_bug,open_enhancement,closed_bug,closed_enhancement}

echo ""
echo "🎉 环境设置完成！"
echo ""
echo "📋 下一步操作："
echo "1. 编辑 .env 文件，填入 API 密钥"
echo "2. 激活虚拟环境: source .venv/bin/activate"
echo "3. 运行脚本: uv run python Scratch.py"
echo ""
echo "💡 使用 'uv run python <script>' 运行脚本，无需手动激活环境"