import os
import hashlib

# ================= HASH =================
def get_file_hash(path):
    try:
        hasher = hashlib.md5()

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)

        return hasher.hexdigest()
    except:
        return None


# ================= PREVIEW =================
def get_preview(path, limit=300):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read(limit)
            return data if data.strip() else None
    except:
        return None


# ================= MALWARE RULE ENGINE =================
MALWARE_RULES = {
    "Ransomware": ["encrypt", "decrypt", "bitcoin", "wallet"],
    "Backdoor": ["socket", "connect(", "bind(", "reverse_shell"],
    "Trojan": ["payload", "autorun", "hidden"],
    "Keylogger": ["keylog", "keyboard", "pynput"],
    "Downloader": ["wget", "curl", "http://", "https://"],
    "Obfuscated": ["base64", "eval(", "exec("],
    "System Attack": ["rm -rf", "del /f", "format c:"]
}

DANGEROUS_EXT = [".exe", ".bat", ".cmd", ".vbs", ".ps1", ".dll"]
SCRIPT_TYPES = [".py", ".js", ".sh", ".bat"]


def detect_malware(path):
    ext = os.path.splitext(path)[1].lower()

    # 🔴 Executable threat
    if ext in DANGEROUS_EXT:
        return {
            "malware": 1,
            "type": "Executable Threat",
            "severity": "High",
            "reason": "Executable file"
        }

    # 🔴 Script scanning
    try:
        if ext in SCRIPT_TYPES:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(1000).lower()

                for mtype, keywords in MALWARE_RULES.items():
                    for k in keywords:
                        if k in content:
                            return {
                                "malware": 1,
                                "type": mtype,
                                "severity": "High" if mtype in ["Ransomware", "Backdoor"] else "Medium",
                                "reason": k
                            }
    except:
        pass

    # 🟡 Binary check
    try:
        with open(path, "rb") as f:
            if b"MZ" in f.read(200):
                return {
                    "malware": 1,
                    "type": "Binary",
                    "severity": "Medium",
                    "reason": "Binary signature"
                }
    except:
        pass

    return {
        "malware": 0,
        "type": None,
        "severity": "Safe",
        "reason": None
    }


# ================= SCANNER =================
def scan_folder(path, progress):
    files_data = []

    if not os.path.exists(path):
        return []

    skip_folders = {"node_modules", "$Recycle.Bin", "Windows", "Program Files", "AppData"}

    try:
        progress["total"] = 0
        progress["current"] = 0
        progress["status"] = "Scanning"

        # 🔥 COUNT FILES
        total = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in skip_folders]
            total += len(files)

        progress["total"] = total

        # 🔥 PROCESS FILES
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in skip_folders]

            for file in files:

                if progress.get("stop"):
                    progress["status"] = "Stopped"
                    return files_data

                full_path = os.path.join(root, file)

                try:
                    size = os.path.getsize(full_path)
                    modified = os.path.getmtime(full_path)
                    file_hash = get_file_hash(full_path)
                except:
                    size = 0
                    modified = 0
                    file_hash = None

                # 🔥 PREVIEW
                ext = os.path.splitext(file)[1].lower()
                preview = None

                if ext in [".txt", ".py", ".js", ".json", ".md", ".log"]:
                    preview = get_preview(full_path)

                # 🔥 MALWARE
                m = detect_malware(full_path)

                files_data.append({
                    "name": file,
                    "path": full_path,
                    "type": ext.replace(".", "") or "unknown",
                    "size": size,
                    "modified": modified,
                    "hash": file_hash,
                    "preview": preview,
                    "malware": m["malware"],
                    "malware_type": m["type"],
                    "malware_severity": m["severity"],
                    "malware_reason": m["reason"]
                })

                # 🔥 PROGRESS UPDATE
                progress["current"] += 1
                progress["current_folder"] = root
                progress["current_file"] = file   # ✅ IMPORTANT

                if progress["current"] % 100 == 0:
                    print("Scanned:", progress["current"])

        progress["status"] = "Completed"

    except Exception as e:
        print("Error:", e)

    return files_data