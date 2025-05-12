# 🧠 AI SEO Toolkit (Bulk SEO Auditor & Keyword Explorer)

This repository contains two powerful SEO tools built with **Streamlit** and powered by **Google Gemini 2.0 Flash**:

- 🔍 **AI Keyword Explorer**: Generates 100 high-quality SEO keywords with insights like CPC, SEO difficulty, and search intent.
- 🧪 **Bulk AI SEO Auditor**: Audits multiple URLs at once and generates human-readable reports, with Gemini-powered AI insights.

---

## 🚀 Features

### 1. AI Keyword Explorer
- Input a seed keyword to get 100 SEO-optimized suggestions.
- Includes search volume, CPC, keyword intent, and more.
- AI-curated and sorted by relevance.
- Download results as a CSV.

### 2. Bulk AI SEO Auditor
- Upload a `.txt` file containing multiple URLs.
- Automatically fetches and analyzes on-page SEO, metadata, content, links, and more.
- AI-generated detailed explanations, suggestions, and prioritizations.
- Displays both raw audit data and Gemini-powered analysis.

---

## 📁 Project Structure

```bash
.Project 1
├── helpers.py           # AI Analysis file
├── seo_audit.py         # SEO Analysis file
├── main1.py             # Main file for Project 1 
├── .env                 # env file for Google API

 .Project 2
├── main.py              # Main file for Project 2
├── .env                 # env file for Google APId

.Main_file
├── app.py               # Run both the project in one interface
├── Requirements.txt     # Dependencies Required
```
## 🛠️ Setup Instructions

To run this project locally, follow the steps below:

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-seo-toolkit.git
cd ai-seo-toolkit
```
### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv             # on windows
source venv/bin/activate        # On macOS/Linux
# activate the env
venv\Scripts\activate       
```

### 3. Install Required Dependencies    
```bash
pip install -r requirements.txt     
```
### 4. Create a .env File 
```bash
GEMINI_API_KEY=your_gemini_api_key_here    
```

## 🛠️ How to Run the Apps

To run this project make sure the virtual environment is set to the one you made and then run this code
```bash
streamlit run app.py
```
