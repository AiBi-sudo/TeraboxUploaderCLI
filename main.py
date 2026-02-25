"""
TeraBox Uploader CLI: main.py
Python CLI tool to make uploads to your Terabox cloud from any Linux or Windows environment
without having to use the website.

This program is provided as-is, without any warranty.
This program is not affiliated with Terabox in any way.
This program is licensed under the MIT License.

Developed by Gonçalo M. (@dnigamer in GitHub).
For more information, please visit https://github.com/dnigamer/TeraboxUploaderCLI
If you find any bugs, please open an issue in the GitHub repository mentioned in the link above.
"""

import fnmatch
import math
import os
import sys
import json
import subprocess
import hashlib
import zipfile
from urllib.parse import quote_plus
import requests
from typing import Optional
import base64

from modules.encryption import Encryption, FileEncryptedException
from modules.formatting import Formatting

CODE_VERSION = "1.8.1"
fmt = Formatting(timestamps=True)

print("-" * 97)
print(f"Terabox Uploader CLI v{CODE_VERSION} 2025")
print("* Developed by Gonçalo M. (@dnigamer in Github).")
print("* For more information, please visit https://github.com/dnigamer/TeraboxUploaderCLI.")
print("* If you find any bugs, please open an issue in the Github repository mentioned in the link above")
print("-" * 97)
print("! This program is licensed under the MIT License.")
print("! This program is provided as-is, without any warranty.")
print("! This program is not affiliated with Terabox in any way.")
print("-" * 97)

# Setup argument component
if len(sys.argv) > 1 and sys.argv[1] == "setup":
    if os.path.exists("secrets.json") and os.path.exists("settings.json"):
        fmt.error("setup", "secrets.json and settings.json already exist in the current folder.")
        sys.exit()

    if os.path.exists("secrets.json"):
        fmt.error("setup", "secrets.json already exists in the current folder.")
    else:
        fmt.info("setup", "Creating secrets.json file...")
        fmt.info("setup", "Please enter the required information for the secrets.json file.")

        print("Enter your jstoken:")
        JS_TOKEN = input(": ")
        if not any(char.isdigit() for char in JS_TOKEN):
            fmt.error("setup", "Invalid jstoken.")
            sys.exit()

        print("Enter your csrfToken:")
        CSRF_TOKEN = input(": ")
        if not CSRF_TOKEN:
            fmt.error("setup", "Invalid csrfToken.")
            sys.exit()

        print("Enter your browserid:")
        BROWSER_ID = input(": ")
        if not BROWSER_ID:
            fmt.error("setup", "Invalid browserid.")
            sys.exit()

        print("Enter your lang:")
        LANG = input(": ")
        if not LANG:
            LANG = "en"

        print("Enter your ndus token:")
        NDUS = input(": ")
        if not NDUS:
            fmt.error("setup", "Invalid ndus token.")
            sys.exit()

        print("Enter your ndut_fmt token:")
        NDUT_FMT = input(": ")
        if not NDUT_FMT:
            fmt.error("setup", "Invalid ndut_fmt token.")
            sys.exit()

        try:
            with open("secrets.json", "w", encoding="utf8") as f:
                f.write("{\n")
                f.write(f'    "jstoken": "{JS_TOKEN}",\n')
                f.write('    "cookies": {\n')
                f.write(f'        "csrfToken": "{CSRF_TOKEN}",\n')
                f.write(f'        "browserid": "{BROWSER_ID}",\n')
                f.write(f'        "lang": "{LANG}",\n')
                f.write(f'        "ndus": "{NDUS}",\n')
                f.write(f'        "ndut_fmt": "{NDUT_FMT}"\n')
                f.write('    }\n')
                f.write("}\n")
                f.close()
        except Exception as e:
            fmt.error("setup", "An error occurred while creating the secrets.json file.")
            fmt.error("setup", f"More information about this error: {e}")
            sys.exit()

        fmt.success("setup", "secrets.json file created.")

    if os.path.exists("settings.json"):
        fmt.error("setup", "settings.json already exists in the current folder.")
    else:
        fmt.info("setup", "Creating settings.json file...")
        fmt.info("setup", "Please enter the required information for the settings.json file.")

        print("Enter the path to the source directory:")
        SOURCE_DIR = input(": ")
        if not SOURCE_DIR:
            fmt.error("setup", "Invalid source directory.")
            sys.exit()
        if not os.path.exists(SOURCE_DIR):
            fmt.error("setup", "Source directory does not exist.")
            sys.exit()

        print("Enter the path to the remote directory:")
        REMOTE_DIR = input(": ")
        if not REMOTE_DIR:
            fmt.error("setup", "Invalid remote directory.")
            sys.exit()

        print("Do you want to move files to another directory after uploading? (yes/no)")
        MOVE_FILES = input(": ")
        if not MOVE_FILES:
            fmt.error("setup", "Please input \"yes\" or \"no\" for move files setting")
            sys.exit()
        if MOVE_FILES.lower() not in ("yes", "no"):
            fmt.error("setup", "Invalid move files setting.")
            fmt.error("setup", "Defaulting to \"false\"/no moving files.")
            MOVE_FILES = "false"
        if MOVE_FILES.lower() == "yes":
            print("Enter the path to the uploaded directory:")
            UPLOADED_DIR = input(": ")
            if not UPLOADED_DIR:
                fmt.error("setup", "Invalid uploaded directory.")
                sys.exit()
            if not os.path.exists(UPLOADED_DIR):
                fmt.error("setup", "Destination directory of uploaded files does not exist.")
                sys.exit()
            MOVE_FILES = "true"
        else:
            MOVE_FILES = "false"
            UPLOADED_DIR = ""

        print("Do you want to delete the source files after uploading? (yes/no)")
        DELETE_SOURCE = input(": ")
        if not DELETE_SOURCE:
            fmt.error("setup", "Please input \"yes\" or \"no\" for delete source setting.")
            sys.exit()
        if DELETE_SOURCE.lower() not in ("yes", "no"):
            fmt.error("setup", "Invalid delete source setting. Defaulting to \"false\"/no deletion.")
            DELETE_SOURCE = "false"
        if DELETE_SOURCE.lower() == "yes":
            DELETE_SOURCE = "true"
        else:
            DELETE_SOURCE = "false"

        print("Do you want to enable file encryption? (yes/no)")
        ENCRYPTION_ENAB = input(": ")
        if not ENCRYPTION_ENAB:
            fmt.error("setup", "Please input \"yes\" or \"no\" for encryption setting.")
            sys.exit()
        if ENCRYPTION_ENAB.lower() not in ("yes", "no"):
            fmt.error("setup", "Invalid encryption setting.")
            fmt.error("setup", "Defaulting to \"false\"/no encryption.")
            ENCRYPTION_ENAB = "false"
        if ENCRYPTION_ENAB.lower() == "yes":
            print("Enter the path to the encryption key:")
            ENCRYPTION_KEY = input(": ")
            if not ENCRYPTION_KEY:
                fmt.error("setup", "Please input a valid path to the encryption key.")
                sys.exit()
            if os.path.exists(ENCRYPTION_KEY):
                ENCRYPTION_ENAB = "true"
                fmt.success("setup", "Encryption key found.")
                fmt.success("setup", "Type of encryption key: " + Encryption().get_key_type(ENCRYPTION_KEY))
            else:
                fmt.info("setup", "Generating encryption key...")
                encrypt = Encryption()
                encrypt.generate_key(ENCRYPTION_KEY)
                ENCRYPTION_ENAB = "true"
                fmt.success("setup", "Encryption key generated successfully.")
        else:
            ENCRYPTION_ENAB = "false"
            ENCRYPTION_KEY = ""

        print("Do you want to ignore specific files? (yes/no)")
        IGNORE_FILES = input(": ")
        if not IGNORE_FILES:
            fmt.error("setup", "Invalid ignore files setting.")
            sys.exit()
        if IGNORE_FILES.lower() not in ("yes", "no"):
            fmt.error("setup", "Invalid ignore files setting.")
        if IGNORE_FILES.lower() == "yes":
            print("Enter the files to ignore separated by a comma (,):")
            IGNORED_FILES = input(": ")
            if not IGNORED_FILES:
                fmt.error("setup", "Invalid ignored files setting.")
                sys.exit()
            IGNORED_FILES = [x.strip() for x in IGNORED_FILES.split(",")]
        else:
            IGNORED_FILES = []

        print("Do you want to show the quota information after each upload? (yes/no)")
        SHOW_QUOTA = input(": ")
        if not SHOW_QUOTA:
            fmt.error("setup", "Invalid show quota setting.")
            sys.exit()
        if SHOW_QUOTA.lower() not in ("yes", "no"):
            fmt.error("setup", "Invalid show quota setting.")
        if SHOW_QUOTA.lower() == "yes":
            SHOW_QUOTA = "true"
        else:
            SHOW_QUOTA = "false"

        try:
            with open("settings.json", "w", encoding="utf8") as f:
                f.write("{\n")
                f.write('  "directories": {\n')
                f.write(f'    "sourcedir": "{SOURCE_DIR}",\n')
                f.write(f'    "remotedir": "{REMOTE_DIR}",\n')
                f.write(f'    "uploadeddir": "{UPLOADED_DIR}"\n')
                f.write('  },\n')
                f.write('  "files": {\n')
                f.write(f'    "movefiles": "{MOVE_FILES}",\n')
                f.write(f'    "deletesource": "{DELETE_SOURCE}"\n')
                f.write('  },\n')
                f.write('  "encryption": {\n')
                f.write(f'    "enabled": "{ENCRYPTION_ENAB}",\n')
                f.write(f'    "encryptionkey": "{ENCRYPTION_KEY}"\n')
                f.write('  },\n')
                f.write('  "ignoredfiles": ["' + '", "'.join(IGNORED_FILES) + '"],\n')
                f.write('  "appearance": {\n')
                f.write(f'    "showquota": "{SHOW_QUOTA}"\n')
                f.write('  }\n')
                f.write("}\n")
                f.close()
            fmt.success("setup", "settings.json file created.")
        except Exception as e:
            fmt.error("setup", "An error occurred while creating the settings.json file.")
            fmt.error("setup", f"More information about this error: {e}")
            sys.exit()

    fmt.info("setup", "Setup completed. Please run the program again without the 'setup' argument.")
    sys.exit()

