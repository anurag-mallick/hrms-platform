import os
import time
import re
from playwright.sync_api import sync_playwright

AUTH_STATE_FILE = 'auth_state.json'

def log_step(message):
    print(f"[JiraBrowser] {message}")

def handle_login(page, config):
    log_step("Attempting login...")
    page.goto(f"{config['base_url']}/login")
    
    # Handle email
    page.fill('input[name="username"]', config['email'])
    page.click('button[id="login-submit"]')
    
    # Handle password
    page.wait_for_selector('input[name="password"]')
    page.fill('input[name="password"]', config['secret'])
    page.click('button[id="login-submit"]')
    
    # Wait for redirect to confirm login
    page.wait_for_url(lambda url: "/jira" in url or "/secure" in url, timeout=60000)
    log_step("Login successful. Saving session state.")
    page.context.storage_state(path=AUTH_STATE_FILE)

def create_ticket_browser(config, data):
    project_key = data.get('project_key', config['default_project'])
    summary = data.get('summary')
    description = data.get('description', '')
    issue_type = data.get('issue_type', 'Task')
    assignee = data.get('assignee', '')
    labels = data.get('labels', '')
    sprint = data.get('sprint', '')

    with sync_playwright() as p:
        # Launch browser (visible)
        browser = p.chromium.launch(headless=False)
        
        context_args = {}
        if os.path.exists(AUTH_STATE_FILE):
            context_args['storage_state'] = AUTH_STATE_FILE
        
        context = browser.new_context(**context_args)
        page = context.new_page()

        try:
            # 1. Navigate to Board
            url = f"{config['base_url']}/jira/software/projects/{project_key}/boards"
            log_step(f"Navigating to {url}")
            page.goto(url)

            # 2. Check for login redirect
            if "login" in page.url:
                log_step("Session expired or not found. Re-authenticating...")
                handle_login(page, config)
                page.goto(url)

            # 3. Click Create
            log_step("Clicking 'Create' button")
            page.get_by_role("button", name="Create").click()
            page.wait_for_selector('button[aria-label="Create"]')

            # 4. Set Issue Type
            log_step(f"Setting issue type to {issue_type}")
            page.get_by_role("button", name="Issue Type").click()
            page.get_by_role("option", name=issue_type).click()

            # 5. Fill Summary
            log_step("Filling summary")
            page.get_by_aria_label("Summary").fill(summary)

            # 6. Fill Description
            if description:
                log_step("Filling description")
                page.get_by_aria_label("Description").fill(description)

            # 7. Set Assignee
            if assignee:
                log_step(f"Setting assignee to {assignee}")
                assignee_field = page.get_by_aria_label("Assignee")
                assignee_field.click()
                page.keyboard.type(assignee)
                page.keyboard.press("Enter")

            # 8. Set Labels
            if labels:
                log_step(f"Setting labels: {labels}")
                label_list = [l.strip() for l in labels.split(',')]
                labels_field = page.get_by_aria_label("Labels")
                labels_field.click()
                for label in label_list:
                    page.keyboard.type(label)
                    page.keyboard.press("Enter")

            # 9. Set Sprint
            if sprint:
                log_step(f"Setting sprint to {sprint}")
                sprint_field = page.get_by_aria_label("Sprint")
                sprint_field.click()
                page.keyboard.type(sprint)
                page.keyboard.press("Enter")

            # 10. Submit
            log_step("Submitting ticket")
            page.get_by_role("button", name="Create").click()

            # 11. Capture Ticket ID
            log_step("Waiting for confirmation...")
            page.wait_for_load_state("networkidle")
            time.sleep(5) 
            
            page_content = page.content()
            match = re.search(r'([A-Z]{2,10}-\d+)', page_content)
            
            if match:
                ticket_id = match.group(1)
                log_step(f"Ticket created successfully: {ticket_id}")
                ticket_url = f"{config['base_url']}/browse/{ticket_id}"
                browser.close()
                return {"success": True, "ticket_id": ticket_id, "url": ticket_url}
            else:
                current_url = page.url
                match_url = re.search(r'/browse/([A-Z]{2,10}-\d+)', current_url)
                if match_url:
                    ticket_id = match_url.group(1)
                    log_step(f"Ticket created successfully (from URL): {ticket_id}")
                    ticket_url = f"{config['base_url']}/browse/{ticket_id}"
                    browser.close()
                    return {"success": True, "ticket_id": ticket_id, "url": ticket_url}
                
                raise Exception("Could not capture Ticket ID from page or URL. Consider switching to API mode for better reliability.")

        except Exception as e:
            log_step(f"Error occurred: {str(e)}")
            browser.close()
            return {"success": False, "error": str(e)}