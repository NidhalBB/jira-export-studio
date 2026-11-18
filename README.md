# Jira Export Studio

A web-based application to export Jira issues to Excel with custom field selection and formatting.

## 📋 Features

- **Connect to Jira Cloud**: Secure connection using email and API token
- **Project Selection**: Browse and select projects to export from
- **Flexible Field Selection**: 
  - Standard fields always included (Issue Key, Summary, Assignee, Status, Created)
  - Searchable custom fields with dual-list selector
  - Move fields between available and selected lists
- **Advanced Filtering**:
  - Date range selection (created between dates)
  - Status transitions tracking (optional)
  - Real-time search through custom fields
- **Professional Excel Export**:
  - Formatted headers with bold font and gray background
  - Auto-adjusted column widths
  - Summary sheet with metadata
  - Support for 5000+ issues

## 🚀 Quick Start

### Requirements
- Python 3.8+
- Jira Cloud instance with API token

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/NidhalBB/jira-export-studio.git
   cd jira-export-studio
   ```

2. **Create virtual environment** (optional but recommended)
   ```bash
   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```
   
   Or use the provided scripts:
   ```bash
   # Linux/macOS
   ./run.sh
   
   # Windows
   run.bat
   ```

5. **Open in browser**
   ```
   http://127.0.0.1:9000
   ```

## 🔐 Credentials

### Getting Your Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token (save it securely!)

### In the Application

1. Enter your Jira email (e.g., `user@company.com`)
2. Paste your API token
3. Enter your Jira instance URL (e.g., `https://company.atlassian.net`)
4. Click "Connect" to test the connection

## 📊 Usage

### Export Data

1. **Connect to Jira** using your credentials
2. **Select Projects**: Check one or more projects
3. **Choose Fields**:
   - Standard fields are pre-selected (checked disabled)
   - Search and select custom fields from the right panel
   - Uncheck to remove fields from the left panel
4. **Set Date Range**: Select "From" and "To" dates
5. **Optional - Status Transitions**: Select statuses to include transition dates
6. **Export**: Click "Export to Excel" to download

### Excel Output

The exported file contains:
- **Export sheet**: All selected data with proper formatting
- **Summary sheet**: Total issues count, project list, date range

## 🛠️ Configuration

### Environment Variables (Optional)

Create a `.env` file for default values:
```
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_token_here
JIRA_BASE_URL=https://company.atlassian.net
```

### Application Settings

Edit `app.py` to modify:
- `PAGE_SIZE` (default: 100 issues per page)
- `REQUEST_TIMEOUT_SECONDS` (default: 30)
- `MAX_CONTENT_LENGTH` (default: 65MB)

## 🔧 Technical Details

### Architecture

```
├── app.py                 # Flask application & Jira API integration
├── templates/
│   ├── login.html        # Login page
│   └── export.html       # Export configuration page
├── static/
│   ├── login.js          # Login form handling
│   ├── export.js         # Export form logic
│   └── style.css         # Styling
└── requirements.txt      # Python dependencies
```

### API Endpoints

- `POST /api/connect` - Test Jira connection and save credentials
- `GET /api/token` - Get fresh security token
- `GET /api/projects` - List available projects
- `GET /api/fields` - Get standard and custom fields
- `GET /api/statuses` - Get statuses for selected projects
- `POST /api/export` - Export issues to Excel

### Key Technologies

- **Flask**: Web framework
- **Requests**: HTTP library for Jira API
- **openpyxl**: Excel file generation
- **Pandas**: Data handling

## 🐛 Troubleshooting

### "Unbounded JQL queries are not allowed"
- Ensure you have selected at least one project and date range
- Check that dates are in correct format (YYYY-MM-DD)

### "Invalid request payload"
- Verify custom fields exist in your Jira instance
- Check that field names don't have special characters

### "400 Client Error: Bad Request"
- Ensure your API token is valid (create a new one if needed)
- Verify your Jira instance URL is correct
- Check that your email matches the Jira account

### No data showing after export
- Verify issues exist in selected projects within the date range
- Check project keys are correct
- Review browser console for errors (F12)

## 📝 Notes

### Jira API
- Uses Jira Cloud REST API v3
- Pagination via cursor-based `nextPageToken` (not offset)
- Maximum 5000 issues per export
- Supports both standard and custom fields

### Field Support
- **Standard Fields**: Key, Summary, Assignee, Status, Created
- **Custom Fields**: Dynamically loaded from your Jira instance
- **Limitations**: Some field types may not export perfectly (linked fields, etc.)

### Performance
- Typical export: 100-500 issues in 2-5 seconds
- Large exports (1000+ issues) may take longer
- Results are cached in browser session

## 📄 License

This project is provided as-is for internal use.

## 👤 Author

Nidhal Ben Brahim

## 🤝 Contributing

For bug reports, feature requests, or improvements, please open an issue.

---

**Built with** ❤️ **using Flask and Jira API**