# Encryption setup component
if len(sys.argv) > 1 and sys.argv[1] == "encryption":
    # Generate encryption key
    fmt.info("encryption", "Generating encryption key...")
    encryption_key = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8")
    fmt.success("encryption", f"Encryption key generated successfully: {encryption_key}")

    print("Do you want to save this encryption key? (yes/no)")
    save_key = input(": ")
    if save_key.lower() == "yes":
        try:
            with open("settings.json", "r", encoding="utf8") as f:
                content = json.load(f)
            content["encryption"]["encryptionkey"] = encryption_key
            with open("settings.json", "w", encoding="utf8") as f:
                json.dump(content, f, indent=2)
                f.truncate()
            fmt.success("encryption", "Encryption key saved successfully.")
        except json.JSONDecodeError as e:
            fmt.error("encryption", "Invalid JSON format in settings.json.")
            fmt.error("encryption", f"More information about this error: {e}")
    else:
        fmt.info("encryption", "Encryption key not saved.")

    fmt.info("encryption", "Encryption process completed.")
    sys.exit()

# CURL INSTALLATION
CURL_URL = "https://curl.se/windows/dl-8.13.0_5/curl-8.13.0_5-win64-mingw.zip"
if os.name == "nt":
    fmt.info("CURL", "Windows host detected. Checking if curl is installed...")
    curl_path = os.path.join("curl", "bin", "curl.exe")
    if not (os.path.exists(curl_path) or os.path.exists("curl.exe")):
        fmt.info("CURL", f"curl.exe not found. Downloading curl from {CURL_URL}...")
        curlreq = requests.get(CURL_URL, timeout=10)
        with open("curl.zip", "wb") as f:
            f.write(curlreq.content)
        fmt.info("CURL", "Extracting curl...")
        with zipfile.ZipFile("curl.zip", "r") as zip_ref:
            zip_ref.extractall(".")
        extracted_dir = "curl-8.13.0_5-win64-mingw"
        if os.path.exists(extracted_dir):
            os.rename(extracted_dir, "curl")
        fmt.info("CURL", "Curl extracted.")
        os.remove("curl.zip")
    else:
        fmt.success("CURL", "curl is already installed or exists in the current folder.")
