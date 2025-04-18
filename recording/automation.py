import os
import subprocess
import platform
import record
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
NEBIUS_BASE_URL = "https://api.studio.nebius.com/v1/"
MODEL = "meta-llama/Meta-Llama-3.1-70B-Instruct"

client = OpenAI(
        base_url=NEBIUS_BASE_URL,
        api_key=NEBIUS_API_KEY,
        )

prompt = r"""
You are an expert assistant that translates natural language instructions into executable commands for the Windows Command Prompt (cmd.exe).
Your goal is to provide *only* the command itself, without any explanation, introduction, markdown formatting, or extra text.
The user is running on the Windows operating system ({platform.system()} {platform.release()}).
Ensure the command is syntactically correct for cmd.exe.

Example 1:
Instruction: send an email to ahmed
Output: python C:\Users\mucef\Desktop\hackthun\Emails\sendEMAIL.py --email contact@mouncef.tech --subject "reminder for meeting tomorrow at 10PM"

Example 2:
Instruction: create a new folder named 'my_project' on the Desktop
Output: mkdir "%USERPROFILE%\\Desktop\\my_project"

Example 3:
Instruction: show network configuration
Output: ipconfig /all

Now, translate the following instruction into a single Windows CMD command:
"""

def get_cmd(instruction):
    system_prompt = prompt
    try:
        response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": instruction}
                ],
                temperature=0.0, 
                max_tokens=150, 
                n=1,
                stop=None # the model decide when to stop (usually after the command)
            )
        if response.choices:
                command = response.choices[0].message.content.strip().strip('`').strip()
                if command:
                    print(f"Generated command: {command}") 
                    return command, None # SUCCESS: Return command and None for error
                else:
                    return None, "API returned an empty response."
        else:
                return None, "API returned no choices."

    except Exception as e:
        error_message = f"API call failed: {e}"
        print(f"Error in get_cmd: {error_message}") # Log the error
        return None, error_message # FAILURE: Return None for command and the error message


def execute_cmd(command):
    try:
        process = subprocess.run(['cmd', '/c', command],
                                 capture_output=True,
                                 text=True,
                                 check=False,
                                 encoding='utf-8',  # Be explicit about encoding
                                 errors='replace')  # Handle potential decoding errors

        if process.stdout:
            print("Output:")
            print(process.stdout)
        if process.stderr:
            print("Error Output:")
            print(process.stderr)
        print(f"\nCommand finished with exit code: {process.returncode}")

        success = process.returncode == 0
        error_msg = process.stderr.strip() if process.stderr else ""

        return success, error_msg

    except Exception as e:
        print(f"An exception occurred: {e}")
        return False, str(e)