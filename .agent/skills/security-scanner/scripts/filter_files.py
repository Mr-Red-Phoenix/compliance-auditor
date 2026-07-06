import sys
from pathlib import Path

def filter_files(directory_path: str, extensions: list) -> list:
    """Filters files within directory_path by a list of allowed extensions."""
    path = Path(directory_path)
    if not path.exists():
        return []
        
    filtered = []
    # Recursively find files
    for file_path in path.rglob("*"):
        if file_path.is_file():
            if file_path.suffix.lower() in extensions:
                filtered.append(str(file_path))
    return filtered

if __name__ == "__main__":
    # Example usage: python filter_files.py <dir_path> .py .ts .tsx
    if len(sys.argv) < 3:
        print("Usage: python filter_files.py <directory_path> <ext1> <ext2> ...", file=sys.stderr)
        sys.exit(1)
        
    target_dir = sys.argv[1]
    allowed_exts = [ext if ext.startswith('.') else f'.{ext}' for ext in sys.argv[2:]]
    
    results = filter_files(target_dir, allowed_exts)
    for r in results:
        print(r)
