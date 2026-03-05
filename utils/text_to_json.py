import json
import os
import re


#来自output_utils.py
def convert_text_to_json(text):
    # 1. Initial global text cleaning
    # First remove any complete [Data: Reports...] patterns
    text = re.sub(r'\[Data:.*?\]', '', text)
    # Also remove any partial Data: Reports references
    text = re.sub(r'\[Data:[^\]]*', '', text)

    # 2. Extract analyst information from reports
    report_pattern = re.compile(
        r'Analyst Report (\d+) from Analyst (\d+) \(Importance Score: (\d+)\)\*\*: (.*?)(?=\n|$)')
    reports = []

    for match in report_pattern.finditer(text):
        report_id = int(match.group(1))
        importance_score = int(match.group(3))
        content = match.group(4).strip()
        # Clean content
        content = clean_text(content)

        reports.append({
            "id": report_id,
            "importance_score": importance_score,
            "content": content
        })

    # 3. Extract analysis evaluations
    eval_pattern = re.compile(r'Analyst Report (\d+) from Analyst (\d+)\*\* (.*?)(?=\n|$)')
    evaluations = []

    for match in eval_pattern.finditer(text):
        report_id = int(match.group(1))
        content = match.group(3).strip()
        # Clean content
        content = clean_text(content)

        evaluations.append({
            "id": report_id,
            "content": content
        })

    # 4. Extract consistency points
    consistency_section = re.search(r'Consistency and Corroboration:(.*?)(?=####|\Z)', text, re.DOTALL)
    consistency_points = []

    if consistency_section:
        consistency_text = consistency_section.group(1).strip()
        for line in consistency_text.split('\n'):
            line = line.strip()
            if line and line.startswith('-'):
                point = line[1:].strip()
                if point.endswith('...'):
                    point = point[:-3].strip()
                # Clean text
                point = clean_text(point)
                if point and not point == '**' and not point.startswith('**') and not point.endswith('**'):
                    consistency_points.append(point)

    # 5. Extract evidence points
    evidence_section = re.search(r'Supporting Evidence:(.*?)(?=###|\Z)', text, re.DOTALL)
    evidence_points = []

    if evidence_section:
        evidence_text = evidence_section.group(1).strip()
        evidence_lines = evidence_text.split('\n')
        for line in evidence_lines:
            if re.match(r'^\d+\.', line.strip()):
                cleaned_evidence = re.sub(r'^\d+\.\s*', '', line).strip()
                cleaned_evidence = re.sub(r'\[Analyst Report \d+(?:, Analyst Report \d+)*\]', '', cleaned_evidence)
                cleaned_evidence = clean_text(cleaned_evidence)
                cleaned_evidence = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_evidence)
                if cleaned_evidence:
                    evidence_points.append(cleaned_evidence)

    # Combine evidence points into a single string with newline separators
    evidence_string = '\n'.join(evidence_points)

    # 6. Extract final judgment
    # Modified to handle Chinese characters and multiple languages
    final_judgment_match = re.search(r'The NEWS \(\*\*(.*?)\*\*\) is \*\*(.*?)\*\*', text)
    if not final_judgment_match:
        # Try another pattern that might match non-English judgments
        final_judgment_match = re.search(r'[Tt]he NEWS \((?:\*\*)?(.*?)(?:\*\*)?\) is (?:\*\*)?(.*?)(?:\*\*)?\.', text)

    final_judgment = ""
    if final_judgment_match:
        verdict = final_judgment_match.group(2).strip()
        final_judgment = verdict
    else:
        # Search for a simplified pattern at the end that might include Chinese characters
        simplified_pattern = re.search(r'[Ff]inal [Jj]udgment[\s\S]*?\*\*(.*?)\*\*\s+is\s+\*\*(.*?)\*\*', text)
        if simplified_pattern:
            final_judgment = simplified_pattern.group(2).strip()

    # 7. Extract news statement - handle Chinese or any language
    news_statement = ""
    news_match = re.search(r'NEWS:\s+\*\*(.*?)\*\*\s+→', text)
    if news_match:
        news_statement = news_match.group(1).strip()

    # If we don't have news statement yet, try with another pattern
    if not news_statement:
        alt_news_match = re.search(r'NEWS:\s+\*\*(.*?)\*\*', text)
        if alt_news_match:
            news_statement = alt_news_match.group(1).strip()

    data = {
        "collection": {
            "reports": reports
        },
        "analysis": {
            "evaluations": evaluations,
            "consistency": consistency_points
        },
        "conclusion": {
            "news_statement": news_statement,
            "evidence": evidence_string,
            "final_judgment": final_judgment
        }
    }

    return json.dumps(data, ensure_ascii=False, indent=2)


