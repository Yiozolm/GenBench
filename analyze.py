#!/usr/bin/env python3
"""
Script to analyze issues from a markdown file and identify suitable programming problems.
"""

import re
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from zai import ZhipuAiClient
from typing import List, Dict, Any
from datetime import datetime

# 加载环境变量
load_dotenv()

MODEL = os.getenv('EVAL_MODEL', 'glm-4.5-air')

def find_markdown_files(input_path: str) -> List[str]:
    """
    Recursively find all markdown files in the given path.

    Args:
        input_path: Path to search (can be file or directory)

    Returns:
        List of markdown file paths
    """
    path = Path(input_path)

    if not path.exists():
        print(f"Error: Path '{input_path}' does not exist.")
        return []

    markdown_files = []

    if path.is_file():
        # If it's a file, check if it's a markdown file
        if path.suffix.lower() in ['.md', '.markdown']:
            markdown_files.append(str(path))
        else:
            print(f"Warning: '{input_path}' is not a markdown file.")
    elif path.is_dir():
        # If it's a directory, recursively find all markdown files
        print(f"📁 Searching for markdown files in: {input_path}")

        # Search for .md and .markdown files recursively
        for md_file in path.rglob("*.md"):
            markdown_files.append(str(md_file))
        for md_file in path.rglob("*.markdown"):
            markdown_files.append(str(md_file))

        print(f"Found {len(markdown_files)} markdown files")

        if not markdown_files:
            print("No markdown files found in the specified directory.")

    return sorted(markdown_files)

