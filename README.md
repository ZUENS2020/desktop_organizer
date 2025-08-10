# Amap Search Agent with Gemini

This is a simple command-line agent that uses the Amap API to search for places and the Google Gemini API to provide intelligent search and summarization.

## Features

-   Natural language understanding of search queries using Gemini.
-   Location search powered by the Amap Web Service API.
-   User-friendly summarization of search results.

## Setup

### 1. Install Dependencies

Clone the repository and install the required Python packages:

```bash
pip install -r requirements.txt
```

### 2. Set API Keys

This agent requires API keys for both Amap and Google Gemini. You need to set them as environment variables.

-   **`AMAP_API_KEY`**: Your Amap API key. **Important:** This must be a key configured for **Web Service (Web服务)** access in the [Amap Console](https://console.amap.com/dev/key/app).
-   **`GEMINI_API_KEY`**: Your Google AI (Gemini) API key. You can get one from [Google AI Studio](https://aistudio.google.com/).

You can set the environment variables in your shell like this:

**On Linux or macOS:**
```bash
export AMAP_API_KEY="YOUR_AMAP_API_KEY"
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

**On Windows (Command Prompt):**
```bash
set AMAP_API_KEY="YOUR_AMAP_API_KEY"
set GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
```

Replace `"YOUR_AMAP_API_KEY"` and `"YOUR_GEMINI_API_KEY"` with your actual keys.

## Usage

Run the agent from your command line, passing your search query as an argument. The query should be enclosed in quotes.

### Example

```bash
python amap_agent.py "restaurants in San Francisco"
```

Or, using a query in Chinese:

```bash
python amap_agent.py "北京的麦当劳"
```

The agent will then print a summary of the search results.
