# 13F Institutional Data Management Console

A streamlined web application for acquiring, organizing, and analyzing SEC 13F filing datasets.

## Features

- **Data Management**: Download 13F-HR filings by CIK and Quarter.
- **Auto Monitor**: Track specific institutional investors and automatically download new filings.
- **Analytics Dashboard**: Analyze holdings changes and options positions with interactive visualizations.

## Deployment & Setup

### Prerequisites

- **Python Version**: Python 3.9 or higher is recommended.
- **OS**: macOS / Linux / Windows.

### 1. Clone & Prepare
Ensure you are in the project root directory:
```bash
cd 13f_web_new
```

### 2. Install Dependencies
It is recommended to use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start the Flask Backend
Run the application using the following command:
```bash
python3 app.py
```
The server will start on `http://127.0.0.1:5000` by default.

## Usage

Access the following modules via your browser:

- **Management Console**: [http://localhost:5000/](http://localhost:5000/) - Main hub for downloading data.
- **Auto Monitor**: [http://localhost:5000/monitor](http://localhost:5000/monitor) - Manage entity watchlists and automated tracking.
- **Analytics**: [http://localhost:5000/dashboard](http://localhost:5000/dashboard) - Deep dive into filing details and position analysis.

## Project Structure

- `app.py`: Main Flask backend server and API endpoints.
- `console.html`: Management console portal.
- `monitor.html`: Automated monitoring interface.
- `dashboard.html`: Analytics dashboard.
- `EDGAR/`: Core logic for SEC filing downloading and extraction.
- `EDGAR/JSON_Reports/`: Processed filing data in JSON format.
- `EDGAR/SEC_Filings/`: Raw filing documents.

## Configuration

- **API Access**: The system uses the SEC EDGAR API. Ensure you have stable internet access.
- **Monitor Config**: Tracked entities are saved in `EDGAR/monitor_config.json`.