else:
    fmt.info("CURL", "Checking for curl...")
    if not subprocess.run(["which", "curl"], stdout=subprocess.PIPE, check=True).stdout.decode('utf-8'):
        fmt.info("CURL", "curl not found. Installing curl...")
        if os.name == "posix":
            fmt.info("CURL", "Installing curl using Homebrew...")
            subprocess.run(["brew", "install", "curl"], check=True)
        elif os.name == "linux":  # Assuming Debian-based distros
            fmt.info("CURL", "Installing curl using apt...")
            subprocess.run(["sudo", "apt", "install", "-y", "curl"], check=True)
        else:
            fmt.error("CURL", "Your OS is not supported for automatic curl installation. Please install curl manually.")
            sys.exit()
    else:
        fmt.info("CURL", "Curl is already installed or exists in the current folder.")

# FFMPEG CHECK
fmt.info("ffmpeg", "Checking for ffmpeg...")
try:
    ffmpeg_result = subprocess.run(
        ["ffmpeg", "-version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if ffmpeg_result.returncode == 0:
        fmt.success("ffmpeg", "ffmpeg is available. Large files (20GB+) will be split into 2 parts automatically.")
        FFMPEG_AVAILABLE = True
    else:
        fmt.warning("ffmpeg", "ffmpeg check failed. Large files (20GB+) will be skipped.")
        FFMPEG_AVAILABLE = False
except FileNotFoundError:
    fmt.warning("ffmpeg", "ffmpeg not found. Large files (20GB+) will be skipped.")
    fmt.warning("ffmpeg", "Install ffmpeg to enable automatic splitting of large files.")
    FFMPEG_AVAILABLE = False

try:
    if not os.path.exists("settings.json"):
        fmt.error("settings", "settings.json file not found.")
        fmt.error("settings", "Please create a settings.json file by running the program with the 'setup'"
                              " argument or following the README.md.")
        sys.exit()

    with open("secrets.json", "r", encoding="utf8") as f:
        try:
            secrets = json.load(f)
        except json.JSONDecodeError as e:
            fmt.error("auth", "Invalid JSON format in secrets.json.")
            fmt.error("auth", f"More information about this error: {e}")
            sys.exit()
        except Exception as e:
            fmt.error("auth", "An error occurred while reading the secrets.json file.")
            fmt.error("auth", f"More information about this error: {e}")
            sys.exit()

        try:
            JSTOKEN = secrets["jstoken"]
            COOKIES = secrets["cookies"]
            COOKIES_STR = ""
            for key, value in COOKIES.items():
                COOKIES_STR += f"{key}={value};"
            f.close()

            if not any(char.isdigit() for char in JSTOKEN):
                fmt.error("auth", "Invalid jstoken.")
                sys.exit()
            fmt.success("auth", "Loaded authentication tokens.")
        except KeyError as e:
            fmt.error("auth", f"Key {e} not found in secrets.json.")
            f.close()
            sys.exit()
        except Exception as e:
            fmt.error("auth", "An error occurred while reading the secrets.json file.")
            fmt.error("auth", f"More information about this error: {e}")
            f.close()
            sys.exit()
except FileNotFoundError as e:
    fmt.error("auth", "secrets.json file not found.")
    fmt.error("auth", f"More information about this error: {e}")
    sys.exit()
except Exception as e:
    fmt.error("auth", "An error occurred while reading the secrets.json file.")
    fmt.error("auth", f"More information about this error: {e}")
    sys.exit()

try:
    if not os.path.exists("settings.json"):
        fmt.error("settings", "settings.json file not found.")
        fmt.error("settings",
                  "Please create a settings.json file by running the program with the 'setup' argument or following "
                  "the README.md.")
        sys.exit()

    with open("settings.json", "r", encoding="utf8") as f:
        try:
            settings = json.load(f)
        except json.JSONDecodeError as e:
            fmt.error("settings", "Invalid JSON format in settings.json.")
            fmt.error("settings", f"More information about this error: {e}")
            sys.exit()
        except Exception as e:
            fmt.error("settings", "An error occurred while reading the settings.json file.")
            fmt.error("settings", f"More information about this error: {e}")
            sys.exit()

        try:
            SOURCE_DIR = settings["directories"].get("sourcedir", "")
            REMOTELOC = settings["directories"].get("remotedir", "")
            MOVETOLOC = settings["directories"].get("uploadeddir", "")
            MOVEFILES = settings["files"].get("movefiles", "false").lower() == "true"
            DELSRCFIL = settings["files"].get("deletesource", "false").lower() == "true"
            ENCRYPTFL = settings["encryption"].get("enabled", "false").lower() == "true"
            ENCRYPKEY = settings["encryption"].get("encryptionkey", "")
            IGNOREFIL = settings.get("ignoredfiles", [])
            SHOWQUOTA = settings["appearance"].get("showquota", "false").lower() == "true"
            CHUNKSIZEMB = int(settings.get("upload", {}).get("chunksizemb", 120))
            # normalize important paths to absolute paths so display helpers work reliably
            try:
                if SOURCE_DIR:
                    SOURCE_DIR = os.path.abspath(SOURCE_DIR)
                if MOVETOLOC:
                    MOVETOLOC = os.path.abspath(MOVETOLOC)
                if ENCRYPKEY:
                    ENCRYPKEY = os.path.abspath(ENCRYPKEY)
            except Exception:
                pass
        except KeyError as e:
            fmt.error("settings", f"Key {e} not found in settings.json.")
            fmt.error("settings", "Please check your settings.json file and the README.md file for these "
                                  "configurations.")
            sys.exit()
        except Exception as e:
            fmt.error("settings", "An error occurred while reading the settings.json file.")
            fmt.error("settings", f"More information about this error: {e}")
            sys.exit()
        f.close()
except FileNotFoundError as e:
    fmt.error("settings", "settings.json file not found.")
    fmt.error("settings", f"More information about this error: {e}")
    sys.exit()
except Exception as e:
    fmt.error("settings", "An error occurred while reading the settings.json file.")
    fmt.error("settings", f"More information about this error: {e}")
    sys.exit()

if DELSRCFIL and MOVEFILES:
    fmt.error("settings",
              "You cannot have move and delete files settings configured as true at the same time.")
    fmt.error("settings", "Please check your settings.json file for these configurations.")
    sys.exit()

if not SOURCE_DIR or not REMOTELOC:
    fmt.error("settings", "Invalid directory paths. Please check the settings.json file for missing paths.")
    sys.exit()

if not os.path.exists(SOURCE_DIR) and not os.path.isdir(SOURCE_DIR):
    fmt.error("settings", "Source directory does not exist. Please check the path.")
    sys.exit()

if not os.path.exists(MOVETOLOC) and not os.path.isdir(MOVETOLOC) and MOVEFILES:
    fmt.error("settings", "Move to directory does not exist. Please check the path.")
    sys.exit()

if not ENCRYPTFL:
    fmt.warning("encryption",
                "File encryption is disabled. However, it is recommended to enable it for security "
                "reasons regarding TeraBox's ToS and Privacy Policy.")
    fmt.warning("encryption",
                "For full security of your files, please enable file encryption in the settings.json "
                "file.")
else:
    encrypt = Encryption()
    if not ENCRYPKEY:
        fmt.error("encryption", "Encryption key path is not set.")
        sys.exit()
    if not os.path.exists(ENCRYPKEY):
        fmt.warning("encryption", "Encryption key file does not exist.")
        fmt.info("encryption", "Generating encryption key...")
        encrypt.generate_key(ENCRYPKEY)
        fmt.success("encryption", "Encryption key generated successfully.")
    else:
        fmt.success("encryption", "Encryption key found.")
        fmt.success("encryption", "Type of encryption key: " + encrypt.get_key_type(ENCRYPKEY))

fmt.success("settings", "Loaded settings.")

# PROGRAM INTERNAL VARS
USERAGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2; rv:121.0) Gecko/20100101 Firefox/121.0"
BASEURLTB = "https://www.terabox.com"
TEMP_DIR = "./temp"
ERRORS = False


def _short_path(path: str, prefer_base: Optional[str] = None) -> str:
    """
    Return a short display path for logs.
    - Prefer a path relative to cwd when possible.
    - If that results in a leading '..', and prefer_base is provided, return a path relative to prefer_base
      prefixed with the base directory name (e.g. 'source/sub1/file').
    - Fall back to absolute path if relpaths fail.
    Paths are returned using the OS-native separators.
    """
    try:
        abs_path = os.path.abspath(path)
    except Exception:
        return str(path)

    # If we have a prefer_base (usually SOURCE_DIR), try to show path relative to it
    if prefer_base:
        try:
            abs_base = os.path.abspath(prefer_base)
            # If path is inside prefer_base, show as 'basename_of_base/relative/path'
            try:
                common = os.path.commonpath([abs_path, abs_base])
            except Exception:
                common = None
            if common == abs_base:
                rel = os.path.relpath(abs_path, abs_base)
                if rel == '.' or rel == './':
                    return os.path.normpath(os.path.basename(abs_base))
                return os.path.normpath(os.path.join(os.path.basename(abs_base), rel))

            # If not strictly inside, try relative to parent of prefer_base to get 'source/..' style
            base_parent = os.path.dirname(abs_base)
            try:
                rel2 = os.path.relpath(abs_path, base_parent)
                if not rel2.startswith('..'):
                    return os.path.normpath(rel2)
            except Exception:
                pass
        except Exception:
            pass

    # Fallback to a relpath to cwd if it doesn't go outside, otherwise absolute
    try:
        relcwd = os.path.relpath(abs_path, os.getcwd())
        if not relcwd.startswith('..'):
            return os.path.normpath(relcwd)
    except Exception:
        pass

    return os.path.normpath(abs_path)


# PROGRAM FUNCTIONS
def convert_size(size_bytes: int) -> str:
    """
    Converts bytes to human-readable size
    :param size_bytes: The size in bytes to convert.
    :return: The size as a human-readable string.
    """
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    it = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, it)
    size = round(size_bytes / p, 2)
    return f"{size} {size_name[it]}"


