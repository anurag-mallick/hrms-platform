# Jira Ticket Creator

A local Python application that allows you to create Jira tickets via a clean web interface. You can choose between a fast, reliable API-based approach or a browser-automation approach that simulates a real user.

## Tech Stack
- **Backend**: Python 3.10+, Flask
- **API Mode**: `requests` library (Jira REST API v3)
- **Browser Mode**: `playwright` (Chromium)
- **Frontend**: Bootstrap 5 CDN, Chart.js (for Dashboard)

## Setup Instructions

### 1. Installation
First, clone or enter the project directory and set up your environment:

```bash
cd jira_automator
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Running the Application
Start the application:
```bash
python app.py
```
Open your browser and navigate to [http://localhost:5000](http://localhost:5000).

### 3. Configuration (UI-Driven)
On your first visit, the app will automatically redirect you to the **Settings** page. Here you can configure:
- **Connection Mode**: Choose between `API Token` (Recommended) or `Browser Automation`.
- **Jira Base URL**: e.g., `https://yourcompany.atlassian.net`
- **Email**: Your Jira account email.
- **Secret**: Your API Token (for API mode) or Password (for Browser mode).
- **Default Project Key**: e.g., `ENG`.
- **Assignee List**: One assignee per line. These will appear as dropdown options in the Single Create and Bulk Create pages.

### 4. Additional Setup for Browser Mode
If you chose **Browser Automation**, you must install the Chromium browser engine:

```bash
playwright install chromium
```

---

## Features

### 1. Single Ticket Creation
Create individual tickets using a simple form. Assignee is now a dropdown populated from your configured assignee list.

### 2. Bulk Ticket Creation (API Mode Only)
Create multiple tickets at once by pasting data directly from Excel or Google Sheets.
- Navigate to the **Bulk Create** tab.
- Paste your table (Columns: Summary, Description, Type, Assignee, Labels, Sprint).
- Supports both tab and pipe (`|`) separators.
- Preview and edit the data in the web-based grid before submitting.

### 3. Sprint Dashboard (API Mode Only)
Visualize your sprint progress with real-time metrics.
- Navigate to the **Sprint Dashboard** tab.
- Select a sprint from the dropdown.
- View a **Status Distribution Chart** and a detailed list of all issues in the sprint.

---

## How to get a Jira API Token (For API Mode)
To use the API mode, you need an Atlassian API token instead of your account password:
1. Log in to [https://id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens).
2. Click **Create API token**.
3. Give it a label (e.g., "Ticket-Automator") and click **Create**.
4. Copy the token immediately; you won't be able to see it again.

## Usage
1. **Run the server**: `python app.py`
2. **Access the UI**: Open [http://localhost:5000](http://localhost:5000) in your browser.
3. **Navigate**: Use the top navigation bar to switch between Single Create, Bulk Create, Dashboard, and Settings.

## Error Handling
- **API Mode**: Returns specific Jira API error messages.
- **Browser Mode**: Logs every step to the terminal. If a timeout occurs, the app will suggest switching to API mode for better stability.
