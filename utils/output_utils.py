import json
import re


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
