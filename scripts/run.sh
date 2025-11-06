#!/bin/bash

# GenBench 运行脚本
# 使用 uv 运行各种工具

set -e

SCRIPT_NAME="$(basename "$0")"

show_usage() {
    echo "GenBench 运行脚本"
    echo ""
    echo "用法: $0 <command> [options]"
    echo ""
    echo "命令:"
    echo "  crawl      - 爬取 GitHub Issues"
    echo "  analyze    - 分析 Issues 适用性"
    echo "  generate   - 生成编程题目"
    echo "  full       - 完整流程 (crawl -> analyze -> generate)"
    echo "  setup      - 设置开发环境"
    echo "  test       - 运行测试"
    echo "  lint       - 代码检查"
    echo "  format     - 代码格式化"
    echo ""
    echo "选项:"
    echo "  --method   - 分析方法 (keyword/llm/hybrid)"
    echo "  --input    - 输入路径"
    echo "  --output   - 输出路径"
    echo ""
    echo "示例:"
    echo "  $0 crawl"
    echo "  $0 analyze --method llm"
    echo "  $0 full --method hybrid"
    echo "  $0 setup"
}

check_env() {
    if [ ! -f .env ]; then
        echo "❌ 未找到 .env 文件，请先运行: $0 setup"
        exit 1
    fi

    # 检查必要的环境变量
    source .env

    if [ -z "$GITHUB_TOKEN" ] || [ "$GITHUB_TOKEN" = "your_github_personal_access_token_here" ]; then
        echo "❌ 请在 .env 文件中设置有效的 GITHUB_TOKEN"
        exit 1
    fi

    if [ -z "$ZHIPU_API_KEY" ] || [ "$ZHIPU_API_KEY" = "your_zhipu_api_key_here" ]; then
        echo "❌ 请在 .env 文件中设置有效的 ZHIPU_API_KEY"
        exit 1
    fi
}

run_crawl() {
    echo "🕷️ 开始爬取 GitHub Issues..."
    check_env
    uv run python Scratch.py
}

run_analyze() {
    local method="llm"
    local input="github_issues_output"
    local output="suitable_programming_issues"

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --method)
                method="$2"
                shift 2
                ;;
            --input)
                input="$2"
                shift 2
                ;;
            --output)
                output="$2"
                shift 2
                ;;
            *)
                echo "❌ 未知参数: $1"
                exit 1
                ;;
        esac
    done

    echo "🔍 开始分析 Issues 适用性..."
    echo "   方法: $method"
    echo "   输入: $input"
    echo "   输出: $output"

    check_env
    uv run python analyze.py --input "$input" --method "$method" --output "$output"
}

run_generate() {
    echo "📝 开始生成编程题目..."
    check_env
    uv run python generate.py
}

run_full() {
    local method="llm"

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --method)
                method="$2"
                shift 2
                ;;
            *)
                echo "❌ 未知参数: $1"
                exit 1
                ;;
        esac
    done

    echo "🚀 开始完整流程..."
    echo "   分析方法: $method"
    echo ""

    run_crawl
    echo ""
    run_analyze --method "$method"
    echo ""
    run_generate

    echo ""
    echo "🎉 完整流程执行完毕！"
}

run_setup() {
    echo "⚙️ 设置开发环境..."
    if [ -f scripts/setup.sh ]; then
        chmod +x scripts/setup.sh
        ./scripts/setup.sh
    else
        echo "❌ 未找到 setup.sh 脚本"
        exit 1
    fi
}

run_test() {
    echo "🧪 运行测试..."
    if uv pip list | grep -q pytest; then
        uv run pytest
    else
        echo "❌ 未安装 pytest，请先运行: $0 setup"
        exit 1
    fi
}

run_lint() {
    echo "🔍 代码检查..."
    if uv pip list | grep -q ruff; then
        uv run ruff check .
    else
        echo "❌ 未安装 ruff，请先运行: $0 setup"
        exit 1
    fi
}

run_format() {
    echo "✨ 代码格式化..."
    if uv pip list | grep -q black; then
        uv run black .
        uv run ruff check --fix .
    else
        echo "❌ 未安装 black/ruff，请先运行: $0 setup"
        exit 1
    fi
}

# 主逻辑
case "${1:-}" in
    crawl)
        run_crawl
        ;;
    analyze)
        shift
        run_analyze "$@"
        ;;
    generate)
        run_generate
        ;;
    full)
        shift
        run_full "$@"
        ;;
    setup)
        run_setup
        ;;
    test)
        run_test
        ;;
    lint)
        run_lint
        ;;
    format)
        run_format
        ;;
    --help|-h)
        show_usage
        ;;
    "")
        show_usage
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac