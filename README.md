# Jira Export Studio

A standalone app for custom Jira data exports without pre-configuration.

## Quick Start (Windows)

1. **Setup**: Double-click `setup.bat` to create and configure the Python environment.
2. **Run**: Double-click `run.bat` to start the app. The browser opens automatically at `http://127.0.0.1:9000`.
3. **Connect**: Enter your Jira credentials (URL, email, API token) in the popup.
4. **Export**: Select projects, dates, and columns, then download as Excel.

## Quick Start (macOS / Linux)

1. **Setup**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Run**:
   ```bash
   source .venv/bin/activate
   python app.py
   ```

## Features

- **Login popup**: Enter Jira credentials before accessing the app. Credentials are stored in the session and not persisted to disk.
- **Custom Excel export**: Select projects, date ranges, and columns (standard and custom fields).
- **Fast session**: Credentials are session-only; disconnect anytime without storing sensitive data locally.

## Jira API Token

If you don't have an API token, create one at:
- **Atlassian Cloud**: https://id.atlassian.com/manage-profile/security/api-tokens

## Troubleshooting

If the app does not open in your browser automatically, navigate to `http://127.0.0.1:9000` manually.

If a port is busy, the app tries the next 20 ports automatically.

## Notes

- The app does not store credentials on disk.
- Each session is independent.
- Exports are limited to 5,000 issues per request.