def clean_text(text):
    """Helper function to thoroughly clean text of all data references and brackets."""
    # Remove complete [Data:...] patterns
    text = re.sub(r'\[Data:.*?\]', '', text)
    # Remove partial [Data: patterns
    text = re.sub(r'\[Data:[^\]]*', '', text)
    # Remove any Reports (x,y,z) patterns
    text = re.sub(r'Reports \([^\)]*\)', '', text)
    # Remove any stray brackets that might be left
    text = text.replace('[', '').replace(']', '')
    # Remove double spaces and trim
    text = re.sub(r'\s{2,}', ' ', text).strip()
    # Clean trailing periods for formatting consistency
    text = text.rstrip('.').strip()

    # Only add back period if it seems to be an English sentence
    # This avoids adding periods to Chinese sentences that don't use them
    if text and re.match(r'^[A-Z]', text) and not text.endswith(('.', '!', '?')):
        text += '.'
    return text




def process_jsonl_file(target_description, k_value="k=5"):
    file_path = "../.cache/new.jsonl"
    output_file_path = "../.cache/news_result.jsonl"
    """
    处理JSONL文件，查找匹配的description并处理其last_output，然后将结果保存到新文件
    
    Args:
        file_path (str): 输入JSONL文件路径
        target_description (str): 需要匹配的description字段值
        k_value (str): 需要处理的last_output中的键，默认为"k=5"
        output_file_path (str): 输出文件路径，如果为None则不保存
    
    Returns:
        dict: 处理后的结构化数据
    """
    # 检查输入文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"输入文件不存在: {file_path}")
    
    # 初始化匹配的数据
    matched_data = None
    
    # 读取JSONL文件并查找匹配的记录
    with open(file_path, 'r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, 1):
            try:
                data = json.loads(line)
                if data.get("description") == target_description:
                    print(f"找到匹配的记录 (第 {line_number} 行)")
                    matched_data = data
                    break
            except json.JSONDecodeError as e:
                print(f"解析第 {line_number} 行时出错: {e}")
                continue
    
    # 如果没有找到匹配的记录
    if matched_data is None:
        raise ValueError(f"未找到description匹配的记录: {target_description}")
    
    # 检查k_value是否存在
    if k_value not in matched_data.get("last_output", {}):
        raise ValueError(f"JSON数据中不存在{k_value}字段")
    
    # 获取对应k_value的文本内容
    text_content = matched_data["last_output"][k_value]
    
    # 检查文本内容是否为空
    if not text_content:
        raise ValueError(f"{k_value}字段的内容为空")
    
    # 转换文本为JSON格式
    structured_data = convert_text_to_json(text_content)
    
    try:
        # 尝试将结果解析为字典
        result = json.loads(structured_data)
    except json.JSONDecodeError:
        # 如果转换失败，直接使用原始数据
        result = structured_data
    
    # 如果需要保存到文件
    if output_file_path:
        # 准备要写入的数据（将claim放在最前面）
        if isinstance(result, list):
            records_to_write = [{"claim": target_description, **item} for item in result]
        else:
            records_to_write = [{"claim": target_description, **result}]
        
        # 检查输出文件是否存在
        file_exists = os.path.exists(output_file_path)
        
        # 检查已存在的claims
        existing_claims = set()
        if file_exists:
            with open(output_file_path, 'r', encoding='utf-8') as infile:
                for line in infile:
                    try:
                        data = json.loads(line)
                        if "claim" in data:
                            existing_claims.add(data["claim"])
                    except json.JSONDecodeError:
                        continue
        
        # 写入文件（追加模式）
        with open(output_file_path, 'a' if file_exists else 'w', encoding='utf-8') as outfile:
            for record in records_to_write:
                if record["claim"] not in existing_claims:
                    json.dump(record, outfile, ensure_ascii=False)
                    outfile.write('\n')
                    print(f"已写入记录（claim: {record['claim']}）")
                else:
                    print(f"跳过已存在的记录（claim: {record['claim']}）")
        
        print(f"\n处理完成，结果已保存到: {output_file_path}")
    
    return result


