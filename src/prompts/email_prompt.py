import json
from openai import OpenAI
import os
from typing import List, Dict, Tuple, Optional

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL")
MODEL = os.getenv("MODEL")

client = OpenAI(
    base_url=NEBIUS_BASE_URL,
    api_key=NEBIUS_API_KEY,
)

def get_email_prompt(instruction: str, contacts: List[Dict[str, str]]) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    """
    Generates an email based on the provided instruction and a contact list.

    This function uses OpenAI's language model to extract email content, subject, and contact information 
    based on the given instruction and list of contacts.

    Args:
        instruction (str): The instruction or prompt detailing what email should be composed.
        contacts (List[Dict[str, str]]): A list of dictionaries containing contact information with 'name' and 'email' keys.

    Returns:
        Tuple[Optional[Dict[str, str]], Optional[str]]:
            - A dictionary containing 'contact', 'subject', and 'body' of the email if successful.
            - An error message if an exception occurs, or None if successful.
    """
    
    prompt = f"""
You are a helpful assistant that extracts email information from user instructions.

You are given this contact list:
{json.dumps(contacts, indent=2)}

You must return a JSON object in this format:
{{
  "contact": "<email from contact list>",
  "subject": "<short subject>",
  "body": "<email body>"
}}

Example:
Instruction: send a reminder email to Sarah about the project deadline
Response:
{{
  "contact": "sarah@example.com",
  "subject": "Project Deadline Reminder",
  "body": "Hi Sarah, just a reminder about the project deadline coming up soon."
}}

ONLY return the JSON object. Do NOT include any other explanation or text.

Now process this instruction:
"""

    try:
        # Send the prompt to the OpenAI model for processing
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": instruction}
            ],
            temperature=0.3,
            max_tokens=250,
        )

        # Parse the model's response into the expected format
        result = response.choices[0].message.content.strip()
        email_data = json.loads(result)
        return email_data, None  # Return the email data and None as no error

    except Exception as e:
        # Handle exceptions and return the error message
        return None, f"Email prompt error: {e}"
