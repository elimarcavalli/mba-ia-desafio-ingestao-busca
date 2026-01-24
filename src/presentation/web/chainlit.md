# 🤖 Sistema de Busca Semântica (RAG) | Semantic Search System

**MBA Engenharia de Software com IA - Full Cycle** | **MBA Software Engineering with AI - Full Cycle**

---

## 📖 Sobre o Projeto | About the Project

🇧🇷 Este é um sistema de **Retrieval-Augmented Generation (RAG)** capaz de:

- 📄 **Ingerir** documentos PDF, processando e armazenando embeddings
- 🔍 **Buscar** informações semanticamente relevantes
- 💬 **Responder** perguntas utilizando apenas o contexto dos documentos

🇺🇸 This is a **Retrieval-Augmented Generation (RAG)** system capable of:

- 📄 **Ingesting** PDF documents, processing and storing embeddings
- 🔍 **Searching** semantically relevant information
- 💬 **Answering** questions using only the context from documents

---

## ✨ Principais Funcionalidades | Key Features

- 🔍 **Busca Semântica | Semantic Search** with PostgreSQL + pgvector
- 🏗️ **Clean Architecture** (Hexagonal)
- 🔌 **Multi-Provider** (OpenAI / Google Gemini)
- ⚡ **Alta Performance | High Performance** with asynchronous processing

---

## 💡 Como Usar | How to Use

🇧🇷 **Português:**
1. **Faça upload** de um documento PDF usando o ícone de anexo 📎
2. **Aguarde** o processamento do documento
3. **Pergunte** sobre o conteúdo do documento

🇺🇸 **English:**
1. **Upload** a PDF document using the attachment icon 📎
2. **Wait** for document processing
3. **Ask** questions about the document content

> 🇧🇷 O assistente responderá apenas com informações dos documentos carregados.
> 🇺🇸 The assistant will only respond with information from loaded documents.

---

## 🛠️ Tecnologias | Technologies

| Componente | Tecnologia |
|------------|------------|
| Backend | Python 3.12+ |
| Framework | LangChain |
| Vector DB | PostgreSQL + pgvector |
| Interface | Chainlit |
| Container | Docker |

---

**Desenvolvido por | Developed by [Elimar Cavalli](https://github.com/elimarcavalli)**

*Desafio do MBA em Engenharia de Software com IA - Full Cycle*
