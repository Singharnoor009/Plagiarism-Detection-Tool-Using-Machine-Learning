import os
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from bs4 import BeautifulSoup
import re
import matplotlib.pyplot as plt 
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from googleapiclient.discovery import build
from fpdf import FPDF


import os
import re
import unicodedata
import requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from fpdf import FPDF
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from fpdf import FPDF
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from docx import Document
from googleapiclient.discovery import build
from flask_caching import Cache


# Initialize Flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configure cache
app.config['CACHE_TYPE'] = 'simple'  # Use simple in-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 3600  # Cache timeout in seconds (1 hour)
cache = Cache(app)

# Set the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

# Ensure the uploads directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure the upload folder for Flask
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Normalize text to avoid encoding issues
def normalize_text(text):
    try:
        return unicodedata.normalize('NFKD', text).encode('utf-8', 'ignore').decode('utf-8')
    except UnicodeDecodeError:
        return text

# Cache the extracted text from URLs
@cache.memoize(timeout=3600)  # Cache for 1 hour
def extract_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove unwanted tags like <script> and <style>
        for script in soup(['script', 'style']):
            script.extract()

        text = soup.get_text()
        return normalize_text(re.sub(r'\s+', ' ', text.strip()))
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

@cache.memoize(timeout=3600)  # Cache PDF text extraction for 1 hour
def extract_text_from_pdf(file_path):
    try:
        # Open and read PDF file from local path
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()

        return normalize_text(re.sub(r'\s+', ' ', text.strip()))
    except Exception as e:
        print(f"Error processing PDF file at {file_path}: {e}")
        return None

# Function to extract text from .docx (Word) files
def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return None

