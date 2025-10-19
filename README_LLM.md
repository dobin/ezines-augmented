# Phrack Article Summarizer

This script uses OpenAI's ChatGPT API to automatically summarize Phrack ezine articles.

## Setup

1. Install required dependencies:
```bash
pip install openai
```

2. Set your OpenAI API key as an environment variable:
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"

# Windows CMD
set OPENAI_API_KEY=your-api-key-here

# Linux/Mac
export OPENAI_API_KEY=your-api-key-here
```

## Usage

### Test Mode (3 Random Articles)
```bash
python phrack-llm.py --test
```

### Process All Articles
```bash
python phrack-llm.py
```

### Custom Prompt
```bash
python phrack-llm.py --prompt "Provide a one-sentence summary of this article"
```

### Specify Output File
```bash
python phrack-llm.py --output my_summaries.json
```

### Combined Options
```bash
python phrack-llm.py --test --prompt "Brief summary" --output test_results.json
```

## Output

The script generates a JSON file with the following structure:
```json
{
  "1/1.txt": {
    "file": "/path/to/file",
    "summary": "AI-generated summary text...",
    "length": 2262
  },
  ...
}
```

## Features

- **Test Mode**: Process only 3 randomly selected articles for testing
- **Custom Prompts**: Specify your own summarization instructions
- **Progress Tracking**: See real-time progress as articles are processed
- **Error Handling**: Gracefully handles file reading and API errors
- **JSON Output**: Structured output for easy integration with other tools

## Cost Considerations

The script uses `gpt-4o-mini` by default for cost efficiency. You can modify the model in the code:
- `gpt-4o-mini` - Most cost-effective
- `gpt-3.5-turbo` - Faster, cheaper
- `gpt-4` - Best quality, more expensive

## Example Prompts

Here are some example prompts you can use:

**Technical Focus:**
```
python phrack-llm.py --prompt "List the main technical vulnerabilities or exploits discussed in this article"
```

**Historical Context:**
```
python phrack-llm.py --prompt "Explain the historical significance of this article in hacker culture and when it was likely written"
```

**One-Liner:**
```
python phrack-llm.py --prompt "Summarize this article in exactly one sentence"
```

**Beginner-Friendly:**
```
python phrack-llm.py --prompt "Explain this article in simple terms that a beginner could understand"
```