def fetch_remote_directory(remote_dir: str) -> list:
    """
    Returns all the files in the remote directory in a list
    :param remote_dir:
    :return: list of files/folders in the remote directory
    """
    try:
        req = requests.get(
            f"{BASEURLTB}/api/list",
            headers={
                "User-Agent": USERAGENT,
                "Referer": BASEURLTB + "/main"
            },
            cookies=COOKIES,
            params={
                "app_id": "250528",
                "web": "1",
                "channel": "dubox",
                "clienttype": "5", # This changed from 0 to 5 in 2025
                "jsToken": f"{JSTOKEN}",
                "dir": f"/{remote_dir}", # Leading slash is now required
                "num": "1000",
                "page": "1",
                "order": "time",
                "desc": "1",
                "showempty": "0"
            },
            timeout=10
        )
        data = json.loads(req.text)
        if "errno" in data and data["errno"] != 0:
            if data["errno"] == -7:
                fmt.error("remote fetch", "Couldn't fetch remote directory. Check if the remote directory exists.")
            if data["errno"] == -6:
                fmt.error("remote fetch", "Couldn't fetch remote directory. Check if all the cookies are valid.")
            else:
                fmt.error("remote fetch", f"API error: {data}")
            return []
        response = data.get("list", [])
        items = []
        for entry in response:
            listing = {
                "name": entry["server_filename"],
                "path": entry["path"],
                "size": entry["size"],
            }
            if entry["isdir"] == 0:
                items.append(listing)
            if entry["isdir"] == 1:
                items.extend(fetch_remote_directory(entry["path"]))
        return items
    except Exception as e:
        fmt.error("remote fetch", f"Exception occurred: {e}")
        return []


def precreate_file(filename: str, md5json_pc_local: str) -> str:
    """
    Precreates a file for upload
    :param filename: The name of the file to precreate in the cloud path including the filepath.
    :param md5json_pc_local: The MD5 hash of the file or full file (if in pieces).
    :return: The upload ID of the file. If the precreate fails, returns "fail".
    """
    try:
        preresponse = requests.post(f"{BASEURLTB}/api/precreate",
                                    headers={"User-Agent": USERAGENT, "Origin": BASEURLTB,
                                             "Referer": BASEURLTB + "/main?category=all",
                                             "Content-Type": "application/x-www-form-urlencoded"},
                                    cookies=COOKIES,
                                    data={"app_id": "250528", "web": "1", "channel": "dubox", "clienttype": "0",
                                          "jsToken": f"{JSTOKEN}", "path": f"{REMOTELOC}/{filename}", "autoinit": "1",
                                          "target_path": f"{REMOTELOC}", "block_list": f"{md5json_pc_local}"},
                                    timeout=10)
        if "uploadid" in preresponse.text:
            return json.loads(preresponse.text)["uploadid"]
        fmt.error("precreate", "File precreate failed.")
        if json.loads(preresponse.text)["errmsg"] == 'need verify':
            fmt.error("precreate",
                      "The login session has expired. Please login again and refresh the credentials.")
            return "fail"
        fmt.error("precreate", f"ERROR: More information: {json.loads(preresponse.text)}")
        return "fail"
    except Exception as exp_precreate:
        fmt.error("precreate", "ERROR: File precreate request failed.")
        fmt.error("precreate", f"ERROR: More information about this error: {exp_precreate}")
        return "fail"


