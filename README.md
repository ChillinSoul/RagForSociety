# Rag For Society

A Retrieval-Augmented Generation tool targeted towards achieving SDG goal 1: End poverty in all its forms everywhere. The system provides accessible information about social aid and government assistance programs in Belgium.

## Features

- 🤖 Hybrid LLM approach combining 8B and 70B parameter models
- 🔍 Advanced RAG with multi-query generation and result fusion
- 🎯 Context-aware responses with source attribution
- 🗣️ Speech-to-text input support
- ♿ Comprehensive accessibility features
- 📊 Token usage monitoring
- 🌍 Optimized for French language social services content

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 16+
- npm
- Git

### Installation

1. Clone the repository

```bash
git clone https://github.com/axelbergergkist/RagForSociety.git
cd RagForSociety
```

2. Set up the backend

```bash
cd backend_ollama
pip install -r requirements.txt
```

3. Set up the frontend

```bash
cd ../next
npm install
```

### Running the Application

1. Start the backend server:

```bash
cd backend_ollama
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. In a new terminal, start the frontend development server:

```bash
cd next
npm run dev
```

3. Open your browser and navigate to `http://localhost:3000`

## Environment Variables

Create a `.env` file in the backend_ollama directory with:

```env
LANGCHAIN_API_KEY=your_langchain_api_key
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Model Configuration

The application supports multiple model configurations using either local inference with Ollama or cloud inference with Groq/ChatGPT.

### Cloud Setup Options (Recommended)

#### Groq (Recommended)

1. Create a Groq account at https://console.groq.com
2. Get your API key
3. Add to `.env`:

```env
GROQ_API_KEY=your_groq_api_key
```

4. Set `ACTIVE_CONFIG = "groq"` in `configs/llm_config.py`

#### ChatGPT Alternative

1. Get OpenAI API key from https://platform.openai.com
2. Add to `.env`:

```env
OPENAI_API_KEY=your_openai_api_key
```

3. Set `ACTIVE_CONFIG = "chatgpt"` in `configs/llm_config.py`

### Local Setup with Ollama

1. Install Ollama:

   - Mac: `curl -fsSL https://ollama.com/install.sh | sh`
   - Windows: Download from https://ollama.com/download/windows
   - Linux: `curl -fsSL https://ollama.com/install.sh | sh`

2. Pull required models:

```bash
# For 8B configuration
ollama pull llama3.1:8b

# For 70B configuration
ollama pull llama3.1:70b
```

3. Choose configuration in `configs/llm_config.py`:
   - `ollama-3.1`: 8B models only (lightweight)
   - `ollama-3.1-70b`: 70B models only (resource-intensive)
   - `ollama-hybrid`: Mixed 8B/70B approach (balanced)

### Configuration Comparison

| Config        | Pros                                   | Cons                      | Requirements        |
| ------------- | -------------------------------------- | ------------------------- | ------------------- |
| Groq          | Fastest inference, no local GPU needed | Requires API key          | None                |
| ChatGPT       | High reliability, great outputs        | Most expensive            | None                |
| Ollama 8B     | Free, minimal resources                | Lower quality             | 16GB RAM, 20GB disk |
| Ollama 70B    | Free, high quality                     | Very resource intensive   | 40GB RAM, 40GB disk |
| Ollama Hybrid | Free, good balance                     | Moderate resources needed | 40GB RAM, 46GB disk |

Configurations are defined in `backend_ollama/app/configs/llm_config.py`. The Groq configuration is recommended for most users as it provides the best balance of performance, cost, and ease of use.

## License

[MIT License](LICENSE)

## Authors

- Axel Bergiers
- Basil Mannaerts

## Acknowledgments

- ECAM Brussels Engineering School
- Belgian Government Social Services
- Sustainable Development Goals Initiative
