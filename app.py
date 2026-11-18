import argparse
import base64
import os
import re
import secrets
import threading
import webbrowser
from datetime import date
from io import BytesIO
from pathlib import Path
from uuid import uuid4
import logging
import sys

import pandas as pd
import requests
from flask import Flask, jsonify, render_template, request, send_file, session
from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from werkzeug.serving import make_server

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

APP_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)
app.config["MAX_CONTENT_LENGTH"] = 65536

ACTION_TOKEN = secrets.token_urlsafe(32)
REQUEST_TIMEOUT_SECONDS = 30
PAGE_SIZE = 100

REQUIRED_SETTINGS = ("jira_email", "jira_api_token", "jira_base_url")
JIRA_FIELDS_API = [
    "summary", "created", "assignee", "status", "description",
    "issuetype", "parent", "key"
]


class JiraSession:
    def __init__(self, email, api_token, base_url):
        self.email = email
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        auth_b64 = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        self.session.headers.update({
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def request_json(self, method, endpoint, **kwargs):
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method, url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"❌ API Error: {method} {url}")
            logging.error(f"   Status: {response.status_code if 'response' in locals() else 'N/A'}")
            if 'response' in locals() and response.text:
                logging.error(f"   Response: {response.text[:1000]}")
            if 'json' in kwargs:
                import json as json_lib
                logging.error(f"   Request Body: {json_lib.dumps(kwargs['json'], indent=2)}")
            raise

    def test_connection(self):
        try:
            logging.debug(f"🔍 Testing connection to {self.base_url}/rest/api/3/myself")
            self.request_json("GET", "/rest/api/3/myself")
            logging.debug("✅ Test connection successful")
            return True
        except Exception as e:
            logging.error(f"❌ Test connection failed: {type(e).__name__}: {str(e)}")
            return False

    def get_field_names(self):
        try:
            data = self.request_json("GET", "/rest/api/3/field")
            return {field["id"]: field["name"] for field in data}
        except Exception:
            return {}

    def get_projects(self):
        try:
            data = self.request_json(
                "GET", "/rest/api/3/project/search",
                params={"maxResults": 50}
            )
            return [{"key": p["key"], "name": p["name"]} for p in data.get("values", [])]
        except Exception:
            return []

    def get_project_statuses(self, project_key):
        try:
            data = self.request_json(
                "GET", f"/rest/api/3/project/{project_key}/statuses"
            )
            statuses = {}
            for issue_type in data:
                for status in issue_type.get("statuses", []):
                    statuses[status["name"]] = status["id"]
            return list(statuses.keys())
        except Exception:
            return []

    def search_issues(self, jql, fields):
        try:
            all_issues = []
            next_token = None
            payload = {
                "jql": jql,
                "fields": fields,
                "maxResults": PAGE_SIZE
            }
            logging.debug(f"📤 Sending search request with payload: {payload}")
            while True:
                if next_token:
                    payload["nextPageToken"] = next_token
                data = self.request_json(
                    "POST", "/rest/api/3/search/jql",
                    json=payload
                )
                all_issues.extend(data.get("issues", []))
                next_token = data.get("nextPageToken")
                if not next_token or not data.get("issues", []):
                    break
            return all_issues[:5000]
        except Exception as e:
            raise RuntimeError(f"Jira search failed: {str(e)}")

    def get_status_transitions(self, issue_key, status_names):
        try:
            data = self.request_json("GET", f"/rest/api/3/issue/{issue_key}/changelog")
            transitions = {}
            for history in data.get("histories", []):
                for item in history.get("items", []):
                    if item.get("field") == "status" and item.get("toString") in status_names:
                        status_name = item.get("toString")
                        transitions[status_name] = history.get("created")
            return transitions
        except Exception:
            return {}

    def close(self):
        self.session.close()


def get_jira_session():
    if not all(key in session for key in REQUIRED_SETTINGS):
        return None
    try:
        return JiraSession(
            session["jira_email"],
            session["jira_api_token"],
            session["jira_base_url"]
        )
    except Exception:
        return None


@app.before_request
def protect_actions():
    if request.method == "POST" and not secrets.compare_digest(
        request.headers.get("X-App-Token", ""), ACTION_TOKEN
    ):
        logging.warning(f"🚨 Token mismatch: expected {ACTION_TOKEN[:10]}..., got {request.headers.get('X-App-Token', '')[:10]}...")
        return jsonify(error="Token expired. Please refresh the page."), 403


@app.after_request
def response_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    )
    return response


