
import argparse
import smtplib
import os
import sys
from email.message import EmailMessage
from dotenv import load_dotenv 
import os
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader, select_autoescape

load_dotenv()

SENDER_EMAIL = os.getenv("GMAIL_USER")
SENDER_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
NEBIUS_BASE_URL = "https://api.studio.nebius.com/v1/"
NEBIUS_MODEL = "meta-llama/Meta-Llama-3.1-70B-Instruct"


template_loader = FileSystemLoader(searchpath=".")

jinja_env = Environment(
        loader=template_loader,
        autoescape=select_autoescape(['html', 'xml']) 
    )

html_template = jinja_env.get_template("MarketingEmail.html")


def generate_email_body_with_ai(subject):
    if not NEBIUS_API_KEY:
        print("Error: NEBIUS_API_KEY environment variable not set.")
        return None
    try:
        client = OpenAI(
        base_url=NEBIUS_BASE_URL,
        api_key=NEBIUS_API_KEY,
        )
    
        prompt = (
    f"You are an expert in crafting clear, concise, and trustworthy service communications designed to avoid spam filters."
    f"Your task is to generate ONLY the email body text for a message with the subject line: '{subject}'. "
    f"Assume the email is from a service or support team to a user/customer."
    f"\n\n"
    f"Key Requirements for the body content:\n"
    f"1.  **Clarity and Directness:** Get straight to the point. Clearly state the email's purpose and its direct relevance to the recipient, connecting logically to the subject: '{subject}'.\n"
    f"2.  **Helpful & Value-Oriented:** Focus on providing necessary information, updates, confirmations, or clear instructions/next steps. Ensure the content is genuinely useful and expected (or logically follows from a user action or request implied by the subject).\n"
    f"3.  **Professional & Trustworthy Tone:** Maintain a helpful, respectful tone. Avoid overly casual or overly formal language. Build trust through clarity.\n"
    f"4.  **Spam Trigger Avoidance:**\n"
    f"    *   Crucially AVOID: Marketing jargon, hype, excessive exclamation points (use sparingly, if at all), ALL CAPS, unnecessary urgency ('Act now!', 'Limited time!'), clickbait phrases, vague promises, or overly promotional language.\n"
    f"    *   Use natural, straightforward language. Short sentences and paragraphs are often better.\n"
    f"    *   Ensure the body content directly matches and logically expands upon the subject line '{subject}'. Misleading subjects are a major spam flag.\n"
    f"\n"
    f"Output Constraints:\n"
    f"-   Generate ONLY the email body text.\n"
    f"-   Strictly NO greeting (e.g., 'Dear User,', 'Hi,').\n"
    f"-   Strictly NO closing or signature (e.g., 'Best regards,', 'The Team', 'Sincerely').\n"
    f"-   Strict maximum length: 350 words. Aim for conciseness – use only the words needed to convey the message clearly.\n"
)



        completion = client.chat.completions.create(
            model=NEBIUS_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=400
        )

        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"An error occured durring ai generation: {e}")
        return None
    





def send_gmail(recipient_email, subject):

    if not SENDER_EMAIL or not SENDER_APP_PASSWORD:
        print("Error: Ensure GMAIL_USER and GMAIL_APP_PASSWORD environment variables are set.")
        print("You might need to create a .env file or export them.")
        sys.exit(1) 

    ai_generated_body = generate_email_body_with_ai(subject)
    ai_generated_html_body = ai_generated_body.replace('\n', '<br>\n')

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    EMAIL_TEMPLATE = f"""
        Hi there,

        {ai_generated_body}

        Best regards,

        The Support Team
        {SENDER_EMAIL}
        """
    
    template_context = {
            "subject": subject,
            "ai_generated_html_body": ai_generated_html_body,
            "sender_email": SENDER_EMAIL
        }
    html_content = html_template.render(template_context)
    
    msg.set_content(EMAIL_TEMPLATE)
    msg.add_alternative(html_content, subtype='html')
    

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server: 
            print(f"Attempting to log in as {SENDER_EMAIL}...")
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            print("Login successful.")

            print(f"Sending email to {recipient_email} with subject '{subject}'...")
            server.send_message(msg)
            print("Email sent successfully!")

    except smtplib.SMTPAuthenticationError:
        print("\nError: SMTP Authentication Failed.")
        print(" - Check if GMAIL_USER and GMAIL_APP_PASSWORD are correct.")
        print(" - Ensure you are using a 16-character App Password, not your regular password.")
        print(" - Make sure 2-Step Verification is enabled for the sender account.")
        print(" - Check if the App Password is still valid in your Google Account settings.")
        sys.exit(1)
    except smtplib.SMTPConnectError:
        print("\nError: Could not connect to the SMTP server (smtp.gmail.com:465).")
        print(" - Check your internet connection.")
        print(" - Check firewall settings if applicable.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send an email using Gmail with a predefined template.")
    parser.add_argument("--email", required=True, help="Recipient's email address.")
    parser.add_argument("--subject", required=True, help="Subject line of the email.")

    args = parser.parse_args()

    send_gmail(args.email, args.subject)  