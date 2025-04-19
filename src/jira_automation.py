import requests
from requests.auth import HTTPBasicAuth
import json
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("JIRA_API_KEY")
EMAIL = os.getenv("EMAIL")
auth = HTTPBasicAuth(EMAIL, API_TOKEN)

account_id = os.getenv('USER_ID')
base_url = os.getenv('JIRA_BASE_URL')

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}


# function to create an issue
def create_issue(issue_name: str, description: str, project_key : str, task_type: str):
    url_issue = f"{base_url}/issue"
    payload = {
        "fields": {
            "assignee": {
                "id": os.getenv("USER_ID") 
            },
            "project": {
                "key": project_key  
            },
            "summary": issue_name,
            "description": {
                "content": [
                    {
                        "content": [
                            {
                                "text": description,
                                "type": "text"
                            }
                        ],
                        "type": "paragraph"
                    }
                ],
                "type": "doc",
                "version": 1
            },
            
            "issuetype": {
                "name": task_type
            }
        }
    }

    response = requests.post(
        url_issue,
        json=payload,
        headers=headers,
        auth=auth
    )

    if response.status_code == 201:
        print("Issue created successfully.")
    else:
        print(f"Failed to create issue: {response.status_code}")
        print(json.dumps(response.json(), sort_keys=True, indent=4, separators=(",", ": ")))



# function to create a project

def create_project(project_name, description):
    key = project_name[:3].upper()  
    
    url_project = f'{base_url}/project'

    payload = {
        "key": key,  
        "name": project_name,
        "projectTypeKey": "business",
        "projectTemplateKey": "com.atlassian.jira-core-project-templates:jira-core-simplified-process-control",
        "description": description,
        "leadAccountId": account_id,
        "assigneeType": "UNASSIGNED",
        "avatarId": 10401
    }

    response = requests.request(
        "POST",
        url_project,
        data=json.dumps(payload),
        headers=headers,
        auth=auth
    )

    response.raise_for_status()

    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))


def list_project():
    url_project=f"{base_url}/project"
    response = requests.request(
        "GET",
        url_project,
        headers=headers,
        auth=auth
    )
    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))