def upload_file(local_path: str, cloud_filename: str, uploadid_local: str, md5hash: str, partseq: int = 0, total_parts: int = 1) -> str:
    """
    Uploads a file
    :param local_path: Local path of the file to upload.
    :param cloud_filename: The name of the file to upload in the cloud path including the filepath.
    :param uploadid_local: The upload ID of the file.
    :param md5hash: The MD5 hash of the file/piece to upload.
    :param partseq: The part sequence of the file. Default is 0 (for single file upload).
    :param total_parts: Total number of parts/chunks. Used for progress display.
    :return: The MD5 hash of the file after upload. If the MD5 hash does not match, returns "mismatch". If the upload
    fails, returns "failed".
    """
    label = os.path.basename(local_path)
    url = (f"{BASEURLTB.replace('www', 'c-jp')}:443/rest/2.0/pcs/superfile2?"
           f"method=upload&type=tmpfile&app_id=250528&path={quote_plus(REMOTELOC + '/' + cloud_filename)}&"
           f"uploadid={uploadid_local}&partseq={partseq}")
    try:
        curl_bin = os.path.join("curl", "bin", "curl.exe") if os.name == "nt" else "curl"
        base_command = [curl_bin,
                "-#",           # progress bar to stderr (# chars)
                "-X", "POST",
                "-H", f"User-Agent:{USERAGENT}",
                "-H", f"Origin:{BASEURLTB}",
                "-H", f"Referer:{BASEURLTB}/main?category=all",
                "-H", "Content-Type:multipart/form-data",
                "-b", f"{COOKIES_STR}",
                "-F", f'file=@"{local_path}"',
                url]

        proc = subprocess.Popen(base_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Read stdout (JSON response) in background thread
        import threading
        stdout_chunks = []
        def read_stdout():
            stdout_chunks.append(proc.stdout.read())
        t = threading.Thread(target=read_stdout)
        t.start()

        # curl -# writes a progress bar like: #####################       20.1%
        # Read stderr byte by byte and parse percentage
        buf = b""
        while True:
            byte = proc.stderr.read(1)
            if not byte:
                break
            if byte in (b"\r", b"\n"):
                line = buf.decode("utf-8", errors="ignore").strip()
                buf = b""
                # curl progress bar line contains % sign
                if "%" in line:
                    try:
                        pct_str = [p for p in line.replace("#", "").split() if "%" in p][0]
                        pct = min(int(float(pct_str.replace("%", ""))), 99)
                        if total_parts > 1:
                            print(f"\r[UPLOAD] {label} — chunk {partseq + 1}/{total_parts} ({pct}%)...", end="", flush=True)
                        else:
                            print(f"\r[UPLOAD] {label} — {pct}%...", end="", flush=True)
                    except Exception:
                        pass
            else:
                buf += byte

        t.join()
        proc.wait()
        stdout_data = stdout_chunks[0] if stdout_chunks else b""

        if proc.returncode != 0:
            print(flush=True)
            fmt.error("upload", f"curl exited with code {proc.returncode}.")
            return "failed"

        uresp = json.loads(stdout_data.decode("utf-8"))

        if "error_code" not in uresp:
            if uresp["md5"] == md5hash:
                return uresp["md5"]
            print(flush=True)
            fmt.error("md5", f"MD5 hash mismatch for cloud file {cloud_filename} chunk {partseq}. Skipping file...")
            return "mismatch"

        print(flush=True)
        fmt.error("upload", "File upload failed.")
        fmt.error("upload", f"ERROR: More information: {uresp}")
        return "failed"
    except Exception as exp_upload:
        print(flush=True)
        fmt.error("upload", "File upload request failed.")
        fmt.error("upload", f"More information about this error: {exp_upload}")
        return "failed"


def create_file(cloudpath_local: str, uploadid_local: str, sizebytes: int, md5json_local: str) -> requests.Response:
    """
    Creates a file on the cloud
    :param cloudpath_local: Cloud path of the file to create.
    :param uploadid_local: The upload ID of the file requested previously.
    :param sizebytes: The size of the file in bytes.
    :param md5json_local: The MD5 hash of the file or full file (if in pieces).
    :return: The response of the create file request.
    """
    crresponse = requests.post(f"{BASEURLTB}/api/create",
                               headers={"User-Agent": USERAGENT, "Origin": BASEURLTB,
                                        "Content-Type": "application/x-www-form-urlencoded"},
                               cookies=COOKIES,
                               params={"isdir": "0", "rtype": "1", "app_id": "250528", "jsToken": f"{JSTOKEN}"},
                               data={"path": f"{cloudpath_local}", "uploadid": f"{uploadid_local}",
                                     "target_path": f"{REMOTELOC}/", "size": f"{sizebytes}",
                                     "block_list": f"{md5json_local}"},
                               timeout=10)
    return crresponse


def clean_temp() -> bool:
    """
    Cleans the temp folder
    :return: True if the temp folder was cleaned successfully, False otherwise.
    """
    if os.path.exists(TEMP_DIR):
        fmt.info("temp", "Cleaning up temp directory...")
        for tmpfilename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, tmpfilename)
            try:
                os.remove(file_path)
            except Exception as exp_temp:
                fmt.error("temp", f"File {tmpfilename} could not be deleted.")
                fmt.error("temp", f"More information about this error: {exp_temp}")
                return False
        fmt.success("temp", "Temp directory cleared.")
        return True

    fmt.info("temp", "Creating temp directory...")
    os.mkdir(TEMP_DIR)
    fmt.success("temp", "Temp directory created.")
    return True


# PROGRAM START
clean_temp()  # Clean temp directory

# Get member info and check if the user is a VIP
fmt.info("vip", "Checking if you are a VIP user...")
vip = json.loads(requests.get(f"{BASEURLTB}/rest/2.0/membership/proxy/user?method=query",
                              headers={"User-Agent": USERAGENT, "Origin": BASEURLTB,
                                       "Referer": BASEURLTB + "/main?category=all",
                                       "Content-Type": "application/x-www-form-urlencoded"},
                              cookies=COOKIES, timeout=19).text)["data"]["member_info"]["is_vip"]
fmt.success("vip", f"You are a {'vip' if vip == 1 else 'non-vip'} user.")


