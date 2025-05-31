# Plagiarism Detection Tool Using Machine Learning

A full-stack web application for detecting textual plagiarism using machine learning. This tool uses a React frontend and a Flask backend, leveraging TF-IDF-based cosine similarity, Google Custom Search API, and PDF report generation.

---

## 🚀 Features

- Upload or paste text to detect plagiarism
- Accepts `.txt`, `.pdf`, and `.docx` files
- Uses Google Custom Search to scan the web
- Calculates similarity using cosine similarity (TF-IDF)
- Generates detailed charts and downloadable PDF reports
- Caches results for performance (1-hour memoization)

---

## 🛠️ Technologies Used

### Client (Frontend)
- React
- react-router-dom
- axios
- Firebase

### Server (Backend)
- Python
- Flask
- python-dotenv
- flask-caching
- FPDF (for PDF report)
- matplotlib (for charts)
- scikit-learn (cosine similarity)
- python-docx, PyPDF2, BeautifulSoup, google-api-python-client

---

## 🧪 API Endpoints

### `POST /api/detect-plagiarism`

Accepts text or a file upload to perform plagiarism detection.

**Form fields:**
- `text`: Optional. Raw text input.
- `file`: Optional. File upload (`.txt`, `.pdf`, `.docx`).

**Returns:**
- A downloadable PDF file (`plagiarism_report.pdf`) with results, highlighted content, and similarity charts.

---

## 🧩 Installation

### 📁 Backend

```bash
pip install flask python-dotenv flask-caching matplotlib fpdf PyPDF2 python-docx google-api-python-client beautifulsoup4 scikit-learn
python -m venv venv
.\venv\scripts\activate