def parse_markdown_files(file_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Parse issues from multiple markdown files.

    Args:
        file_paths: List of markdown file paths

    Returns:
        List of dictionaries representing issues
    """
    all_issues = []
    issue_id_counter = 1

    for file_path in file_paths:
        print(f"📖 Parsing: {os.path.basename(file_path)}")

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
            continue

        # Split content by issue headers (assuming markdown format with # ## etc.)
        # This pattern matches common markdown issue formats
        issue_pattern = r'(#{1,3}\s+(?:Issue|#\d+).*?)(?=#{1,3}\s+(?:Issue|#\d+)|\Z)'
        matches = re.findall(issue_pattern, content, re.DOTALL | re.IGNORECASE)

        if not matches:
            print(f"  ⚠️  No issues found in {os.path.basename(file_path)}")
            continue

        for match in matches:
            issue = {
                'id': issue_id_counter,
                'title': '',
                'body': match.strip(),
                'labels': [],
                'suitable': False,
                'reason': '',
                'source_file': file_path
            }

            # Extract title from first line
            lines = match.strip().split('\n')
            if lines:
                title_line = lines[0].strip()
                # Remove markdown headers
                issue['title'] = re.sub(r'^#{1,3}\s*', '', title_line).strip()

            # Try to extract labels or tags
            labels_pattern = r'(?:labels?:?\s*|tags?:?\s*)(\[.*?\]|.*?)$'
            for line in lines[:5]:  # Check first few lines for labels
                labels_match = re.search(labels_pattern, line, re.IGNORECASE)
                if labels_match:
                    labels_text = labels_match.group(1)
                    # Extract labels from brackets or comma-separated text
                    if '[' in labels_text and ']' in labels_text:
                        labels_text = labels_text[labels_text.find('[')+1:labels_text.rfind(']')]
                    issue['labels'] = [label.strip().strip('"\'') for label in labels_text.split(',') if label.strip()]

            all_issues.append(issue)
            issue_id_counter += 1

        print(f"  ✓ Found {len(matches)} issues")

    return all_issues

def load_reference_problems(reference_dir: str = "existbench") -> List[str]:
    """
    Load reference problems from existbench directory.

    Args:
        reference_dir: Directory containing reference problem files

    Returns:
        List of reference problem content strings
    """
    if not os.path.exists(reference_dir):
        print(f"⚠️  Reference directory '{reference_dir}' not found. Using generic criteria.")
        return []

    print(f"📚 Loading reference problems from: {reference_dir}")

    reference_problems = []
    markdown_files = find_markdown_files(reference_dir)

    if not markdown_files:
        print(f"⚠️  No markdown files found in '{reference_dir}'. Using generic criteria.")
        return []

    for file_path in markdown_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if content:
                    # Limit content length to avoid overly long prompts
                    if len(content) > 1500:
                        content = content[:1500] + "..."
                    reference_problems.append(f"**File: {os.path.basename(file_path)}**\n{content}")
        except Exception as e:
            print(f"  ❌ Error loading {os.path.basename(file_path)}: {e}")

    print(f"  ✓ Loaded {len(reference_problems)} reference problems")
    return reference_problems

def parse_markdown_issues(input_path: str) -> List[Dict[str, Any]]:
    """
    Parse issues from a markdown file or directory.

    Args:
        input_path: Path to file or directory containing markdown files

    Returns:
        List of dictionaries representing issues
    """
    # Find all markdown files
    markdown_files = find_markdown_files(input_path)

    if not markdown_files:
        return []

    # Parse all files
    return parse_markdown_files(markdown_files)

def is_suitable_programming_issue(issue: Dict[str, Any]) -> tuple[bool, str]:
    """
    Determine if an issue is suitable as a programming problem.

    Args:
        issue: Dictionary containing issue information

    Returns:
        Tuple of (is_suitable, reason)
    """
    title = issue.get('title', '').lower()
    body = issue.get('body', '').lower()
    labels = [label.lower() for label in issue.get('labels', [])]

    # Positive indicators - these suggest good programming problems
    positive_keywords = [
        'implement', 'add', 'create', 'build', 'develop', 'feature', 'enhancement',
        'optimization', 'refactor', 'improve', 'extend', 'integrate', 'support',
        'algorithm', 'function', 'method', 'class', 'module', 'component',
        'performance', 'efficiency', 'speed', 'memory', 'cache', 'optimize'
    ]

    # Negative indicators - these suggest issues NOT suitable as programming problems
    negative_keywords = [
        'typo', 'spelling', 'grammar', 'format', 'style', 'lint', 'cleanup',
        'deprecated', 'remove', 'delete', 'security', 'vulnerability', 'hack',
        'workaround', 'temporary', 'patch', 'hotfix', 'urgent', 'critical',
        'broken build', 'missing import', 'syntax error'
    ]

    # Cross-platform indicators - these suggest issues NOT suitable for fixed Docker environment
    cross_platform_keywords = [
        'cross-platform', 'cross platform', 'platform independent', 'multiplatform',
        'windows', 'macos', 'mac os', 'linux', 'ubuntu', 'debian', 'centos',
        'ios', 'android', 'web', 'browser', 'chrome', 'firefox', 'safari',
        'compatibility', 'portable', 'mobile', 'desktop', 'native',
        'operating system', 'os-specific', 'platform-specific'
    ]

    # Potentially suitable bug-related indicators
    moderate_bug_keywords = [
        'algorithm', 'performance', 'optimization', 'logic', 'calculation',
        'rendering', 'display', 'interaction', 'behavior', 'refactor'
    ]

    # Labels that indicate good programming problems
    positive_labels = [
        'enhancement', 'feature', 'good first issue', 'help wanted', 'performance',
        'optimization', 'refactor', 'algorithm', 'implementation'
    ]

    # Labels that indicate bad programming problems
    negative_labels = [
        'bug', 'documentation', 'maintenance', 'security', 'cleanup', 'chore',
        'wontfix', 'duplicate', 'question', 'discussion'
    ]

    # Check for strong negative indicators first
    for keyword in negative_keywords:
        if keyword in title[:100]:  # Check first 100 chars of title
            return False, f"Contains negative keyword: '{keyword}'"

    # Check for cross-platform indicators (not suitable for fixed Docker environment)
    for keyword in cross_platform_keywords:
        if keyword in title.lower() or keyword in body[:500].lower():
            return False, f"Cross-platform issue not suitable for fixed environment: '{keyword}'"

    # Check negative labels
    for label in negative_labels:
        if label in labels:
            return False, f"Has negative label: '{label}'"

    # Check for strong positive indicators
    has_positive_keyword = any(keyword in title or keyword in body[:500]
                              for keyword in positive_keywords)
    has_positive_label = any(label in labels for label in positive_labels)

    # Check if it's a specific, implementable feature
    specific_patterns = [
        r'implement\s+\w+', r'add\s+\w+\s+support', r'create\s+\w+',
        r'build\s+\w+', r'develop\s+\w+', r'integrate\s+\w+'
    ]
    has_specific_pattern = any(re.search(pattern, title, re.IGNORECASE)
                              for pattern in specific_patterns)

    # Check for complexity indicators (good for programming problems)
    complexity_indicators = [
        'algorithm', 'data structure', 'optimization', 'performance', 'efficiency',
        'scaling', 'memory', 'cpu', 'cache', 'parallel', 'async', 'concurrent'
    ]
    has_complexity = any(indicator in body.lower() for indicator in complexity_indicators)

    # Check for moderate bug fix potential
    has_moderate_bug = any(keyword in title.lower() or keyword in body[:500].lower()
                         for keyword in moderate_bug_keywords)

    # Bug-related patterns that suggest educational value
    bug_patterns = [
        r'fix\s+(?:algorithm|logic|calculation|performance)',
        r'resolve\s+(?:performance|memory|rendering)',
        r'correct\s+(?:behavior|logic|calculation)',
        r'improve\s+(?:performance|efficiency|algorithm)'
    ]
    has_bug_pattern = any(re.search(pattern, title.lower(), re.IGNORECASE)
                         for pattern in bug_patterns)

    # Determine suitability
    if has_positive_label or has_positive_keyword or has_specific_pattern:
        if has_complexity:
            return True, "Complex implementation challenge with good learning value"
        else:
            return True, "Clear implementation task suitable for programming exercise"
    elif has_moderate_bug or has_bug_pattern:
        # Bug fixes with educational complexity
        return True, "Moderate bug fix with good learning value"
    elif len(title) > 20 and not any(neg in title for neg in negative_keywords):
        # Longer titles might indicate substantial features
        return True, "Substantial request based on title length and content"
    else:
        return False, "Lacks clear implementation requirements or learning value"

def is_suitable_programming_issue_llm(issue: Dict[str, Any], client: ZhipuAiClient, reference_problems: List[str] = None) -> tuple[bool, str]:
    """
    Use LLM to determine if an issue is suitable as a programming problem.

    Args:
        issue: Dictionary containing issue information
        client: ZhipuAiClient instance for making API calls
        reference_problems: List of reference problem examples

    Returns:
        Tuple of (is_suitable, reason)
    """
    title = issue.get('title', '')
    body = issue.get('body', '')
    labels = issue.get('labels', [])

    # Build system prompt with reference examples and criteria
    system_prompt = """You are an expert evaluator of programming exercises and challenges. Your task is to analyze GitHub issues and determine if they would be suitable as programming problems for educational purposes.

"""

    # Add reference examples if available
    if reference_problems:
        system_prompt += f"""REFERENCE EXAMPLES - Use these as benchmarks for suitable programming problems:

{chr(10).join(reference_problems[:3])}  # Limit to 3 examples to avoid overly long prompts

Based on these reference examples, evaluate whether new issues match the desired complexity and educational value.

"""

    system_prompt += """CRITERIA FOR SUITABILITY:
- Should involve implementing new functionality, features, or algorithms
- Should have clear requirements and goals
- Should be educational and provide learning value
- For bug fixes: should be moderate complexity fixes that provide learning opportunities
  • Acceptable: algorithm bugs, logic errors, performance issues, UI/UX improvements
  • Not acceptable: simple typo fixes, urgent security patches, trivial configuration changes
- Should have complexity similar to the reference examples (if provided)
- Should be challenging but achievable for programming practice
- **IMPORTANT: Should NOT involve cross-platform compatibility issues (fixed Docker environment)**

ENVIRONMENT CONSTRAINTS:
- All programming problems will be solved in a fixed Docker environment
- Issues requiring cross-platform compatibility, OS-specific features, or multiple platform support are NOT suitable
- Focus on core functionality, algorithms, and logic rather than platform integration

BUG FIX COMPLEXITY GUIDELINES:
✓ Suitable bug fixes: algorithm implementation errors, performance bottlenecks, UI interaction bugs, data structure bugs, moderate refactoring needs
✗ Unsuitable bug fixes: syntax errors, typos, missing imports, urgent security vulnerabilities, broken builds, simple CSS fixes

CROSS-PLATFORM EXCLUSIONS:
✗ Not suitable: Windows/Mac/Linux compatibility, browser compatibility, mobile/desktop differences, OS-specific APIs, platform-specific UI, multi-environment deployment

Please respond with exactly one line in the format:
SUITABLE: [true/false] - [brief reason]

Examples of good responses:
SUITABLE: true - Clear implementation task with appropriate complexity
SUITABLE: false - Simple typo fix in documentation
SUITABLE: true - Algorithm optimization problem matching reference difficulty
SUITABLE: true - Moderate bug fix with educational value
SUITABLE: false - Critical security bug requiring immediate patch
SUITABLE: false - Cross-platform compatibility issue
SUITABLE: false - Platform-specific implementation
SUITABLE: false - Simple typo or syntax error fix
"""

    # Build user prompt with the specific issue
    user_prompt = f"""Please analyze this GitHub issue and determine if it would be suitable as a programming exercise/challenge.

**Issue Title:** {title}

**Labels:** {', '.join(labels) if labels else 'None'}

**Description:**
{body[:2000]}...

Based on the criteria and reference examples provided, is this issue suitable as a programming problem?"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        )

        response_content = response.choices[0].message.content.strip()

        # Parse the response to extract suitability and reason
        # Look for the SUITABLE pattern
        import re
        match = re.search(r'SUITABLE:\s*(true|false)\s*-\s*(.+)', response_content, re.IGNORECASE)

        if match:
            is_suitable = match.group(1).lower() == 'true'
            reason = match.group(2).strip()
            return is_suitable, f"LLM analysis: {reason}"
        else:
            # Try to extract a boolean answer from anywhere in the response
            if any(word in response_content.lower() for word in ['true', 'suitable', 'yes', 'good']):
                return True, f"LLM assessment: {response_content[:100]}..."
            else:
                return False, f"LLM assessment: {response_content[:100]}..."

    except Exception as e:
        print(f"Warning: LLM analysis failed: {e}")
        return False, f"LLM analysis error: {str(e)}"

def analyze_issues_with_llm(issues: List[Dict[str, Any]], reference_dir: str = "./existbench", output_file: str = "suitable_programming_issues_llm.json") -> List[Dict[str, Any]]:
    """
    Analyze issues using LLM and mark suitable programming problems.
    Skips issues that have already been analyzed.

    Args:
        issues: List of issue dictionaries
        reference_dir: Directory containing reference problem examples
        output_file: JSON file to check for existing analysis

    Returns:
        List of issues with suitability information added
    """
    suitable_issues = []

    # Load existing analysis to skip already analyzed issues
    existing_data = load_existing_analysis(output_file)

    # Filter out already analyzed issues
    unanalyzed_issues = []
    skipped_count = 0

    for issue in issues:
        if is_issue_analyzed(issue['id'], existing_data):
            # Restore existing analysis data
            existing_issue_data = existing_data[str(issue['id'])]
            issue['suitable'] = existing_issue_data.get('suitable', False)
            issue['reason'] = existing_issue_data.get('reason', '')

            if issue['suitable']:
                suitable_issues.append(issue)
            skipped_count += 1
        else:
            unanalyzed_issues.append(issue)

    if skipped_count > 0:
        print(f"⏭️  Skipped {skipped_count} already analyzed issues")

    if not unanalyzed_issues:
        print("✅ All issues have been analyzed already")
        return suitable_issues

    print("🤖 Using LLM to analyze new issues...")
    print("Model: GLM-4.5-air")
    print(f"New issues to analyze: {len(unanalyzed_issues)}")
    print()

    # Load reference problems
    reference_problems = load_reference_problems(reference_dir)

    # Initialize the client
    api_key = os.getenv('ZHIPU_API_KEY')
    if not api_key:
        print("错误: 请在 .env 文件中设置 ZHIPU_API_KEY！")
        return suitable_issues

    client = ZhipuAiClient(api_key=api_key)

    for i, issue in enumerate(unanalyzed_issues, 1):
        print(f"Analyzing issue {i}/{len(unanalyzed_issues)}: {issue['title'][:50]}...")

        is_suitable, reason = is_suitable_programming_issue_llm(issue, client, reference_problems)
        issue['suitable'] = is_suitable
        issue['reason'] = reason

        if is_suitable:
            suitable_issues.append(issue)
            print(f"  ✓ Suitable: {reason}")
        else:
            print(f"  ✗ Not suitable: {reason}")
        print()

    return suitable_issues

def analyze_issues(issues: List[Dict[str, Any]], output_file: str = "suitable_programming_issues.json") -> List[Dict[str, Any]]:
    """
    Analyze issues and mark suitable programming problems.
    Skips issues that have already been analyzed.

    Args:
        issues: List of issue dictionaries
        output_file: JSON file to check for existing analysis

    Returns:
        List of issues with suitability information added
    """
    suitable_issues = []

    # Load existing analysis to skip already analyzed issues
    existing_data = load_existing_analysis(output_file)

    # Filter out already analyzed issues
    unanalyzed_issues = []
    skipped_count = 0

    for issue in issues:
        if is_issue_analyzed(issue['id'], existing_data):
            # Restore existing analysis data
            existing_issue_data = existing_data[str(issue['id'])]
            issue['suitable'] = existing_issue_data.get('suitable', False)
            issue['reason'] = existing_issue_data.get('reason', '')

            if issue['suitable']:
                suitable_issues.append(issue)
            skipped_count += 1
        else:
            unanalyzed_issues.append(issue)

    if skipped_count > 0:
        print(f"⏭️  Skipped {skipped_count} already analyzed issues")

    if not unanalyzed_issues:
        print("✅ All issues have been analyzed already")
        return suitable_issues

    print("🔤 Analyzing new issues with keyword-based method...")
    print(f"New issues to analyze: {len(unanalyzed_issues)}")
    print()

    for issue in unanalyzed_issues:
        is_suitable, reason = is_suitable_programming_issue(issue)
        issue['suitable'] = is_suitable
        issue['reason'] = reason

        if is_suitable:
            suitable_issues.append(issue)
            print(f"✓ Suitable: {issue['title'][:50]}...")
        else:
            print(f"✗ Not suitable: {issue['title'][:50]}... ({reason})")

    return suitable_issues

def load_existing_analysis(json_file: str) -> Dict[str, Any]:
    """
    Load existing analysis results from JSON file.

    Args:
        json_file: Path to the JSON file containing previous analysis results

    Returns:
        Dictionary containing existing analysis results, or empty dict if file doesn't exist
    """
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"📂 Loaded existing analysis from {json_file}")
            metadata = existing_data.get('metadata', {})
            print(f"  Previous analysis: {metadata.get('total_issues', 0)} issues, {metadata.get('suitable_issues', 0)} suitable")
            return existing_data
        except Exception as e:
            print(f"⚠️  Error loading existing analysis: {e}")
            return {}
    else:
        print("📄 No existing analysis file found, starting fresh")
        return {}

