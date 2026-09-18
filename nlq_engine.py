import ollama
import re
from config import LLM_MODEL

FORBIDDEN_PATTERNS = [
    "import", "exec", "eval", "open(", "__", "os.", "sys.",
    "subprocess", "shutil", "requests", "socket", "input(",
]
 
 
def _is_code_safe(code: str) -> bool:
    lowered = code.lower()
    return not any(pattern in lowered for pattern in FORBIDDEN_PATTERNS)
 
 
def _extract_code(llm_response: str) -> str:
    fenced = re.search(r"```(?:python)?\s*(.*?)```", llm_response, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    return llm_response.strip()

SYSTEM_PROMPT = """You are a data analyst assistant. You are given a pandas \
DataFrame called `df` containing customer support tickets with these columns:
 
- ticket_id (string)
- created_at (datetime)
- category (string: Billing, Technical, General)
- priority (string: Low, Medium, High, Critical)
- status (string: Open, Resolved, Escalated)
- response_time_hrs (float)
- resolution_time_hrs (float, NaN if unresolved)
- agent_id (string)
- customer_rating (int 1-5, NaN if unresolved)
- issue_summary (string)
 
Given a question, respond with EXACTLY ONE LINE of pandas code that computes \
the answer, assigned to a variable called `result`. Do not use import \
statements. Do not explain the code. Do not use markdown formatting. \
Output ONLY the single line of code.
 
Example:
Question: How many tickets are Open?
result = len(df[df['status'] == 'Open'])
"""

def ask_question(df, question):
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            options={"temperature": 0},
        )
    except Exception as e:
        # Covers Ollama not running, model not found, etc.
        return {"success": False, "error": f"LLM call failed: {e}"}
 
    raw_code = response["message"]["content"]
    code = _extract_code(raw_code)
 
    if not _is_code_safe(code):
        return {
            "success": False,
            "error": "Generated code failed safety check.",
            "generated_code": code,
        }
 
    local_vars = {"df": df, "pd": __import__("pandas")}

    SAFE_BUILTINS = {
        "len": len, "sum": sum, "min": min, "max": max, "abs": abs,
        "round": round, "sorted": sorted, "list": list, "dict": dict,
        "set": set, "tuple": tuple, "str": str, "int": int,
        "float": float, "bool": bool, "range": range,
        "enumerate": enumerate, "zip": zip,
    }

    try:
        exec(code, {"__builtins__": SAFE_BUILTINS}, local_vars)
        result = local_vars.get("result", "No result was produced.")
    except Exception as e:
        return {
            "success": False,
            "error": f"Generated code failed to run: {e}",
            "generated_code": code,
        }
 
    return {
        "success": True,
        "answer": result,
        "generated_code": code,  # shown in the UI for transparency
    }
