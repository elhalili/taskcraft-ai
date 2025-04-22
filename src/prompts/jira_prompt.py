import json
from openai import OpenAI
import os
from typing import Tuple, Optional, Dict, Any

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL")
MODEL = os.getenv("MODEL")

client = OpenAI(
    base_url=NEBIUS_BASE_URL,
    api_key=NEBIUS_API_KEY,
)

def get_jira_prompt(instruction: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Generates Jira operation details based on the provided instruction.

    Args:
        instruction (str): The instruction detailing what Jira operation to perform.

    Returns:
        Tuple[Optional[Dict[str, Any]], Optional[str]]:
            - A dictionary containing 'operation' and operation-specific parameters
            - An error message if an exception occurs, or None if successful.
    """
    
    prompt = f"""
You are a Jira operations assistant that extracts task details from user instructions.

You must return a JSON object with one of these formats:

1. For listing projects:
{{
  "operation": "list_project"
}}

2. For creating a project:
{{
  "operation": "create_project",
  "params": {{
    "project_name": "<project name>",
    "description": "<project description>"
  }}
}}

3. For creating an issue:
{{
  "operation": "create_issue",
  "params": {{
    "issue_name": "<issue name>",
    "description": "<issue description>",
    "project_key": "<project key>",
    "task_type": "<task type>"
  }}
}}


Examples:
1. Instruction: list all projects
Response:
{{
  "operation": "list_project"
}}

2. Instruction: create a new project called Marketing with description for marketing team
Response:
{{
  "operation": "create_project",
  "params": {{
    "project_name": "Marketing",
    "description": "Project for marketing team"
  }}
}}

3. Instruction: create a bug ticket in project DEV about login page not working
Response:
{{
  "operation": "create_issue",
  "params": {{
    "issue_name": "Login page not working",
    "description": "The login page returns 500 error when submitting credentials",
    "project_key": "DEV",
    "task_type": "bug"
  }}
}}

4. Instruction: list all issues in the last seven days
Response:
{{
  "operation": "fetch_recent_issues",
  "params": {{
    "days": "7"
  }}
}}

ONLY return the JSON object. Do NOT include any other explanation or text.

Now process this instruction:
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": instruction}
            ],
            temperature=0.3,
            max_tokens=250,
        )

        result = response.choices[0].message.content.strip()
        jira_data = json.loads(result)
        
        # Validate the operation type
        valid_operations = ["list_project", "create_project", "create_issue", "fetch_recent_issues"]
        if jira_data["operation"] not in valid_operations:
            return None, f"Invalid operation type: {jira_data['operation']}"
            
        return jira_data, None

    except json.JSONDecodeError:
        return None, "Invalid JSON response from model"
    except Exception as e:
        return None, f"Jira prompt error: {e}"
    
def generate_success_message(operation_result: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Generates a human-readable success message based on the completed Jira operation.
    
    Args:
        operation_result (Dict[str, Any]): The result of the Jira operation containing:
            - "operation": the operation type
            - "params": the parameters used for the operation
    
    Returns:
        Tuple[Optional[str], Optional[str]]:
            - A success message string if successful
            - An error message if an exception occurs, or None if successful
    """
    prompt = f"""
You are a Jira assistant that generates friendly messages for completed operations.

You will receive a JSON object describing a completed Jira operation and you must return
a brief, friendly humain readable description.

only the message.
Now generate a message for this completed operation:
{json.dumps(operation_result, indent=2)}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(operation_result)}
            ],
            temperature=0.2,  # Lower temperature for more predictable responses
            max_tokens=100,
        )

        message = response.choices[0].message.content.strip()
        # Remove any accidental JSON formatting or quotes
        message = message.strip('"').strip("'").strip()
        return message, None

    except Exception as e:
        return None, f"Failed to generate success message: {e}"