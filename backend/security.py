import os

# 🔥 RULES ENGINE (LIKE MINI ANTIVIRUS)
MALWARE_RULES = {
    "Ransomware": ["encrypt", "decrypt", "ransom", "bitcoin", "wallet"],
    "Backdoor": ["socket", "connect(", "bind(", "listen(", "reverse_shell"],
    "Trojan": ["payload", "dropper", "execute", "hidden", "autorun"],
    "Keylogger": ["keyboard", "keylog", "pynput", "listener"],
    "Downloader": ["wget", "curl", "http://", "https://"],
    "Obfuscated": ["base64", "eval(", "exec(", "compile(", "marshal"],
    "System Attack": ["rm -rf", "del /f", "format c:", "shutdown"]
}

DANGEROUS_EXT = [".exe", ".bat", ".cmd", ".vbs", ".ps1", ".dll"]

SCRIPT_TYPES = [".py", ".js", ".sh", ".bat"]


def detect_malware(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    # 🔴 1. Dangerous executable
    if ext in DANGEROUS_EXT:
        return {
            "malware": 1,
            "type": "Executable Threat",
            "severity": "High",
            "reason": "Executable file can run system-level commands"
        }

    # 🔴 2. Scan script content
    try:
        if ext in SCRIPT_TYPES:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(1500).lower()

                for m_type, keywords in MALWARE_RULES.items():
                    for k in keywords:
                        if k in content:
                            return {
                                "malware": 1,
                                "type": m_type,
                                "severity": "High" if m_type in ["Ransomware", "Backdoor"] else "Medium",
                                "reason": f"Detected pattern: {k}"
                            }

    except:
        pass

    # 🟡 3. Suspicious but not confirmed
    try:
        with open(file_path, "rb") as f:
            data = f.read(200)

            if b"MZ" in data:  # Windows binary signature
                return {
                    "malware": 1,
                    "type": "Unknown Binary",
                    "severity": "Medium",
                    "reason": "Binary file signature detected"
                }
    except:
        pass

    # 🟢 4. Safe
    return {
        "malware": 0,
        "type": None,
        "severity": "Safe",
        "reason": None
    }