#!/usr/bin/env python3
"""
Ezine Article Summarizer using OpenAI ChatGPT API

This script processes ezine articles and generates summaries using OpenAI's ChatGPT.
Supports test mode (3 random articles) and full mode (all articles).
Can process any directory containing .txt files, including Phrack, 29a, cDc, and other ezines.
"""

import os
import sys
import json
import random
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from openai import OpenAI


PROMPT = """
you are a security researcher browsing a 
hacking ezine archive. you have extensive security knowledge.
You want to browse the phrack zine database, looking for interesting or still relevant articles. the short summary should give a quick overview to decide if its worth reading. Then the summary can be read to get the gist of it, without the fluff.

Answer in json, like {
    "reference": "",
    "title": "", 
    "authors: "",
    "date": "",
    "short_summary": "",
    "summary" 
}
Make sure it is a valid JSON, handling quotes in the text properly.

The following are found somewhere at the beginning of the file.

* Where "reference" is the zine and article reference like "Volume Two, Issue 12, Phile #6 of 11"
* Where "title" is the title
* "Authors" the author or authors
* "date" is the written date, if given in the article
* "historical_context": any historical context about the article, if any
* "target_audience": who would be interested in this article (hackers, phreakers, security professionals, etc.)
* "short_summary": Summarize the content in a few sentences
* "summary": Summarize the content in a 2-3 paragraphs maximum. Keep the style of the author here. Key technical concepts and techniques. 
"""