def get_files_in_directory(find_dir, base_directory) -> dict:
    """
    Recursively gets all files in the source directory
    :param find_dir:             The directory to get files from
    :param base_directory:  The base directory to get the relative path
    :return:                dict of files in the directory
    """
    dir_files = {}
    for filename in os.listdir(find_dir):
        full_path = os.path.join(find_dir, filename)
        if os.path.isfile(full_path):
            if filename in [".DS_Store", os.path.basename(__file__), "settings.json", "secrets.json"]:
                fmt.warning("upload", f"Skipping file {filename} because it's a protected file.")
                continue
            for exclusion in IGNOREFIL:
                if fnmatch.fnmatch(filename, exclusion):
                    fmt.warning("upload", f"Skipping file {filename} because it's in the ignore list.")
                    continue
            sizebytes = os.path.getsize(full_path)
            relpath = os.path.relpath(full_path, base_directory)
            dir_files.setdefault(find_dir, []).append({"name": filename, "relative_path": relpath, "sizebytes":
                                                       sizebytes, "encrypted": False, "encrypterror": False})
        elif os.path.isdir(full_path):
            dir_files.update(get_files_in_directory(full_path, base_directory))

    return dir_files


# Loop through files in source directory and add to array
try:
    display_source = _short_path(SOURCE_DIR, prefer_base=SOURCE_DIR)
except Exception:
    display_source = SOURCE_DIR
fmt.info("upload", f"Checking files in {display_source}...")
files = get_files_in_directory(SOURCE_DIR, SOURCE_DIR)
if len(files) == 0:
    fmt.success("upload", "No files to upload.")
    fmt.debug("program", "Program closing. Have a nice day!")
    sys.exit()

# ENCRYPTION (IF ENABLED)
if ENCRYPTFL:
    encrypt = Encryption()
    if len(files) == 0:
        fmt.success("encrypt", "No files to encrypt.")

    try:
        KEY_TYPE = encrypt.get_key_type(ENCRYPKEY)
        fmt.debug("encrypt", f"Formatting files using key type: {KEY_TYPE}")
    except Exception as e:
        fmt.error("encrypt", f"Encryption key {ENCRYPKEY} is invalid.")
        fmt.error("encrypt", f"More information about this error: {e}")
        ERRORS = True
        sys.exit()

    fmt.info("encrypt", f"Encrypting files in {SOURCE_DIR}...")
    for directory, files_in_directory in files.items():
        for file in files_in_directory:
            fmt.info("encrypt", f"Encrypting file {file['name']}...")
            try:
                encrypt.encrypt_file(ENCRYPKEY, os.path.join(str(directory),
                                                             str(file['name'].replace(str(directory), ''))))
                file['name'] = f"{file['name']}.enc"
                file['sizebytes'] = os.path.getsize(os.path.join(TEMP_DIR, file['name']))
                file['encrypted'] = True
                fmt.success("encrypt", f"File {file['name']} encrypted successfully.")
            except FileEncryptedException:
                file['name'] = f"{file['name']}.enc"
                file['sizebytes'] = os.path.getsize(os.path.join(TEMP_DIR, file['name']))
                file['encrypted'] = True
                fmt.warning("encrypt", f"File {file['name']} is already encrypted.")
                continue
            except Exception as e:
                fmt.error("encrypt", f"File {file['name']} encryption failed.")
                fmt.error("encrypt", f"More information about this error: {e}")
                file['encrypterror'] = True
                ERRORS = True
                continue

