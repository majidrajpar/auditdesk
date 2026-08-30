"""
AuditDesk Portable Standalone Packager (Option 2)
Builds a zero-install, 100% self-contained portable package with official signed
Windows Embedded Python (64-bit) and pre-bundled dependencies.

Produces: dist/AuditDesk-Portable-Windows-x64.zip
"""

import os
import sys
import shutil
import urllib.request
import zipfile
import subprocess

EMBED_PYTHON_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(ROOT_DIR, "build_portable_temp")
DIST_DIR = os.path.join(ROOT_DIR, "dist")
RUNTIME_DIR = os.path.join(BUILD_DIR, "runtime")


def build_portable_package():
    print("=" * 65)
    print("   BUILDING AUDITDESK PORTABLE ZERO-INSTALL PACKAGE (OPTION 2)")
    print("=" * 65)

    # 1. Clean previous build
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(RUNTIME_DIR, exist_ok=True)

    # 2. Download Official Windows 64-bit Embeddable Python
    embed_zip_path = os.path.join(BUILD_DIR, "python_embed.zip")
    print(f"\n[1/5] Downloading official signed Windows Embedded Python 3.11...")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(EMBED_PYTHON_URL) as resp, open(embed_zip_path, "wb") as out:
        shutil.copyfileobj(resp, out)
    print("  ✓ Python embeddable zip downloaded successfully.")

    # 3. Extract Embedded Python to runtime/
    print("\n[2/5] Extracting Python runtime...")
    with zipfile.ZipFile(embed_zip_path, "r") as zf:
        zf.extractall(RUNTIME_DIR)
    os.remove(embed_zip_path)

    # Enable import site in python311._pth
    pth_file = os.path.join(RUNTIME_DIR, "python311._pth")
    if os.path.exists(pth_file):
        with open(pth_file, "r") as f:
            lines = f.readlines()
        with open(pth_file, "w") as f:
            for line in lines:
                if "import site" in line:
                    f.write("import site\n")
                else:
                    f.write(line)
            f.write("..\n")
            f.write(".\\site-packages\n")
            f.write(".\\Lib\\site-packages\n")

    # 4. Install python-docx directly into the portable runtime
    print("\n[3/5] Installing dependencies into portable runtime...")
    site_packages = os.path.join(RUNTIME_DIR, "site-packages")
    os.makedirs(site_packages, exist_ok=True)

    # Install python-docx via pip targeted to the portable runtime
    cmd = [
        sys.executable, "-m", "pip", "install",
        "python-docx>=0.8.11",
        "--target", site_packages,
        "--no-compile", "--quiet"
    ]
    subprocess.check_call(cmd)
    print("  ✓ Pre-bundled python-docx and OpenXML libraries into portable runtime.")

    # 5. Copy Application Source Files
    print("\n[4/5] Copying AuditDesk application files...")
    shutil.copy(os.path.join(ROOT_DIR, "server.py"), BUILD_DIR)
    shutil.copy(os.path.join(ROOT_DIR, "launch.py"), BUILD_DIR)
    shutil.copy(os.path.join(ROOT_DIR, "requirements.txt"), BUILD_DIR)
    shutil.copy(os.path.join(ROOT_DIR, "README.md"), BUILD_DIR)
    shutil.copy(os.path.join(ROOT_DIR, "LICENSE"), BUILD_DIR)

    shutil.copytree(os.path.join(ROOT_DIR, "data"), os.path.join(BUILD_DIR, "data"))
    shutil.copytree(os.path.join(ROOT_DIR, "engine"), os.path.join(BUILD_DIR, "engine"))
    shutil.copytree(os.path.join(ROOT_DIR, "static"), os.path.join(BUILD_DIR, "static"))

    # Create root 1-Click Portable launcher
    portable_bat = os.path.join(BUILD_DIR, "AuditDesk-Portable.bat")
    with open(portable_bat, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("title AuditDesk Portable - Fieldwork OS\n")
        f.write("cd /d \"%~dp0\"\n")
        f.write("echo Starting AuditDesk Portable (Zero-Install)...\n")
        f.write("\".\\runtime\\python.exe\" server.py\n")
        f.write("pause\n")

    # 6. Compress into Standalone Portable ZIP
    zip_output_path = os.path.join(DIST_DIR, "AuditDesk-Portable-Windows-x64.zip")
    print(f"\n[5/5] Packaging standalone portable archive: {zip_output_path}...")
    with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BUILD_DIR):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, BUILD_DIR)
                zipf.write(abs_path, os.path.join("AuditDesk-Portable", rel_path))

    # Clean build folder
    shutil.rmtree(BUILD_DIR)

    size_mb = os.path.getsize(zip_output_path) / (1024 * 1024)
    print("\n" + "=" * 65)
    print(f"  🎉 PORTABLE PACKAGE SUCCESSFULLY CREATED! ({size_mb:.2f} MB)")
    print(f"  Location: {zip_output_path}")
    print("=" * 65)
    print("\nHow to use:")
    print("1. Extract 'AuditDesk-Portable-Windows-x64.zip' anywhere (Desktop, USB drive).")
    print("2. Double-click 'AuditDesk-Portable.bat'.")
    print("3. Zero installation, zero admin rights, 100% offline.")


if __name__ == "__main__":
    build_portable_package()
