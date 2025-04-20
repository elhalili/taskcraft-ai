import requests
from requests.auth import HTTPBasicAuth
import json
import os

JIRA_API_TOKEN = os.getenv("JIRA_API_KEY")
print(JIRA_API_TOKEN)
JIRA_EMAIL = os.getenv("JIRA_EMAIL")

auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

ACCOUNT_ID = os.getenv('JIRA_USER_ID')
BASE_URL = os.getenv('JIRA_BASE_URL')

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}


# function to create an issue
def create_issue(issue_name: str, description: str, project_key : str, task_type: str):
    url_issue = f"{BASE_URL}/issue"
    payload = {
        "fields": {
            "assignee": {
                "id": ACCOUNT_ID 
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
        return json.encoder({"msg": "Issue created successfully."})
    
    print(f"Failed to create issue: {response.status_code}")
    return json.dumps(response.json(), sort_keys=True, indent=4, separators=(",", ": "))



# function to create a project

def create_project(project_name, description):
    key = project_name[:3].upper()  
    
    url_project = f'{BASE_URL}/project'

    payload = {
        "key": key,  
        "name": project_name,
        "projectTypeKey": "business",
        "projectTemplateKey": "com.atlassian.jira-core-project-templates:jira-core-simplified-process-control",
        "description": description,
        "leadAccountId": ACCOUNT_ID,
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

    print(response)

    response.raise_for_status()

    return json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": "))


def list_project():
    url_project=f"{BASE_URL}/project"
    response = requests.request(
        "GET",
        url_project,
        headers=headers,
        auth=auth
    )
    return json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": "))