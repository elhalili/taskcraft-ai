import requests
from requests.auth import HTTPBasicAuth
import json
import os
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()


JIRA_API_TOKEN = os.getenv("JIRA_API_KEY")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
ACCOUNT_ID = os.getenv('JIRA_USER_ID')
BASE_URL = os.getenv('JIRA_BASE_URL')
JIRA_SERVER=os.getenv("JIRA_SERVER")

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


# function to fetch last issues based on how much days

def fetch_recent_issues(days):
    jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))
    
    jql_query = f'created >= "-{days}d" ORDER BY created DESC'
    
    issues = jira.search_issues(jql_query)
    
    issue_list = []
    for issue in issues:
        issue_key = issue.key
        summary = issue.fields.summary
        created_date = issue.fields.created
        status = issue.fields.status.name
        assignee = issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned"
        
        issue_data = {
            "issue_key": issue_key,
            "summary": summary,
            "created_date": created_date,
            "status": status,
            "assignee": assignee
        }
        
        issue_list.append(issue_data)
    
    response_dict = {
        "total_issues": len(issue_list),
        "issues": issue_list
    }
    
    return json.dumps(json.loads(json.dumps(response_dict)), sort_keys=True, indent=4, separators=(",", ": "))