def is_issue_analyzed(issue_id: int, existing_data: Dict[str, Any]) -> bool:
    """
    Check if an issue has already been analyzed.

    Args:
        issue_id: The ID of the issue to check
        existing_data: Dictionary containing existing analysis results

    Returns:
        True if the issue has been analyzed, False otherwise
    """
    return str(issue_id) in existing_data and 'metadata' not in existing_data[str(issue_id)]

def save_issues_analysis(all_issues: List[Dict[str, Any]], output_file: str, analysis_method: str):
    """
    Save all issues analysis results to a JSON file with ID as key.
    Merges with existing data instead of overwriting.

    Args:
        all_issues: List of all issue dictionaries (both suitable and unsuitable)
        output_file: Base name for output file
        analysis_method: The method used for analysis ('keyword', 'llm', 'hybrid')
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    json_file = f"{output_file}.json"

    # Load existing data
    existing_data = load_existing_analysis(json_file)

    # Create new results structure
    results = {
        'metadata': {
            'generated_at': timestamp,
            'total_issues': len(all_issues),
            'suitable_issues': len([issue for issue in all_issues if issue.get('suitable', False)]),
            'analysis_method': analysis_method,
            'updated_issues': 0
        }
    }

    # Count new/updated issues
    updated_count = 0

    # Merge existing non-metadata entries and update with new analysis
    for key, value in existing_data.items():
        if key != 'metadata':
            results[key] = value

    # Add or update issues with ID as key
    for issue in all_issues:
        issue_id = str(issue['id'])
        issue_data = {
            'title': issue.get('title', ''),
            'suitable': issue.get('suitable', False),
            'reason': issue.get('reason', ''),
            'labels': issue.get('labels', [])
        }

        # Check if this is a new or updated issue
        if issue_id not in existing_data or existing_data[issue_id] != issue_data:
            updated_count += 1

        results[issue_id] = issue_data

    # Update metadata with actual counts from merged data
    total_issues = len([k for k in results.keys() if k.isdigit()])
    suitable_issues = len([v for k, v in results.items() if k.isdigit() and v.get('suitable', False)])

    results['metadata']['total_issues'] = total_issues
    results['metadata']['suitable_issues'] = suitable_issues
    results['metadata']['updated_issues'] = updated_count

    # Save as JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Saved analysis results to:")
    print(f"  JSON: {json_file}")
    print(f"  Total issues: {total_issues}")
    print(f"  Suitable issues: {suitable_issues}")
    print(f"  Updated in this run: {updated_count}")
    print(f"  Format: issue_id -> {{title, suitable, reason, labels}}")

def main():
    """Main function to run the issue analysis."""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze GitHub issues for suitable programming problems')
    parser.add_argument('--input', '-i', default='issues.md', help='Input markdown file or directory containing issues')
    parser.add_argument('--output', '-o', default='suitable_programming_issues', help='Base name for output files')
    parser.add_argument('--method', '-m', choices=['keyword', 'llm', 'hybrid'], default='keyword',
                       help='Analysis method: keyword (rule-based), llm (AI-based), or hybrid (both)')
    parser.add_argument('--reference', '-r', default='./existbench',
                       help='Directory containing reference problem examples for LLM analysis')

    args = parser.parse_args()

    print("🔍 Analyzing issues...")
    print(f"Input path: {args.input}")
    print(f"Analysis method: {args.method}")
    print()

    # Parse issues from markdown file(s) or directory
    issues = parse_markdown_issues(args.input)

    if not issues:
        print("No issues found in the input path.")
        return

    print(f"Found {len(issues)} total issues\n")

    # Determine output file names based on method
    if args.method == 'llm':
        output_base = f"{args.output}_llm"
        json_file = f"{output_base}.json"
    elif args.method == 'hybrid':
        output_base = f"{args.output}_hybrid"
        json_file = f"{output_base}.json"
    else:  # keyword method (default)
        output_base = args.output
        json_file = f"{output_base}.json"

    # Analyze and find suitable programming issues
    if args.method == 'llm':
        suitable_issues = analyze_issues_with_llm(issues, args.reference, json_file)
    elif args.method == 'hybrid':
        # First pass with keyword analysis
        print("🔤 First pass: Keyword-based analysis...")
        keyword_suitable = analyze_issues(issues, f"{args.output}.json")

        # Second pass with LLM for ambiguous cases
        ambiguous_issues = [issue for issue in issues if not issue.get('suitable', False)]
        if ambiguous_issues:
            print(f"\n🤖 Second pass: LLM analysis for {len(ambiguous_issues)} ambiguous issues...")
            llm_suitable = analyze_issues_with_llm(ambiguous_issues, args.reference, f"{args.output}_llm.json")

            # Combine results
            suitable_issues = keyword_suitable + llm_suitable
        else:
            suitable_issues = keyword_suitable
    else:  # keyword method (default)
        suitable_issues = analyze_issues(issues, json_file)

    print(f"\n📊 Analysis complete!")
    print(f"Total issues found: {len(issues)}")

    # Count total analyzed issues (including previously analyzed)
    if os.path.exists(json_file):
        existing_data = load_existing_analysis(json_file)
        total_analyzed = len([k for k in existing_data.keys() if k.isdigit()])
    else:
        total_analyzed = len([issue for issue in issues if 'suitable' in issue])

    print(f"Issues with analysis: {total_analyzed}")
    print(f"Suitable programming issues: {len(suitable_issues)}")

    if total_analyzed > 0:
        print(f"Percentage suitable: {len(suitable_issues)/total_analyzed*100:.1f}%")

    print(f"Analysis method: {args.method}")

    # Save all issues analysis results
    save_issues_analysis(issues, output_base, args.method)

if __name__ == "__main__":
    main()