# Function to extract text from .txt files
def extract_text_from_txt(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error extracting text from TXT: {e}")
        return None

# Cosine similarity using TF-IDF
def calculate_cosine_similarity(text1, text2):
    try:
        vectorizer = CountVectorizer(stop_words='english').fit([text1, text2])
        tfidf_matrix = vectorizer.transform([text1, text2])
        return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except Exception as e:
        print(f"Similarity error: {e}")
        return 0

# Allowed file extensions for upload
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Google Custom Search - Function to search both HTML and PDFs
def google_search(query, api_key, cse_id, num=2):
    service = build("customsearch", "v1", developerKey=api_key)
    all_results = []

    try:
        res_web = service.cse().list(q=query, cx=cse_id, num=num).execute()
        all_results.extend(res_web.get('items', []))

        res_pdf = service.cse().list(q=query, cx=cse_id, fileType='pdf', num=num).execute()
        all_results.extend(res_pdf.get('items', []))

    except Exception as e:
        print(f"Search error: {e}")

    # Check and filter out empty URLs
    return [result for result in all_results if 'link' in result]

# Plagiarism detection function with PDF handling
# def detect_plagiarism(content, api_key, cse_id):
#     plagiarized_sources = []
#     total_similarity_score = 0
#     total_sentences = 0

#     content = normalize_text(content)
#     sentences = re.split(r'(?<=[.!?])\s+', content)

#     for sentence in sentences:
#         sentence = sentence.strip()
#         if len(sentence) > 15:
#             print(f"🔍 Searching: {sentence[:40]}...")  # Preview of sentence
#             search_results = google_search(sentence, api_key, cse_id)

#             for result in search_results:
#                 url = result.get('link')
#                 title = result.get('title')

#                 if url.endswith('.pdf'):
#                     page_text = extract_text_from_pdf(url)
#                 else:
#                     page_text = extract_text_from_url(url)

#                 if page_text:
#                     truncated_page = page_text[:2000]
#                     cosine_sim = calculate_cosine_similarity(sentence, truncated_page)
#                     total_similarity_score += cosine_sim
#                     total_sentences += 1

#                     if cosine_sim > 0.5:
#                         plagiarized_sources.append({
#                             'sentence': sentence,
#                             'source_url': url,
#                             'source_title': title,
#                             'similarity_score': cosine_sim
#                         })

#     average_similarity_score = (total_similarity_score / total_sentences) * 100 if total_sentences > 0 else 0
#     return plagiarized_sources, average_similarity_score


def detect_plagiarism(content, api_key, cse_id):
    plagiarized_sources = []
    total_similarity_score = 0
    total_sentences = 0
    checked_urls = set()

    content = normalize_text(content)
    sentences = re.split(r'(?<=[.!?])\s+', content)

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 15:
            print(f"🔍 Searching: {sentence[:40]}...")  # Preview of sentence
            search_results = google_search(sentence, api_key, cse_id)

            for result in search_results:
                url = result.get('link')
                title = result.get('title')

                if not url or url in checked_urls:
                    continue

                # Mark this URL as checked to prevent redundant fetches
                checked_urls.add(url)

                # Try to extract full content
                if url.endswith('.pdf'):
                    page_text = extract_text_from_pdf(url)
                else:
                    page_text = extract_text_from_url(url)

                if not page_text:
                    continue

                # Compare the sentence with a chunk from the source to decide if it's worth checking full text
                truncated_page = page_text[:2000]
                sentence_similarity = calculate_cosine_similarity(sentence, truncated_page)

                if sentence_similarity > 0.5:
                    # Check full content similarity
                    full_doc_similarity = calculate_cosine_similarity(content, page_text)

                    if full_doc_similarity > 0.8:
                        print(f"✅ Full content match with {url} (similarity: {full_doc_similarity:.2f})")

                        plagiarized_sources.append({
                            'sentence': sentence,
                            'source_url': url,
                            'source_title': title,
                            'similarity_score': full_doc_similarity
                        })

                        # Short-circuit: full document match confirmed
                        average_similarity_score = full_doc_similarity * 100
                        return plagiarized_sources, average_similarity_score

                # Partial match fallback
                total_similarity_score += sentence_similarity
                total_sentences += 1

                if sentence_similarity > 0.5:
                    plagiarized_sources.append({
                        'sentence': sentence,
                        'source_url': url,
                        'source_title': title,
                        'similarity_score': sentence_similarity
                    })

    average_similarity_score = (total_similarity_score / total_sentences) * 100 if total_sentences > 0 else 0
    return plagiarized_sources, average_similarity_score


# Generate similarity chart
def generate_similarity_chart(plagiarized_sources):
    if plagiarized_sources:
        urls = [entry['source_url'] for entry in plagiarized_sources]
        scores = [entry['similarity_score'] for entry in plagiarized_sources]
        shortened_urls = [url if len(url) <= 30 else url[:30] + '...' for url in urls]

        plt.figure(figsize=(10, 6))
        plt.bar(shortened_urls, scores, color='blue')
        plt.ylabel('Similarity Score')
        plt.title('Similarity Scores by URL')
        plt.xticks(rotation=45, ha="right", fontsize=8)
        plt.tight_layout()

        chart_file = 'similarity_chart.png'
        plt.savefig(chart_file)
        plt.close()
        return chart_file
    return None

# Generate pie chart
def generate_pie_chart(average_similarity_score):
    labels = ['Original', 'Plagiarized']
    sizes = [100 - average_similarity_score, average_similarity_score]
    colors = ['green', 'red']
    explode = (0, 0.1)

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
    plt.axis('equal')

    pie_chart_file = 'average_similarity_pie_chart.png'
    plt.savefig(pie_chart_file)
    plt.close()
    return pie_chart_file

# Generate PDF report
def generate_pdf_report(content, plagiarized_sources, average_similarity_score, chart_file, pie_chart_file):
    if not content:
        print("No content to generate the report.")
        return None

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, txt="Plagiarism Report", ln=True, align='C')
    pdf.ln(10)

    # Insert pie chart
    if pie_chart_file:
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, txt="Plagiarism Breakdown:", ln=True, align='C')
        pdf.image(pie_chart_file, x=55, w=100)
        pdf.ln(10)

    # Section: Uploaded Content
    pdf.set_font("Arial", style='B', size=12)
    pdf.multi_cell(0, 10, txt="Uploaded Content:", align='L')
    pdf.set_font("Arial", size=12)
    pdf.ln(2)

    sentences = content.split('. ')
    for sentence in sentences:
        normalized_sentence = normalize_text(sentence.strip())
        plagiarized_entry = None

        # Use cosine similarity to detect plagiarized sentence
        for entry in plagiarized_sources:
            similarity = calculate_cosine_similarity(normalized_sentence, normalize_text(entry['sentence'].strip()))
            if similarity > 0.8:  # Threshold for match
                plagiarized_entry = entry
                break

        if plagiarized_entry:
            # Highlight entire sentence in red background
            pdf.set_fill_color(255, 0, 0)       # Red background
            pdf.set_text_color(255, 255, 255)   # White text
            pdf.multi_cell(0, 10, txt=sentence.strip(), align='L', fill=True)
            pdf.set_text_color(0, 0, 0)         # Reset to black
        else:
            pdf.multi_cell(0, 10, txt=sentence.strip(), align='L')

        pdf.ln(2)

    # Section: Sources of Plagiarized Text
    if plagiarized_sources:
        pdf.ln(5)
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, txt="Plagiarized Sources:", ln=True, align='L')
        pdf.set_font("Arial", size=12)
        for entry in plagiarized_sources:
            pdf.multi_cell(0, 10, txt=f"{entry['source_title']} ({entry['source_url']}) - Similarity: {entry['similarity_score']*100:.2f}%", align='L')

    # Save the PDF
    pdf_report = 'plagiarism_report.pdf'
    pdf.output(pdf_report)

    return pdf_report

# Route to handle plagiarism detection
@app.route('/api/detect-plagiarism', methods=['POST'])
def detect_plagiarism_api():
    text = request.form.get('text')
    file = request.files.get('file')

    content = None

    # Handle file upload
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract text from the file based on file extension
        if filename.endswith('.txt'):
            content = extract_text_from_txt(file_path)
        elif filename.endswith('.pdf'):
            content = extract_text_from_pdf(file_path)  # Ensure correct file path usage
        elif filename.endswith('.docx'):
            content = extract_text_from_docx(file_path)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

    # Handle direct text input
    elif text:
        content = text
    else:
        return jsonify({"error": "No content or file provided"}), 400

    if not content:
        return jsonify({"error": "Failed to extract text from the provided file or input."}), 400

    # Run plagiarism check
    api_key = "" # ---------API_KEY
    cse_id = ""  #  Custom Search Engine ID
    plagiarized_sources, average_similarity_score = detect_plagiarism(content, api_key, cse_id)

    # Generate charts and report
    chart_file = generate_similarity_chart(plagiarized_sources)
    pie_chart_file = generate_pie_chart(average_similarity_score)
    pdf_report = generate_pdf_report(content, plagiarized_sources, average_similarity_score, chart_file, pie_chart_file)

    # Return the PDF report as a downloadable file
    return send_file(pdf_report, as_attachment=True, download_name="plagiarism_report.pdf")


if __name__ == '__main__':
    app.run(debug=True)

