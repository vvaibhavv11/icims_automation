# iCIMS Job Application Automation

An intelligent job application automation tool that uses AI to fill out multi-page job application forms on iCIMS-powered career sites. The system extracts form fields, processes them using Google's Gemini AI model with resume data, and automatically fills out the application forms.

## 🚀 Features

- **AI-Powered Form Filling**: Uses Google Gemini 2.5 Flash model to intelligently fill form fields based on resume content
- **Multi-Page Navigation**: Automatically handles multi-page application forms (typically 4-5 pages)
- **Resume Upload**: Supports PDF resume upload and processing
- **Intelligent Field Detection**: Handles various input types including text, email, select, checkbox, radio, date, and file uploads
- **Cookie Management**: Automatically handles cookie consent banners
- **Stealth Mode**: Uses playwright-stealth to avoid detection by anti-bot measures
- **iframe Support**: Handles complex nested iframe structures common in iCIMS applications

## 📋 Prerequisites

- Python 3.13+
- Google AI API key (for Gemini model)
- Chromium browser (managed by Playwright)

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/vvaibhavv11/icims_automation
cd icims_automation
```

2. Install dependencies (using uv):
```bash
uv sync
```

3. Install Playwright browsers:
```bash
uv run python -m playwright install
```

4. Set up your Google API key and job URL in a `.env` file (see `.env.example` for format)

## 📁 Project Structure

```
icims_automation/
├── main.py          # Main application logic and orchestration
├── core.py          # Core automation functions (form extraction, data entry)
├── prompt.py        # AI system prompts and instructions
├── pyproject.toml   # Project dependencies and configuration
└── README.md        # This file
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root (see `.env.example`):
```
GOOGLE_GEMINI_API_KEY="your-actual-api-key-here"
JOB_URL="https://your-target-job-url"
```

### Resume Path
Update the resume file path in `core.py`:
```python
with open("/path/to/your/resume.pdf", "rb") as f:
    b64 = f.read()
```

## 🎯 How It Works

### 1. **Page Navigation**
- Opens the job application page using Playwright with stealth mode
- Handles cookie consent banners automatically
- Clicks the "Apply" button to start the application process

### 2. **Form Field Extraction**
- Extracts HTML content from iCIMS iframe structures
- Identifies various form field types:
  - Text inputs and textareas
  - Email fields
  - Select dropdowns (regular and special)
  - Checkboxes and radio buttons
  - Date fields
  - File upload fields

### 3. **AI Processing**
- Sends extracted form HTML and resume (PDF) to Google Gemini AI
- AI analyzes the form requirements and matches them with resume data
- Returns structured field-value pairs for form filling

### 4. **Form Filling**
- Automatically fills form fields with AI-generated responses
- Handles file uploads with the provided resume
- Manages special select elements and complex form controls

### 5. **Page Progression**
- Identifies and clicks appropriate navigation buttons (Next, Submit, etc.)
- Continues until all pages are processed or no more navigation options exist

## 🤖 AI Behavior

The system uses carefully crafted prompts to ensure:

- **Minimum Required Fields**: Only fills required fields to progress through pages
- **Resume-Based Answers**: Prioritizes information from the uploaded resume
- **Smart Defaults**: Uses intelligent defaults for fields without clear resume matches
- **Work Authorization**: Automatically handles visa/authorization questions appropriately
- **File Handling**: Manages resume uploads and file input fields

## 📦 Dependencies

- **playwright**: Web browser automation
- **playwright-stealth**: Anti-detection measures
- **pydantic-ai**: AI model integration and structured outputs
- **nest-asyncio**: Async/await support
- **pydantic**: Data validation and modeling
- **uv**: Fast Python package installer and dependency manager
- **python-dotenv**: Loads environment variables from `.env` files

## 🚀 Usage

1. Update the configuration (`.env` file, resume path)
2. Run the application:
```bash
uv run main.py
```

The application will:
- Open a Chromium browser window
- Navigate to the specified job URL
- Automatically fill out the multi-page application form
- Continue until completion or until no more pages are available