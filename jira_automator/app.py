import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from jira_api import create_ticket_api, get_sprints_api, get_sprint_metrics_api
from jira_browser import create_ticket_browser

app = Flask(__name__)
CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "mode": "api",
            "base_url": "",
            "email": "",
            "secret": "",
            "default_project": "",
            "assignees": ""
        }
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config_data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config_data, f, indent=4)

@app.route('/')
def index():
    config = load_config()
    if not config.get('base_url') or not config.get('email') or not config.get('secret'):
        return redirect(url_for('config_page'))
    assignees = [a.strip() for a in config.get('assignees', '').split('\\n') if a.strip()]
    return render_template('index.html', default_project=config.get('default_project', ''), assignees=assignees)

@app.route('/config')
def config_page():
    return render_template('config.html', config=load_config())

@app.route('/save-config', methods=['POST'])
def save_config_route():
    data = request.json
    save_config(data)
    return jsonify({"success": True})

@app.route('/bulk')
def bulk_page():
    config = load_config()
    assignees = [a.strip() for a in config.get('assignees', '').split('\\n') if a.strip()]
    return render_template('bulk.html', default_project=config.get('default_project', ''), assignees=assignees)

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/create-ticket', methods=['POST'])
def create_ticket():
    config = load_config()
    data = request.json
    
    if not data.get('summary'):
        return jsonify({"success": False, "error": "Summary is required"}), 400

    mode = config.get('mode')
    if mode == 'api':
        result = create_ticket_api(config, data)
    else:
        result = create_ticket_browser(config, data)
    
    if result.get('success'):
        print(f"\\n[SUCCESS] Ticket Created: {result.get('ticket_id')}")
    
    return jsonify(result)

@app.route('/create-bulk', methods=['POST'])
def create_bulk():
    config = load_config()
    data = request.json
    tickets = data.get('tickets', [])
    
    if not tickets:
        return jsonify({"success": False, "error": "No tickets provided"}), 400

    if config.get('mode') != 'api':
        return jsonify({"success": False, "error": "Bulk creation is only supported in API mode."}), 400
    
    results = []
    for ticket in tickets:
        res = create_ticket_api(config, ticket)
        results.append({
            "summary": ticket.get('summary'),
            "result": res
        })
    
    return jsonify({"success": True, "results": results})

@app.route('/api/sprints', methods=['GET'])
def api_sprints():
    config = load_config()
    if config.get('mode') != 'api':
        return jsonify({"success": False, "error": "Dashboard metrics are only available in API mode"}), 400
    
    sprints = get_sprints_api(config)
    return jsonify({"success": True, "sprints": sprints})

@app.route('/api/metrics/<sprint_id>', methods=['GET'])
def api_metrics(sprint_id):
    config = load_config()
    if config.get('mode') != 'api':
        return jsonify({"success": False, "error": "Dashboard metrics are only available in API mode"}), 400
    
    metrics = get_sprint_metrics_api(config, sprint_id)
    return jsonify(metrics)

if __name__ == '__main__':
    print("\\nStarting Jira Ticket Creator...")
    print("Web UI available at http://localhost:5000")
    app.run(debug=True, port=5000)