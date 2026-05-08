import requests
from requests.auth import HTTPBasicAuth
import json

def log_step(message):
    print(f"[JiraAPI] {message}")

class JiraAPIClient:
    def __init__(self, config):
        self.base_url = config['base_url']
        self.email = config['email']
        self.token = config['secret']
        self.auth = HTTPBasicAuth(self.email, self.token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def _get_user_account_id(self, query):
        log_step(f"Searching for user account ID: {query}")
        url = f"{self.base_url}/rest/api/3/user/search"
        params = {"query": query}
        response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
        
        if response.status_code == 200:
            users = response.json()
            if users:
                return users[0]['accountId']
        
        log_step(f"Could not find user account ID for {query}")
        return None

    def _get_sprint_id(self, sprint_name):
        log_step(f"Searching for sprint ID: {sprint_name}")
        url = f"{self.base_url}/rest/agile/1.0/sprint"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        if response.status_code == 200:
            sprints = response.json().get('values', [])
            for s in sprints:
                if s['name'].lower() == sprint_name.lower():
                    return s['id']
        
        log_step(f"Could not find sprint with name {sprint_name}")
        return None

    def create_issue(self, data):
        project_key = data.get('project_key')
        summary = data.get('summary')
        description = data.get('description', '')
        issue_type = data.get('issue_type', 'Task')
        assignee = data.get('assignee', '')
        labels = data.get('labels', '')
        sprint = data.get('sprint', '')

        account_id = None
        if assignee:
            account_id = self._get_user_account_id(assignee)

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": issue_type},
                "labels": [l.strip() for l in labels.split(',')] if labels else [],
            }
        }

        if description:
            payload["fields"]["description"] = {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": description}
                        ]
                    }
                ]
            }

        if account_id:
            payload["fields"]["assignee"] = {"accountId": account_id}

        log_step("Sending request to create issue...")
        url = f"{self.base_url}/rest/api/3/issue"
        response = requests.post(url, auth=self.auth, headers=self.headers, json=payload)

        if response.status_code == 201:
            result = response.json()
            ticket_id = result['key']
            log_step(f"Ticket created successfully: {ticket_id}")
            
            if sprint:
                sprint_id = self._get_sprint_id(sprint)
                if sprint_id:
                    log_step(f"Assigning ticket {ticket_id} to sprint {sprint_id}")
                    sprint_url = f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
                    sprint_payload = {"issueId": result['id']}
                    requests.post(sprint_url, auth=self.auth, headers=self.headers, json=sprint_payload)
                else:
                    log_step(f"Warning: Sprint '{sprint}' not found, skipping assignment.")

            return {
                "success": True,
                "ticket_id": ticket_id,
                "url": f"{self.base_url}/browse/{ticket_id}"
            }
        else:
            error_msg = response.text
            log_step(f"Failed to create issue: {error_msg}")
            return {"success": False, "error": f"Jira API Error: {response.status_code} - {error_msg}"}

    def get_sprints(self):
        """Fetch all available sprints."""
        log_step("Fetching available sprints...")
        url = f"{self.base_url}/rest/agile/1.0/sprint"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        if response.status_code == 200:
            return response.json().get('values', [])
        return []

    def get_sprint_metrics(self, sprint_id):
        """Fetch issues for a specific sprint and calculate metrics."""
        log_step(f"Fetching issues for sprint {sprint_id}...")
        url = f"{self.base_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        
        if response.status_code != 200:
            return {"success": False, "error": "Failed to fetch sprint issues"}
        
        issues = response.json().get('issues', [])
        
        # Metrics calculation
        total_issues = len(issues)
        status_counts = {}
        
        for issue in issues:
            status = issue['fields'].get('status', {}).get('name', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
        return {
            "success": True,
            "total_issues": total_issues,
            "status_distribution": status_counts,
            "issues": [
                {"key": i['key'], "summary": i['fields']['summary'], "status": i['fields']['status']['name']}
                for i in issues
            ]
        }

def create_ticket_api(config, data):
    client = JiraAPIClient(config)
    return client.create_issue(data)

def get_sprints_api(config):
    client = JiraAPIClient(config)
    return client.get_sprints()

def get_sprint_metrics_api(config, sprint_id):
    client = JiraAPIClient(config)
    return client.get_sprint_metrics(sprint_id)