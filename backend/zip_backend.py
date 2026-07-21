import zipfile
import os

# ENTERPRISE ALLOW-LIST: The ONLY things that will go to Azure.
# Everything else (Handouts, outputs, tests, venv, .env, hidden files) is strictly ignored.
ALLOWED_ROOT_ITEMS = {'api.py', 'main.py', 'requirements.txt', 'src'}

print("Starting strict enterprise zip process...")

with zipfile.ZipFile('deploy.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk('.'):
        
        # Block __pycache__ from ever being zipped, even inside allowed folders
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        # If we are at the root level (backend folder), force it to only look at ALLOWED items
        if root == '.':
            dirs[:] = [d for d in dirs if d in ALLOWED_ROOT_ITEMS]
            files = [f for f in files if f in ALLOWED_ROOT_ITEMS]

        # Write the allowed files to the zip
        for file in files:
            file_path = os.path.join(root, file)
            zf.write(file_path, os.path.relpath(file_path, '.'))
            print(f"Securely Added: {os.path.relpath(file_path, '.')}")

print("\nSUCCESS: deploy.zip is perfectly clean and ready for Azure!")
