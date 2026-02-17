#!/usr/bin/env python3
"""
Sync deletions across languages.
Reads a list of deleted files (passed as arguments) and removes their counterparts
in other languages.
"""

import sys
import os
from pathlib import Path

LANGUAGES = {"gr", "nl", "en"}

def get_counterparts(filepath: Path) -> list[Path]:
    """
    Given a file path like 'src/content/news/gr/post.md',
    return paths for 'src/content/news/nl/post.md' and 'src/content/news/en/post.md'.
    """
    parts = list(filepath.parts)
    
    # Find which part is the language code
    try:
        lang_index = -1
        for i, part in enumerate(parts):
            if part in LANGUAGES:
                lang_index = i
                break
        
        if lang_index == -1:
            return []

        current_lang = parts[lang_index]
        counterparts = []
        
        for lang in LANGUAGES:
            if lang == current_lang:
                continue
                
            new_parts = parts.copy()
            new_parts[lang_index] = lang
            counterparts.append(Path(*new_parts))
            
        return counterparts
        
    except Exception:
        return []

def main():
    # Skip the first argument (script name)
    deleted_files = sys.argv[1:]
    
    if not deleted_files:
        print("No files provided to sync.")
        return

    print(f"Processing {len(deleted_files)} deleted file(s)...")
    
    for file_path_str in deleted_files:
        # Remove quotes if present (though shell should handle this)
        file_path_str = file_path_str.strip('"').strip("'")
        file_path = Path(file_path_str)
        
        print(f"Source deleted: {file_path}")
        
        counterparts = get_counterparts(file_path)
        for target in counterparts:
            if target.exists():
                print(f"  Removing counterpart: {target}")
                try:
                    os.remove(target)
                except OSError as e:
                    print(f"  Error removing {target}: {e}")
            else:
                print(f"  Counterpart not found (already deleted?): {target}")

if __name__ == "__main__":
    main()
