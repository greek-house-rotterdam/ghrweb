#!/usr/bin/env python3
"""
Verify that all content exists in all three languages (gr, nl, en).
Scans src/content/ and ensures that for every file in one language,
a corresponding file exists in the other two with the same filename.
"""

import sys
from pathlib import Path

CONTENT_DIR = Path("src/content")
LANGUAGES = {"gr", "nl", "en"}

def get_collections():
    """Return a list of collection directories (e.g. news, events)."""
    if not CONTENT_DIR.exists():
        return []
    return [d for d in CONTENT_DIR.iterdir() if d.is_dir()]

def verify_collection(collection_dir: Path) -> list[str]:
    """Check a single collection for missing translations."""
    errors = []
    
    # gather all filenames (slugs) across all languages
    all_slugs = set()
    for lang in LANGUAGES:
        lang_dir = collection_dir / lang
        if lang_dir.exists():
            for f in lang_dir.glob("*.md"):
                all_slugs.add(f.name)
    
    # check for missing files
    for slug in all_slugs:
        for lang in LANGUAGES:
            expected_file = collection_dir / lang / slug
            if not expected_file.exists():
                errors.append(f"Missing: {expected_file}")
                
    return errors

def main():
    print(f"Verifying content integrity in {CONTENT_DIR}...")
    
    collections = get_collections()
    all_errors = []
    
    for collection in collections:
        # Skip if it doesn't look like a content collection (no lang folders)
        if not any((collection / lang).exists() for lang in LANGUAGES):
            continue
            
        print(f"Checking collection: {collection.name}")
        errors = verify_collection(collection)
        all_errors.extend(errors)
        
    if all_errors:
        print("\n❌ Content integrity check failed! The following files are missing:")
        for error in sorted(all_errors):
            print(f"  - {error}")
        print("\nThis usually means the translation workflow failed or hasn't run yet.")
        sys.exit(1)
    
    print("\n✅ All content is present in all languages.")

if __name__ == "__main__":
    main()
