# 📌 Rita Suite – AI-Powered Knowledge Base with Django

## 🚀 Introduction

**Rita Suite** is a **Django-based application** that integrates **AI** to build and manage a knowledge base from multiple data sources. The project supports:

* Managing information from **Data.csv** and **knowledge.txt**
* Generating embeddings with **SentenceTransformer**
* Storing and querying with **FAISS Index**
* Integrating AI from Google Generative AI and other services

This project can be used to develop a **personal AI Assistant**, chatbot, or intelligent search system based on personal/group data.

---

## 📂 Project Structure

```
├── .env                      # Environment configuration (API keys, SECRET_KEY...)【15†source】
├── .gitignore                # Ignored files/folders for git commits【16†source】
├── Data.csv                  # Source data for AI knowledge
├── db.sqlite3                # Default Django database
├── knowledge_base.index       # FAISS index (embeddings)
├── knowledge_base_chunks.json # Processed knowledge chunks
├── manage.py                  # Django management script【18†source】
├── prepare_knowledge_base.py  # Script to generate knowledge base【19†source】
├── requirements.txt           # Python dependencies【20†source】
```

---

## ⚙️ Installation

### 1. Clone the project

```bash
git clone <repository-url>
cd rita_suite
```

### 2. Create virtual environment & install requirements

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 3. Setup environment variables

Create a `.env` file with required keys (see `.env.example`):

```env
SECRET_KEY=django-insecure-abcdefg12345!@#$%^&*()
DEBUG=True
GOOGLE_API_KEY=your_google_api_key
TIKTOK_API_KEY=your_tiktok_api_key
```

### 4. Run migrations and Django server

```bash
python manage.py migrate
python manage.py runserver
```

---

## 🧠 Build Knowledge Base

Run the script to generate embeddings and FAISS index:

```bash
python prepare_knowledge_base.py
```

This will create 2 files:

* `knowledge_base.index`
* `knowledge_base_chunks.json`

---

## 📦 Key Dependencies

* **Django** – Core web framework【20†source】
* **SentenceTransformers** – Text embeddings【19†source】
* **FAISS** – Efficient vector search【19†source】
* **Google Generative AI SDK** – AI integration【20†source】
* **Pandas, Numpy** – Data processing【20†source】
* **Gunicorn** – Production server【20†source】

See full list in [`requirements.txt`](requirements.txt).

---

## 🛡️ Security

* Do not commit `.env` (API keys, SECRET\_KEY, tokens)【16†source】
* Database (`db.sqlite3`) and media files are ignored【16†source】
* Use **DEBUG=False** in production

---

## 🚀 Deployment

Example with Gunicorn:

```bash
gunicorn rita_suite.wsgi:application --bind 0.0.0.0:8000
```

Combine with **Nginx** or **Docker** for production deployment.

---

## 👤 Author

* **Le Quy Phat (LQP)** – Data Analyst
* Email: [lequyphat0123@gmail.com](mailto:lequyphat0123@gmail.com)
* Website: [https://lequyphat.wuaze.com](https://lequyphat.wuaze.com)

---

## 📜 License

This project is developed for learning and research purposes. Make sure to check licenses when integrating third-party APIs/SDKs.

---

✨ *Rita Suite – Build your own AI brain!*
