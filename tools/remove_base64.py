#!/usr/bin/env python3
"""
Remove base64-encoded binary data blocks from text files.
Removes blocks that start with "begin XXX filename" and end with "end".
"""

import re
import os
import sys
from pathlib import Path


def remove_base64_blocks(content):
    """
    Remove base64 uuencoded blocks from text content.
    
    Matches blocks starting with "begin <mode> <filename>" and ending with "end".
    Example:
        begin 644 clet
        M'XL(`'9N.3...
        ...
        end
    """
    # Pattern matches: 
    # - "begin" followed by octal permissions and filename
    # - All lines until "end" (including the end line)
    # - Optionally followed by blank lines
    pattern = r'\nbegin \d+ \S+\n.*?\nend\n*'
    
    # Remove all matching blocks
    cleaned = re.sub(pattern, '\n', content, flags=re.DOTALL)
    
    return cleaned


def process_file(file_path, dry_run=False):
    """Process a single file to remove base64 blocks."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()
        
        cleaned_content = remove_base64_blocks(original_content)
        
        # Check if anything changed
        if original_content == cleaned_content:
            print(f"  No base64 blocks found in: {file_path}")
            return False
        
        if dry_run:
            # Count how many blocks were found
            blocks_found = len(re.findall(r'\nbegin \d+ \S+\n.*?\nend\n*', 
                                         original_content, flags=re.DOTALL))
            print(f"  [DRY RUN] Would remove {blocks_found} block(s) from: {file_path}")
            return True
        else:
            # Write the cleaned content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            blocks_removed = len(re.findall(r'\nbegin \d+ \S+\n.*?\nend\n*', 
                                           original_content, flags=re.DOTALL))
            size_before = len(original_content)
            size_after = len(cleaned_content)
            size_diff = size_before - size_after
            
            print(f"  ✓ Removed {blocks_removed} block(s) from: {file_path}")
            print(f"    Size: {size_before} → {size_after} bytes (-{size_diff} bytes)")
            return True
            
    except Exception as e:
        print(f"  ✗ Error processing {file_path}: {e}", file=sys.stderr)
        return False


def find_and_process_files(directory, pattern='**/*.txt', dry_run=False):
    """Find all matching files and process them."""
    base_path = Path(directory)
    
    if not base_path.exists():
        print(f"Error: Directory '{directory}' does not exist.", file=sys.stderr)
        return
    
    print(f"Scanning for files matching '{pattern}' in: {base_path}")
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (files will be modified)'}")
    print("-" * 70)
    
    files = list(base_path.glob(pattern))
    
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return
    
    print(f"Found {len(files)} file(s) to check\n")
    
    processed = 0
    modified = 0
    
    for file_path in sorted(files):
        processed += 1
        if process_file(file_path, dry_run):
            modified += 1
    
    print("\n" + "=" * 70)
    print(f"Summary: Processed {processed} file(s), modified {modified} file(s)")
    if dry_run:
        print("\n⚠️  This was a DRY RUN. No files were actually modified.")
        print("   Run without --dry-run to apply changes.")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Remove base64-encoded binary data blocks from text files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run on current directory
  python remove_base64.py --dry-run
  
  # Process all .txt files in data/phrack directory
  python remove_base64.py data/phrack
  
  # Process specific file
  python remove_base64.py data/phrack/61/9.txt
  
  # Custom pattern
  python remove_base64.py data --pattern "**/*.txt"
        """
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory or file to process (default: current directory)'
    )
    
    parser.add_argument(
        '--pattern',
        default='**/*.txt',
        help='Glob pattern for files to process (default: **/*.txt)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if path.is_file():
        # Process single file
        print(f"Processing single file: {path}")
        print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
        print("-" * 70)
        process_file(path, args.dry_run)
    else:
        # Process directory
        find_and_process_files(args.path, args.pattern, args.dry_run)


if __name__ == '__main__':
    main()