@app.get("/")
def index():
    if not all(key in session for key in REQUIRED_SETTINGS):
        return render_template("login.html", token=ACTION_TOKEN)
    return render_template(
        "export.html", token=ACTION_TOKEN,
        email=session.get("jira_email", "")
    )


@app.get("/api/token")
def get_token():
    """Return the current valid security token."""
    logging.debug(f"📋 Token requested: {ACTION_TOKEN[:10]}...")
    return jsonify(token=ACTION_TOKEN), 200


@app.post("/api/connect")
def connect():
    logging.debug("🔵 /api/connect endpoint called")
    payload = request.get_json(silent=True) or {}
    logging.debug(f"📦 Received payload: {list(payload.keys())}")
    
    email = str(payload.get("email", "")).strip()
    api_token = str(payload.get("api_token", "")).strip()
    base_url = str(payload.get("base_url", "")).strip()

    logging.debug(f"📝 Credentials - Email: {email}, URL: {base_url}, Token: {'*' * 10}")

    if not email or not api_token or not base_url:
        logging.warning("❌ Missing required fields")
        return jsonify(error="All fields are required."), 400
    if not re.match(r"^https?://", base_url):
        logging.warning("❌ Invalid URL format")
        return jsonify(error="Base URL must start with http:// or https://"), 400

    logging.info("🔐 Testing Jira connection...")
    jira = JiraSession(email, api_token, base_url)
    if not jira.test_connection():
        logging.error("❌ Connection test failed")
        jira.close()
        return jsonify(error="Connection failed. Check your credentials."), 401

    logging.info("✅ Connection successful! Saving to session...")
    session["jira_email"] = email
    session["jira_api_token"] = api_token
    session["jira_base_url"] = base_url
    logging.info("✅ Session saved. Returning success response.")
    return jsonify(success=True), 200


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify(success=True), 200


@app.get("/api/projects")
def projects():
    jira = get_jira_session()
    if not jira:
        return jsonify(error="Not connected."), 401
    try:
        projects = jira.get_projects()
        jira.close()
        return jsonify(projects=projects), 200
    except Exception as e:
        jira.close()
        return jsonify(error=str(e)), 500


@app.get("/api/statuses")
def statuses():
    jira = get_jira_session()
    if not jira:
        return jsonify(error="Not connected."), 401
    try:
        project_key = request.args.get("project")
        if not project_key:
            return jsonify(error="Project key is required."), 400
        
        status_list = jira.get_project_statuses(project_key)
        logging.debug(f"📊 Statuses for {project_key}: {status_list}")
        jira.close()
        return jsonify(statuses=status_list), 200
    except Exception as e:
        logging.error(f"❌ Error getting statuses: {str(e)}")
        jira.close()
        return jsonify(error=str(e)), 500


@app.get("/api/fields")
def fields():
    jira = get_jira_session()
    if not jira:
        return jsonify(error="Not connected."), 401
    try:
        field_map = jira.get_field_names()
        standard_fields = ["key", "summary", "assignee", "status"]
        custom_fields = [
            (field_id, name) for field_id, name in field_map.items()
            if field_id.startswith("customfield_")
        ]
        custom_fields.sort(key=lambda x: x[1])
        jira.close()
        return jsonify(
            standard=standard_fields,
            custom=[(f_id, f_name) for f_id, f_name in custom_fields]
        ), 200
    except Exception as e:
        jira.close()
        return jsonify(error=str(e)), 500


