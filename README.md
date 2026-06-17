# 📄🧠 DocMind - RAG Semantic Search System

> **Your intelligent assistant for documents** — PDF, TXT, CSV, HTML, JSON, Markdown and DOCX. Ask questions and get accurate answers based on your documents!

![Version](https://img.shields.io/badge/System%20version-1.0.0-informational.svg)
![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-Integration-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg)
![Docker](https://img.shields.io/badge/Docker-Container-2496ED.svg)

---

## 💡 What is DocMind?

**DocMind transforms any document into an intelligent assistant that answers your questions instantly.** No more manual searching through lengthy documents!

Imagine having an expert who has read your entire document and can answer any question about it in seconds - that's DocMind.

### 🆚 Why is RAG superior?

| Approach               | Limitations                                   | DocMind (RAG)                                |
| ---------------------- | --------------------------------------------- | -------------------------------------------- |
| **Keyword search**     | Finds only exact terms, ignores context       | ✅ Understands synonyms and semantic context |
| **ChatGPT directly**   | Invents information, no access to your docs   | ✅ Answers based 100% on your document       |
| **Manual reading**     | Slow, tiring, error-prone                     | ✅ Instant, accurate, never forgets          |
| **Traditional Ctrl+F** | Literal, doesn't understand complex questions | ✅ Answers questions in natural language     |

### 🔄 How it works:

1. 📄 You upload a document (PDF, TXT, CSV, HTML, JSON, MD or DOCX)
2. 🧠 The system processes and "understands" the content using vector embeddings
3. 💬 You ask questions in natural language
4. 🔍 The system searches for the most semantically relevant passages
5. ✨ The AI generates a precise answer based only on the document

---

## 🎯 What is it for?

**Practical use cases:**

- 📚 **Students**: Ask questions about textbooks, books, and scientific articles
- 💼 **Professionals**: Quickly consult contracts, reports, and technical documentation
- 🔬 **Researchers**: Extract information from papers and academic documents
- 📋 **Companies**: Analyze manuals, policies, and corporate documents
- 🎓 **Teachers**: Prepare materials and clarify doubts about extensive content

**Example questions:**

- "What is the main topic of this document?"
- "What does the text say about [specific subject]?"
- "Summarize the main points"
- "What are the conclusions presented?"

---

## 🚀 How to Get Started

**Requirements:** [Python 3.12+](https://www.python.org/downloads/) and [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed

It's super simple! Just 3 steps:

```bash
# 1. Clone the repository
git clone https://github.com/elimarcavalli/mba-ia-desafio-ingestao-busca.git

# 2. Enter the folder
cd mba-ia-desafio-ingestao-busca

# 3. Run the system
python3 main.py
```

### 📺 What you'll see when starting

When you run `python3 main.py`, an interactive menu will appear:

<pre>
<span style="color: #d946ef; font-weight: bold;">=== MBA Software Engineering with AI - Project Manager ===
GitHub: https://github.com/elimarcavalli/mba-ia-desafio-ingestao-busca.git</span>
1. Start System (Normal)
2. Force Restart (Kill existing + Start)
3. Quick Launch (Skip checks)
4. Stop All Processes (Kill Only)
5. Reset System (Wipe User Data & Config Only)
6. Exit

Select option (1-6):
</pre>

**For first run, choose option `1`**

The system will:

- ✅ Automatically create Python virtual environment
- ✅ Install all necessary dependencies
- ✅ Configure PostgreSQL database via Docker
- ✅ Ask for your API key (OpenAI or Google Gemini)
- ✅ Generate the Chainlit auth secret used to sign session tokens
- ✅ Start the web interface at `http://localhost:8000`

**Done!** In less than 2 minutes you'll be chatting with your documents! 🎉

> **Login:** the first time you open the web UI, just type a new username and password — your account is created automatically (Argon2id-hashed password, per-user chat history). Returning users sign in with the same form.

---

## 🖥️ CLI Mode

Prefer the terminal? It also works without the web UI:

```bash
# Ingest the document defined by PDF_PATH in .env (default: document.pdf)
python3 src/ingest.py

# Ingest a specific file (replaces what was ingested before)
python3 src/ingest.py path/to/file.pdf

# Add a file while keeping previously ingested ones (ask across all of them)
python3 src/ingest.py path/to/another.pdf --append

# Ask a single question and exit (one-shot)
python3 src/chat.py "What is the revenue of company X?"

# Or start an interactive chat session
python3 src/chat.py
```

> 💡 The scripts automatically use the project's `venv`. Don't have one yet? Run `python3 main.py` once (option 1), or set up manually:

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env        # then fill in your API key
docker compose up -d
```

---

## ⚙️ Prerequisites

- **[Python 3.12+](https://www.python.org/downloads/)** installed
- **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** installed and running
- **API Key** from [OpenAI](https://platform.openai.com/api-keys) or [Google Gemini](https://aistudio.google.com/app/apikey)

> 💡 **Tip**: The `main.py` script checks everything automatically and guides you if something is missing!

---

## 🎨 Web Interface

After starting, access `http://localhost:8000` and you'll see a modern and intuitive interface where you can:

- 📎 **Drag and drop** documents for upload
- 💬 **Ask questions** in natural language
- 📚 **Manage** multiple documents
- 🔍 **View history** of conversations
- ⚡ **Get answers** in seconds

---

## 🛠️ Technologies

| Component        | Technology             |
| ---------------- | ---------------------- |
| Language         | Python 3.12+           |
| AI Framework     | LangChain              |
| Vector Database  | PostgreSQL + pgvector  |
| Web Interface    | Chainlit               |
| Containerization | Docker                 |
| LLM Providers    | OpenAI / Google Gemini |

---

## 🏗️ Architecture

The system follows **Clean Architecture** (Hexagonal Architecture):

- **Domain**: Pure business rules, no external dependencies
- **Application**: Use cases (Ingestion and Search)
- **Infrastructure**: Adapters for database and AI APIs
- **Presentation**: Web interface (Chainlit) and CLI

This ensures:

- ✅ Testable and maintainable code
- ✅ Easy switching of AI providers
- ✅ Scalability and performance

---

## 📖 Documentation Index

### Guides & References

| # | Document | Description |
|---|----------|-------------|
| 1 | [Architecture](docs/en-US/1-ARCHITECTURE-en-US.md) | Clean/Hexagonal Architecture overview |
| 2 | [RAG Pipeline](docs/en-US/2-RAG-PIPELINE-en-US.md) | End-to-end ingestion and retrieval flow |
| 3 | [AI Models](docs/en-US/3-AI-MODELS-en-US.md) | LLM and embedding provider configuration |
| 4 | [pgvector](docs/en-US/4-PGVECTOR-en-US.md) | Vector database setup and tuning |
| 5 | [Extending the System](docs/en-US/5-EXTENDING-SYSTEM-en-US.md) | How to add new loaders, providers and features |
| — | [AGENTS.md](AGENTS.md) | Instructions for AI assistants |

### Screenshots

| CLI — Ingest & Chat |
|---------------------|
| ![CLI](docs/screenshots/0-cli-ingest-chat.png) |

| Login | Home |
|-------|------|
| ![Login](docs/screenshots/1-login.png) | ![Home](docs/screenshots/2-home.png) |

| Chat — PDF upload | Chat — Question 1 |
|-------------------|-------------------|
| ![PDF upload](docs/screenshots/3-chat1-pdf.png) | ![Question 1](docs/screenshots/4-chat2-1.png) |

| Chat — Answer | Chat — Follow-up |
|---------------|------------------|
| ![Answer](docs/screenshots/5-chat2-2.png) | ![Follow-up](docs/screenshots/6-chat2-3.png) |

| Multi-document chat (Markdown) |
|-------------------------------|
| ![Multi-doc](docs/screenshots/7-chat3-multi-md.png) |

---

## 📄 License

This project is under the MIT license.

---

**Built by [Elimar Cavalli](https://github.com/elimarcavalli)**

_MBA Challenge in Software Engineering with AI - Full Cycle_
