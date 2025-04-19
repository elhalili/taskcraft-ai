import platform
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL")
MODEL = os.getenv("MODEL")

client = OpenAI(
    base_url=NEBIUS_BASE_URL,
    api_key=NEBIUS_API_KEY,
)

def get_cmd_prompt(instruction):
    os_type = platform.system().lower()

    if "windows" in os_type:
        prompt = f"""
You are an expert assistant that translates natural language instructions into executable commands for Windows Command Prompt (cmd.exe).
Only return the command with no explanation or formatting.
The user is on: {platform.system()} {platform.release()}.

Example:
Instruction: create a folder 'test' on desktop
Output: mkdir "%USERPROFILE%\\Desktop\\test"

Now, convert this instruction into a single Windows CMD command:
"""
    elif "linux" in os_type:
        prompt = f"""
You are an expert assistant that translates natural language instructions into shell commands for Linux (bash).
Only return the shell command, no extra explanation or formatting.

Example:
Instruction: list all files including hidden ones
Output: ls -la

Now, convert this instruction into a single Linux bash command:
"""
    else:
        return None, f"Unsupported OS: {os_type}"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": instruction}
            ],
            temperature=0.0,
            max_tokens=100,
        )

        command = response.choices[0].message.content.strip().strip('`')
        return command, None

    except Exception as e:
        return None, f"CMD prompt error: {e}"