@app.post("/api/export")
def export_excel():
    payload = request.get_json(silent=True) or {}
    projects = payload.get("projects", [])
    start_date = payload.get("start_date", "")
    end_date = payload.get("end_date", "")
    columns = payload.get("columns", [])
    statuses = payload.get("statuses", [])

    logging.debug(f"📥 Export request received: projects={projects}, start_date={start_date}, end_date={end_date}, columns={columns}")

    if not projects or not start_date or not end_date or not columns:
        return jsonify(error="Projects, dates, and columns are required."), 400

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        if start > end:
            raise ValueError("Start date must be on or before end date.")
    except ValueError as e:
        return jsonify(error=f"Invalid dates: {str(e)}"), 400

    jira = get_jira_session()
    if not jira:
        return jsonify(error="Not connected."), 401

    try:
        # Build fields to fetch based on selected columns
        fields_to_fetch = set(JIRA_FIELDS_API)
        field_map = jira.get_field_names()
        
        # Map column names to field IDs
        for col in columns:
            # Check if it's a custom field
            field_id = next(
                (fid for fid, fname in field_map.items() if fname == col and fid.startswith("customfield_")),
                None
            )
            if field_id:
                fields_to_fetch.add(field_id)
                logging.debug(f"🔧 Added custom field '{col}' ({field_id}) to fetch list")
        
        fields_list = list(fields_to_fetch)
        logging.debug(f"📦 Fields to fetch: {fields_list}")
        
        project_list = ", ".join(projects)
        jql = f'project in ({project_list}) AND created >= "{start.isoformat()}" AND created <= "{end.isoformat()}"'
        
        logging.debug(f"🔍 JQL Query: {jql}")
        issues = jira.search_issues(jql, fields_list)
        field_map = jira.get_field_names()

        workbook = Workbook()
        workbook.remove(workbook.active)

        for sheet_name in ["Export", "Summary"]:
            worksheet = workbook.create_sheet(sheet_name)

        export_sheet = workbook["Export"]
        export_sheet.append(columns)

        for cell in export_sheet[1]:
            cell.font = Font(bold=True, size=11)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")

        for issue in issues:
            fields = issue.get("fields", {})
            row = []
            for col in columns:
                if col == "Issue key":
                    value = issue.get("key")
                elif col == "Summary":
                    value = fields.get("summary")
                elif col == "Assignee":
                    value = fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None
                elif col == "Status":
                    value = fields.get("status", {}).get("name") if fields.get("status") else None
                elif col == "Created":
                    value = fields.get("created")
                elif col == "Issue type":
                    value = fields.get("issuetype", {}).get("name") if fields.get("issuetype") else None
                else:
                    custom_field_id = next(
                        (fid for fid, fname in field_map.items() if fname == col),
                        None
                    )
                    value = fields.get(custom_field_id) if custom_field_id else None
                    if isinstance(value, dict):
                        value = value.get("name") or value.get("value")
                    elif isinstance(value, list):
                        value = ", ".join(str(v) for v in value)

                row.append(value)
            export_sheet.append(row)

        for col_idx, col_name in enumerate(columns, start=1):
            col_letter = chr(64 + col_idx) if col_idx <= 26 else "A"
            max_length = 0
            for row in export_sheet.iter_rows(min_col=col_idx, max_col=col_idx):
                for cell in row:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
            export_sheet.column_dimensions[col_letter].width = min(max_length + 2, 50)

        summary_sheet = workbook["Summary"]
        summary_sheet.append(["Metric", "Value"])
        summary_sheet.append(["Total Issues", len(issues)])
        summary_sheet.append(["Projects", ", ".join(projects)])
        summary_sheet.append(["Date Range", f"{start} to {end}"])

        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        jira.close()

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"jira_export_{uuid4().hex[:8]}.xlsx"
        )
    except Exception as e:
        jira.close()
        return jsonify(error=f"Export failed: {str(e)}"), 500


def main():
    parser = argparse.ArgumentParser(description="Jira Custom Export App")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--no-browser", action="store_true")
    arguments = parser.parse_args()

    server = None
    for port in range(arguments.port, min(arguments.port + 20, 65536)):
        try:
            server = make_server("127.0.0.1", port, app, threaded=True)
            break
        except (OSError, SystemExit):
            continue

    if server is None:
        raise RuntimeError("No available local port. Try --port with another port number.")

    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Jira Export Studio: {url}", flush=True)

    if not arguments.no_browser:
        threading.Timer(0.8, webbrowser.open, args=(url,)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
