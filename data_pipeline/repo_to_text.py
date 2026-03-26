import os

# --- הגדרות ---
# שם קובץ הפלט
OUTPUT_FILE = "full_project_context.txt"

# תיקיות שיש להתעלם מהן (ניתן להוסיף או להסיר)
IGNORE_DIRS = {
    '.git', '.idea', '.vscode', '__pycache__', 'venv', 'env',
    'node_modules', 'dist', 'build', '.DS_Store', '.venv'
}

# סיומות קבצים שיש להתעלם מהן (קבצים בינאריים, תמונות וכו')
IGNORE_EXTENSIONS = {
    '.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico',
    '.exe', '.bin', '.dll', '.so', '.zip', '.tar', '.gz',
    '.pdf', '.docx', '.pptx', '.xlsx', '.md'
}

# קבצים ספציפיים שרצוי לא לכלול (בעיקר סיסמאות)
IGNORE_FILES = {
    '.env', 'secrets.json', 'package-lock.json', 'yarn.lock'
}


def is_text_file(file_path):
    """בדיקה פשוטה האם הקובץ הוא קובץ טקסט שניתן לקריאה"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)  # מנסה לקרוא את ההתחלה
        return True
    except (UnicodeDecodeError, IOError):
        return False


def main():
    root_dir = os.getcwd()  # התיקייה הנוכחית

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        print(f"Starting scan in: {root_dir}")

        for root, dirs, files in os.walk(root_dir):
            # הסרת תיקיות שאנחנו רוצים להתעלם מהן כדי ש-os.walk לא ייכנס אליהן
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()

                # סינונים
                if file in IGNORE_FILES:
                    continue
                if ext in IGNORE_EXTENSIONS:
                    continue
                if file == OUTPUT_FILE or file == os.path.basename(__file__):
                    continue  # לא לכלול את הסקריפט עצמו או את קובץ הפלט

                if is_text_file(file_path):
                    try:
                        relative_path = os.path.relpath(file_path, root_dir)

                        # כתיבת כותרת ברורה לכל קובץ
                        outfile.write(f"\n{'=' * 40}\n")
                        outfile.write(f"FILE: {relative_path}\n")
                        outfile.write(f"{'=' * 40}\n")

                        # כתיבת תוכן הקובץ
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())

                        print(f"Added: {relative_path}")

                    except Exception as e:
                        print(f"Error reading {file}: {e}")

    print(f"\n--- Done! ---")
    print(f"All code is merged into: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()