class PhackSummarizer:
    def __init__(self, api_key: Optional[str] = None, test_mode: bool = False, prompt: Optional[str] = None, directory: Optional[str] = None):
        """
        Initialize the Phrack summarizer.
        
        Args:
            api_key: OpenAI API key (reads from OPENAI_API_KEY env var if not provided)
            test_mode: If True, only process 3 random articles
            prompt: Custom prompt for summarization
            directory: Directory to search for articles (defaults to 'zines' subdirectory)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.test_mode = test_mode
        self.default_prompt = prompt or self._get_default_prompt()
        
        # Set the base directory to search for articles
        if directory:
            self.base_dir = Path(directory)
        else:
            # Default to 'zines' subdirectory in the script's parent directory
            script_dir = Path(__file__).parent
            self.base_dir = script_dir / 'zines'
        
        # Validate that the directory exists
        if not self.base_dir.exists():
            raise ValueError(f"Directory does not exist: {self.base_dir}")
        if not self.base_dir.is_dir():
            raise ValueError(f"Path is not a directory: {self.base_dir}")
        
    def _get_default_prompt(self) -> str:
        """Return the default summarization prompt."""
        return PROMPT

    def find_all_articles(self) -> List[Tuple[Path, str]]:
        """
        Find all .txt files in the specified directory structure.
        
        Returns:
            List of tuples (file_path, relative_path_string)
        """
        articles = []
        
        # Search recursively for .txt files
        for txt_file in self.base_dir.rglob('*.txt'):
            # Calculate relative path from base directory
            rel_path = txt_file.relative_to(self.base_dir)
            articles.append((txt_file, str(rel_path)))
        
        # Sort by the relative path for consistent ordering
        articles.sort(key=lambda x: x[1])
        return articles

    def read_article(self, file_path: Path) -> Optional[str]:
        """Read article content from file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None

    def summarize_article(self, content: str, custom_prompt: Optional[str] = None, max_retries: int = 3) -> Optional[str]:
        """
        Use OpenAI ChatGPT to summarize the article.
        
        Args:
            content: Article text content
            custom_prompt: Optional custom prompt to override default
            max_retries: Maximum number of retry attempts for API calls
            
        Returns:
            Summary text from ChatGPT
        """
        prompt = custom_prompt or self.default_prompt
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # or "gpt-3.5-turbo" for cheaper option
                    messages=[
                        {"role": "system", "content": "You are a technical writer specialized in computer security and hacker culture history."},
                        {"role": "user", "content": f"{prompt}\n\nArticle content:\n{content}"}  # Limit content to avoid token limits
                    ],
                    temperature=0.2,
                    response_format={ "type": "json_object" },
                )
                return response.choices[0].message.content.strip() if response.choices[0].message.content else None
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠ API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"  Retrying...")
                else:
                    print(f"  ✗ Error calling OpenAI API after {max_retries} attempts: {e}")
                    return None
        
        return None

    def process_articles(self, custom_prompt: Optional[str] = None, output_file: str = "summaries.json"):
        """
        Process articles and generate summaries.
        
        Args:
            custom_prompt: Optional custom prompt for summarization
            output_file: Output JSON file name (deprecated, kept for compatibility)
        """
        articles = self.find_all_articles()
        
        if not articles:
            print("No articles found!")
            return
        
        print(f"Found {len(articles)} articles total.")
        
        if self.test_mode:
            articles = random.sample(articles, min(3, len(articles)))
            print(f"Test mode: Processing {len(articles)} random articles")
        
        success_count = 0
        skipped_count = 0
        
        for i, (file_path, rel_path) in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}] Processing: {rel_path}")
            
            # Check if JSON file already exists
            json_path = file_path.with_suffix('.json')
            if json_path.exists():
                print(f"  ⊙ Skipped (JSON already exists)")
                skipped_count += 1
                continue
            
            content = self.read_article(file_path)
            if not content:
                print(f"  Skipped (could not read file)")
                continue
            
            print(f"  Article length: {len(content)} characters")
            
            # Try to get a valid JSON response, with retries
            max_attempts = 3
            summary_json = None
            
            for attempt in range(max_attempts):
                summary = self.summarize_article(content, custom_prompt)
                
                if not summary:
                    break  # API call failed completely
                
                # Parse the JSON response from LLM
                try:
                    # Try to extract JSON from the response (in case there's extra text)
                    summary_clean = summary.strip()
                    if summary_clean.startswith('```json'):
                        summary_clean = summary_clean.split('```json')[1].split('```')[0].strip()
                    elif summary_clean.startswith('```'):
                        summary_clean = summary_clean.split('```')[1].split('```')[0].strip()
                    
                    summary_json = json.loads(summary_clean)
                    break  # Successfully parsed JSON
                    
                except json.JSONDecodeError as e:
                    if attempt < max_attempts - 1:
                        print(f"  ⚠ Failed to parse JSON (attempt {attempt + 1}/{max_attempts}): {e}")
                        print(f"  Retrying...")
                    else:
                        print(f"  ✗ Failed to parse JSON after {max_attempts} attempts: {e}")
                        print(f"  Response was: {summary[:200]}...")
            
            if summary_json:
                # Write JSON file next to the text file
                json_path = file_path.with_suffix('.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(summary_json, f, indent=2, ensure_ascii=False)
                
                print(f"  ✓ Summary saved to {json_path.name}")
                success_count += 1
            else:
                print(f"  ✗ Failed to generate valid summary")
        
        print(f"\n{'='*60}")
        print(f"Processed {success_count} articles successfully")
        print(f"Skipped {skipped_count} articles (JSON already exists)")
        print(f"JSON files saved next to each .txt file")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description='Summarize ezine articles using OpenAI ChatGPT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode with 3 random articles from default zines directory
  python phrack-llm.py --test

  # Process all articles in default zines directory
  python phrack-llm.py

  # Process articles from a specific directory
  python phrack-llm.py --directory /path/to/articles

  # Process phrack articles specifically
  python phrack-llm.py -d zines/phrack

  # Use custom prompt
  python phrack-llm.py --prompt "Summarize this article in one paragraph"

  # Specify output file
  python phrack-llm.py --output my_summaries.json

Environment:
  OPENAI_API_KEY must be set with your OpenAI API key
        """
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: only process 3 random articles'
    )
    
    parser.add_argument(
        '--prompt',
        type=str,
        help='Custom prompt for summarization'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='summaries.json',
        help='Output JSON file name (default: summaries.json)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='OpenAI API key (or set OPENAI_API_KEY env var)'
    )
    
    parser.add_argument(
        '--directory', '-d',
        type=str,
        help='Directory to search for articles (default: ./zines/)'
    )
    
    args = parser.parse_args()
    
    try:
        summarizer = PhackSummarizer(
            api_key=args.api_key,
            test_mode=args.test,
            prompt=args.prompt,
            directory=args.directory
        )
        
        summarizer.process_articles(
            custom_prompt=args.prompt,
            output_file=args.output
        )
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