def split_file_with_ffmpeg(file_path: str, file_name: str, size_limit: int) -> list:
    """
    Splits a large file into as many parts as needed to stay under size_limit per part.
    Works for video/audio files using ffmpeg. For non-media files, falls back to raw binary splitting.
    :param file_path: Absolute path to the file to split.
    :param file_name: Name of the file.
    :param size_limit: Maximum allowed size per part in bytes.
    :return: List of dicts representing the split parts, ready for upload.
    """
    base_name, ext = os.path.splitext(file_name)
    file_size = os.path.getsize(file_path)

    # Minimum parts needed: ceil(file_size / size_limit)
    num_parts = math.ceil(file_size / size_limit)

    fmt.info("ffmpeg", f"File {file_name} is {convert_size(file_size)}. Splitting into {num_parts} parts...")

    part_paths = []
    part_names = []
    for i in range(num_parts):
        part_name = f"{base_name}_part{i + 1}{ext}"
        part_names.append(part_name)
        part_paths.append(os.path.join(TEMP_DIR, part_name))

    # Try ffmpeg for media files first
    try:
        # Get duration using ffprobe
        probe_result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        duration = float(probe_result.stdout.decode("utf-8").strip())
        segment_duration = duration / num_parts

        fmt.info("ffmpeg", f"Media file detected. Duration: {duration:.2f}s. "
                            f"Each part will be ~{segment_duration:.2f}s...")

        all_ok = True
        for i in range(num_parts):
            start_time = i * segment_duration
            out_path = part_paths[i]
            # -ss BEFORE -i = fast input-side seeking, no full file scan
            if i < num_parts - 1:
                result = subprocess.run(
                    ["ffmpeg", "-y", "-ss", str(start_time), "-i", file_path,
                     "-t", str(segment_duration), "-c", "copy", out_path],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            else:
                # Last part: no -t, read to end of file
                result = subprocess.run(
                    ["ffmpeg", "-y", "-ss", str(start_time), "-i", file_path,
                     "-c", "copy", out_path],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            if result.returncode != 0:
                all_ok = False
                break
            fmt.success("ffmpeg", f"Part {i + 1}/{num_parts} written: {part_names[i]}")

        if not all_ok:
            raise RuntimeError("ffmpeg split failed on one or more parts.")

    except Exception as e:
        fmt.warning("ffmpeg", f"ffmpeg media split failed ({e}). Falling back to raw binary split...")

        # Fallback: raw binary split into equal byte chunks
        chunk_size = math.ceil(file_size / num_parts)
        try:
            with open(file_path, "rb") as src:
                for i in range(num_parts):
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    with open(part_paths[i], "wb") as part_file:
                        part_file.write(chunk)
                    fmt.success("ffmpeg", f"Binary part {i + 1}/{num_parts} written: {part_names[i]}")
        except Exception as bin_err:
            fmt.error("ffmpeg", f"Binary split also failed: {bin_err}")
            return []

    # Build file-like dicts for each part
    parts = []
    for part_name, part_path in zip(part_names, part_paths):
        if os.path.exists(part_path):
            parts.append({
                "name": part_name,
                "relative_path": part_name,
                "sizebytes": os.path.getsize(part_path),
                "encrypted": False,
                "encrypterror": False,
                "_split_source": file_path,
                "_is_split_part": True,
            })
        else:
            fmt.error("ffmpeg", f"Expected split part not found: {part_name}")
    return parts

def _process_single_file_entry(directory, file, remote_files):
    global ERRORS
    # Safe, forward-slash relative path for logging and cloud comparisons
    rel_disp = file['relative_path'].replace('\\', '/')

    # Determine what the cloud-relative filename will be (append .enc for encrypted files)
    cloud_relative = rel_disp + ('.enc' if file.get('encrypted') else '')

    # Skip if file already exists remotely (compare using the cloud-relative name)
    for remote_file in remote_files:
        if remote_file.get("path", "").endswith(cloud_relative):
            abs_path = os.path.abspath(os.path.join(str(directory), str(file["name"])))
            display_local = _short_path(abs_path, prefer_base=SOURCE_DIR)
            fmt.warning("upload", f"File {file['name']} (OS path: {display_local}) already exists on the cloud. Skipping file...")
            return

    # Local source directory selection
    if file.get('_is_split_part'):
        local_source_dir = TEMP_DIR
        fmt.debug("file", f"File {rel_disp} is a split part. Using temp directory as {TEMP_DIR}.")
    elif file['encrypted']:
        local_source_dir = TEMP_DIR
        fmt.debug("file", f"File {rel_disp} is encrypted. Using source directory as {TEMP_DIR}.")
    else:
        local_source_dir = settings["directories"]["sourcedir"]
        fmt.debug("file", f"File {rel_disp} is not encrypted. Using source directory as {local_source_dir}.")

    fmt.info("upload", f"Uploading {rel_disp} ({convert_size(file['sizebytes'])})...")

    # Quota check
    if SHOWQUOTA:
        quotareq = requests.get(
            f"{BASEURLTB}/api/quota?checkfree=1",
            headers={"User-Agent": USERAGENT},
            cookies=COOKIES,
            timeout=10,
        )
        quota = json.loads(quotareq.text)
        aviquot = quota['total'] - quota['used']
        fmt.debug("quota", f"Available quota: {convert_size(aviquot)}")
        if aviquot < file['sizebytes']:
            fmt.error("quota", f"Not enough quota available for file {file['name']}.")
            return
        fmt.debug("quota", f"Available quota after the upload: {convert_size(aviquot - file['sizebytes'])}")

    # Resolve local file path
    local_file_path = os.path.abspath(os.path.join(local_source_dir, file['relative_path']))
    if file['encrypted']:
        local_file_path = os.path.abspath(os.path.join(TEMP_DIR, file['name']))
    if not os.path.exists(local_file_path):
        try:
            display_missing = _short_path(local_file_path, prefer_base=SOURCE_DIR)
        except Exception:
            display_missing = local_file_path
        fmt.error(
            "upload",
            f"File {display_missing} does not exist on the source directory anymore. Skipping file...",
        )
        ERRORS = True
        return

    # Size limits — attempt ffmpeg split for oversized files
    vip_limit = 21474836479   # 20 GB
    free_limit = 4294967296   # 4 GB
    size_limit = vip_limit if vip == 1 else free_limit
    limit_label = "20GB" if vip == 1 else "4GB"

    if file['sizebytes'] >= size_limit:
        fmt.warning("upload", f"File {file['name']} exceeds the {limit_label} limit "
                               f"({convert_size(file['sizebytes'])}).")
        if FFMPEG_AVAILABLE:
            fmt.info("ffmpeg", f"Attempting to split {file['name']} into {math.ceil(file['sizebytes'] / int(size_limit * 0.95))} parts with ffmpeg...")
            split_parts = split_file_with_ffmpeg(local_file_path, file['name'], size_limit)
            if split_parts:
                fmt.success("ffmpeg", f"Split complete. Uploading {len(split_parts)} parts separately...")
                errors_before = ERRORS
                all_parts_ok = True
                for part in split_parts:
                    if part['sizebytes'] >= size_limit:
                        fmt.error("ffmpeg", f"Split part {part['name']} is still over the limit "
                                             f"({convert_size(part['sizebytes'])}). Skipping.")
                        ERRORS = True
                        all_parts_ok = False
                        continue
                    errors_before_part = ERRORS
                    _process_single_file_entry(TEMP_DIR, part, remote_files)
                    if ERRORS != errors_before_part:
                        all_parts_ok = False

                # If all parts uploaded successfully, handle the original source file
                if all_parts_ok:
                    original_src = os.path.abspath(os.path.join(local_source_dir, file['relative_path']))
                    if MOVEFILES:
                        try:
                            dst_move = os.path.abspath(os.path.join(MOVETOLOC, file['name']))
                            os.rename(original_src, dst_move)
                            fmt.success("move", f"Original file {file['name']} moved to {MOVETOLOC}.")
                        except Exception as e:
                            fmt.error("move", f"Could not move original file {file['name']}: {e}")
                    else:
                        try:
                            os.remove(original_src)
                            fmt.success("cleanup", f"Original file {file['name']} deleted after successful split upload.")
                        except Exception as e:
                            fmt.warning("cleanup", f"Could not delete original file {file['name']}: {e}")
                else:
                    fmt.warning("ffmpeg", f"Not all parts of {file['name']} uploaded successfully. Original file kept.")
            else:
                fmt.error("ffmpeg", f"Splitting failed for {file['name']}. Skipping file.")
                ERRORS = True
        else:
            fmt.error("upload", f"File {file['name']} is too big and ffmpeg is not available to split it.")
            fmt.error("upload", f"File size: {convert_size(file['sizebytes'])}")
            fmt.error("upload", f"Maximum file size for your account: {limit_label}")
            ERRORS = True
        return

    # Build upload pieces and MD5 list
    pieces = []
    md5dict = []
    if file['sizebytes'] >= 2147483648:
        CHUNK_SIZE = CHUNKSIZEMB * 1024 * 1024
        actual_size = os.path.getsize(local_file_path)
        num_chunks = math.ceil(actual_size / CHUNK_SIZE)
        with open(local_file_path, 'rb') as f:
            for i in range(num_chunks):
                print(f"\r[PREP] Splitting chunk {i + 1}/{num_chunks}...", end="", flush=True)
                chunk_filename = os.path.join(TEMP_DIR, f"{file['name']}.part{i:03d}")
                chunk = f.read(CHUNK_SIZE)
                with open(chunk_filename, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                md5dict.append(hashlib.md5(chunk).hexdigest())
                pieces.append(chunk_filename)
        print(f"\r[PREP] {len(pieces)} chunks ready.                    ", flush=True)
    else:
        print(f"\r[PREP] Calculating MD5...", end="", flush=True)
        with open(local_file_path, 'rb') as md5_file:
            md5dict = [hashlib.md5(md5_file.read()).hexdigest()]
        print(f"\r[PREP] Precreating on cloud...", end="", flush=True)
        pieces.append(local_file_path)
    md5json = json.dumps(md5dict)

    # Precreate on cloud
    cloud_relative = rel_disp + ('.enc' if file['encrypted'] else '')
    uploadid = precreate_file(cloud_relative, md5json)
    if uploadid == 'fail':
        print(flush=True)
        ERRORS = True
        return
    print(f"\r[PREP] Ready to upload.                              ", flush=True)
    cloudpath = (os.path.join(REMOTELOC, cloud_relative)).replace('\\', '/')

    # Upload
    upload_failed = False
    if len(pieces) > 1:
        total_chunks = len(pieces)
        for idx, pi in enumerate(pieces):
            resp = upload_file(pi, cloud_relative, uploadid, md5dict[idx], idx, total_chunks)
            if resp in ("failed", "mismatch"):
                upload_failed = True
                break
        if not upload_failed:
            print(f"\r[UPLOAD] {rel_disp} — 100% complete.          ", flush=True)
    else:
        print(f"\r[UPLOAD] {rel_disp} — uploading...", end="", flush=True)
        resp = upload_file(pieces[0], cloud_relative, uploadid, md5dict[0], 0, 1)
        if resp in ("failed", "mismatch"):
            upload_failed = True
        else:
            print(f"\r[UPLOAD] {rel_disp} — 100% complete.          ", flush=True)
    if upload_failed:
        ERRORS = True
        return

    # Create the file on the cloud
    fmt.info("upload", f"Finalizing file {rel_disp} upload...")
    create = create_file(str(cloudpath), uploadid, file['sizebytes'], md5json)
    success_create = json.loads(create.text).get("errno") == 0
    if success_create:
        display_local = _short_path(local_file_path, prefer_base=SOURCE_DIR)
        fmt.success("upload", f"File {display_local} uploaded and saved on cloud successfully.")
        fmt.success("upload", f"The file is now available at {cloudpath} in the cloud.")
    else:
        fmt.error("upload", f"File {file['name']} upload failed.")
        fmt.error("upload", f"More information: {create}")
        ERRORS = True
        return

    # Move/delete
    if MOVEFILES:
        try:
            src_move = os.path.abspath(os.path.join(local_source_dir, file['relative_path']))
            dst_move = os.path.abspath(os.path.join(MOVETOLOC, os.path.basename(file['relative_path'])))
            try:
                display_src_move = _short_path(src_move, prefer_base=SOURCE_DIR)
            except Exception:
                display_src_move = src_move
            try:
                display_dst_move = _short_path(
                    dst_move, prefer_base=MOVETOLOC or os.path.dirname(dst_move)
                )
            except Exception:
                display_dst_move = dst_move
            fmt.info("move", f"Moving file {display_src_move} to {display_dst_move}...")
            os.rename(src_move, dst_move)
            fmt.success("move", f"File {file['name']} moved successfully to destination.")
        except Exception as e:
            fmt.error("move", f"File {file['name']} could not be moved.")
            fmt.error("move", f"More information about this error: {e}")
            ERRORS = True
            return

    if DELSRCFIL:
        try:
            src_del = os.path.abspath(os.path.join(local_source_dir, file['relative_path']))
            try:
                display_src_del = _short_path(src_del, prefer_base=SOURCE_DIR)
            except Exception:
                display_src_del = src_del
            fmt.info("delete", f"Deleting file {display_src_del} from source directory...")
            os.remove(src_del)
            fmt.success("delete", f"File {file['name']} deleted successfully.")
        except Exception as e:
            fmt.error("delete", f"File {file['name']} could not be deleted.")
            fmt.error("delete", f"More information about this error: {e}")
            ERRORS = True
            return

    # Conclude per-file procedure
    try:
        final_path = (
            local_file_path
            if not file['encrypted']
            else os.path.abspath(os.path.join(TEMP_DIR, file['name']))
        )
        display_local = _short_path(final_path, prefer_base=SOURCE_DIR)
    except Exception:
        display_local = file.get('name', 'unknown file')
    fmt.success("upload", f"File {display_local} concluded every upload procedure.")

    # Clean up temp chunks for this file only (scoped to current file's prefix)
    if os.path.exists(TEMP_DIR):
        current_file_prefix = file['name']
        chunks_to_delete = [
            item for item in os.listdir(TEMP_DIR)
            if item.startswith(current_file_prefix) and os.path.isfile(os.path.join(TEMP_DIR, item))
        ]
        total_chunks_cleanup = len(chunks_to_delete)
        for i, item in enumerate(chunks_to_delete):
            print(f"\r[CLEANUP] Deleting chunk {i + 1}/{total_chunks_cleanup}: {item}...", end="", flush=True)
            try:
                os.remove(os.path.join(TEMP_DIR, item))
            except Exception as e:
                print()
                fmt.warning("cleanup", f"Failed to delete temp chunk {item}: {e}")
        if total_chunks_cleanup > 0:
            print(f"\r[CLEANUP] Deleted {total_chunks_cleanup} temp chunks for {file['name']}.          ")

    # Delete source file after successful upload (only if not already handled by MOVEFILES/DELSRCFIL)
    # Skip for split parts — they are already cleaned up by the chunk cleanup above
    if not MOVEFILES and not DELSRCFIL and not file.get('_is_split_part'):
        try:
            src_cleanup = os.path.abspath(os.path.join(local_source_dir, file['relative_path']))
            os.remove(src_cleanup)
            fmt.info("cleanup", f"Deleted source file: {file['name']}")
        except Exception as e:
            fmt.warning("cleanup", f"Could not delete source file {file['name']}: {e}")


remote_files = fetch_remote_directory(REMOTELOC)

for directory, files_in_directory in files.items():
    if not files_in_directory:
        continue
    for file in files_in_directory:
        if file['encrypterror']:
            continue
        _process_single_file_entry(directory, file, remote_files)

if not ERRORS:
    fmt.success("upload", "All files were uploaded.")
    clean_temp()
    fmt.debug("program", "Program closing. Have a nice day!")
else:
    fmt.warning("upload",
                "Some files were not uploaded or had problems while uploading. Please check the logs!")
    fmt.debug("program", "Program closing. Have a nice day!")
