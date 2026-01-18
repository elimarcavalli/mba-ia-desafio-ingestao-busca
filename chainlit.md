# 🤖 Sistema de Busca Semântica (RAG)

**MBA Engenharia de Software com IA - Full Cycle**

---

## 📖 Sobre o Projeto

Este é um sistema de **Retrieval-Augmented Generation (RAG)** capaz de:

- 📄 **Ingerir** documentos PDF, processando e armazenando embeddings
- 🔍 **Buscar** informações semanticamente relevantes
- 💬 **Responder** perguntas utilizando apenas o contexto dos documentos

---

## ✨ Principais Funcionalidades

- 🔍 **Busca Semântica** com PostgreSQL + pgvector
- 🏗️ **Clean Architecture** (Hexagonal)
- 🔌 **Multi-Provider** (OpenAI / Google Gemini)
- ⚡ **Alta Performance** com processamento assíncrono

---

## 💡 Como Usar

1. **Faça upload** de um documento PDF usando o ícone de anexo 📎
2. **Aguarde** o processamento do documento
3. **Pergunte** sobre o conteúdo do documento

> O assistente responderá apenas com informações dos documentos carregados.

---

## 🔐 Autenticação

- Novos usuários são criados automaticamente no primeiro login
- Usuário: mínimo 3 caracteres
- Senha: mínimo 4 caracteres

---

## 🛠️ Tecnologias

| Componente | Tecnologia |
|------------|------------|
| Backend | Python 3.12+ |
| Framework | LangChain |
| Vector DB | PostgreSQL + pgvector |
| Interface | Chainlit |
| Container | Docker |

---

**Desenvolvido por [Elimar Cavalli](https://github.com/elimarcavalli)**

*Desafio do MBA em Engenharia de Software com IA - Full Cycle*