"""
engine/advanced_features.py
============================
NEW FILE - Advanced capabilities added on top of the existing Jarvis engine.

1. Bilingual (Hindi + English) speech OUTPUT       -> speak_bilingual()
2. Bilingual (Hindi + English) speech INPUT         -> recognize_bilingual()
3. "Open VS Code and write <language> code for X"    -> openVSCodeAndWriteCode()
4. "Shutdown / restart my system"                    -> shutdownSystem() / restartSystem()
   + Wake-on-LAN helper to power ON another PC        -> wakeOnLan()
5. "Open Outlook and mail <email>, write a mail..."   -> sendOutlookMail()
6. Advanced "open X" app launcher (Outlook, Gmail, Chrome, VS Code,
   WhatsApp, Spotify, Zoom, Slack, Word/Excel/PowerPoint, GitHub,
   Notion, and more) with desktop-app-first + web-fallback logic
   -> openApp() / smartOpenCommand()

Install the extra dependencies (also added to requirements.txt):
    pip install gTTS pygame

Outlook automation uses win32com (already in requirements.txt as pywin32) and
only works on Windows with Outlook desktop installed. On other platforms, or
if Outlook isn't installed, it automatically falls back to SMTP (configure
SMTP_* values in engine/config.py) and, as a last resort, opens a pre-filled
mailto: draft in the default mail client.
"""

import os
import re
import time
import shutil
import socket
import platform
import subprocess
import traceback
import tempfile
import urllib.parse
import webbrowser

import eel
import requests

from engine.config import (
    ASSISTANT_NAME,
    OLLAMA_URL,
    OLLAMA_MODEL,
    VSCODE_COMMAND,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_USE_TLS,
)


# ---------------------------------------------------------------------------
# 1 & 2. BILINGUAL SPEECH (Hindi + English)
# ---------------------------------------------------------------------------

# DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")


# def is_hindi(text):
#     """True if the text contains Devanagari (Hindi) script."""
#     return bool(DEVANAGARI_RE.search(text))


# def speak_bilingual(text):
#     """
#     Speaks `text`.
#     - If it contains Hindi (Devanagari) characters -> uses gTTS (Hindi voice).
#     - Otherwise -> uses the existing pyttsx3 English voice from engine.command.
#     This is a drop-in replacement for the old speak() function.
#     """
#     text = str(text)

#     try:
#         eel.DisplayMessage(text)
#         eel.receiverText(text)
#     except Exception:
#         pass

#     if is_hindi(text):
#         try:
#             from gtts import gTTS
#             import pygame

#             tmp_path = os.path.join(tempfile.gettempdir(), "jarvis_hi_tts.mp3")
#             gTTS(text=text, lang="hi").save(tmp_path)

#             if not pygame.mixer.get_init():
#                 pygame.mixer.init()

#             pygame.mixer.music.load(tmp_path)
#             pygame.mixer.music.play()

#             while pygame.mixer.music.get_busy():
#                 pygame.time.wait(100)
#             return
#         except Exception as e:
#             print("Hindi TTS failed, falling back to English voice:", e)

#     # English fallback - reuse the pyttsx3 engine already created in command.py
#     try:
#         from engine.command import engine
#         engine.say(text)
#         engine.runAndWait()
#     except Exception:
#         traceback.print_exc()

def speak(text):
    """
    English-only speech output using the existing pyttsx3 engine.
    """
    text = str(text)

    try:
        eel.DisplayMessage(text)
        eel.receiverText(text)
    except Exception:
        pass

    try:
        from engine.command import engine
        engine.say(text)
        engine.runAndWait()
    except Exception:
        traceback.print_exc()
# def recognize_bilingual(recognizer, audio):
#     """
#     Given an already-captured `audio` sample, tries Hindi recognition first,
#     then falls back to Indian English. Returns lowercase text or "".
#     """
#     import speech_recognition as sr

#     # Try Hindi
#     try:
#         query = recognizer.recognize_google(audio, language="hi-IN")
#         if query:
#             return query.lower().strip()
#     except Exception:
#         pass

#     # Fall back to English (India)
#     try:
#         query = recognizer.recognize_google(audio, language="en-IN")
#         return query.lower().strip()
#     except Exception:
#         return ""



def recognize_english(recognizer, audio):
    """
    Recognize English speech only.
    """
    try:
        query = recognizer.recognize_google(audio, language="en-US")
        return query.lower().strip()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Shared helper: talk to the local Ollama model for free-text generation
# ---------------------------------------------------------------------------

def _ask_ai(prompt, timeout=120):
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()["response"].strip()


# ---------------------------------------------------------------------------
# 3. "Open VS Code and write <language> code for X"
# ---------------------------------------------------------------------------

LANGUAGE_EXTENSIONS = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "java": ".java",
    "c++": ".cpp",
    "cpp": ".cpp",
    "c#": ".cs",
    "csharp": ".cs",
    "c": ".c",
    "html": ".html",
    "css": ".css",
    "sql": ".sql",
    "php": ".php",
    "go": ".go",
    "ruby": ".rb",
}


def _detect_language(query):
    for key, ext in LANGUAGE_EXTENSIONS.items():
        if key in query:
            return key, ext
    return "python", ".py"  # default language if none mentioned


def _extract_code_topic(query):
    cleaned = query
    filler_words = [
        ASSISTANT_NAME, "open", "vs code", "vscode", "visual studio code",
        "and", "write", "a", "an", "the", "code", "for", "create",
        "program", "of", "in", "please",
    ]
    for word in filler_words:
        cleaned = re.sub(rf"\b{re.escape(word)}\b", "", cleaned, flags=re.IGNORECASE)
    for lang in LANGUAGE_EXTENSIONS:
        cleaned = re.sub(rf"\b{re.escape(lang)}\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "a simple hello world program"


def generate_code_with_ai(topic, language):
    prompt = (
        f"Write a complete, working {language} program for the following task: "
        f"{topic}. Return ONLY the raw code. Do not include any explanation "
        f"and do not wrap it in markdown code fences."
    )
    code = _ask_ai(prompt)
    # Strip markdown fences just in case the model added them anyway
    code = re.sub(r"^```[a-zA-Z]*\n|```$", "", code.strip(), flags=re.MULTILINE)
    return code.strip()


def openVSCodeAndWriteCode(query):
    """
    Handles commands like:
      "jarvis open vs code and write a python code for bubble sort"
      "open visual studio code write javascript code to reverse a string"
    """
    from engine.command import speak

    try:
        language, ext = _detect_language(query)
        topic = _extract_code_topic(query)

        speak(f"Generating {language} code for {topic}. Please wait.")

        try:
            code = generate_code_with_ai(topic, language)
            if not code:
                raise ValueError("empty response")
        except Exception as e:
            print("AI code generation failed:", e)
            code = (
                f"# Could not reach the AI model to generate code.\n"
                f"# Requested topic: {topic}\n"
                f"# Language: {language}\n"
            )

        folder = os.path.join(os.path.expanduser("~"), "JarvisCode")
        os.makedirs(folder, exist_ok=True)

        slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic).strip("_").lower() or "jarvis_code"
        file_path = os.path.join(folder, f"{slug}{ext}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        speak("Opening Visual Studio Code")

        try:
            subprocess.Popen([VSCODE_COMMAND, file_path])
        except FileNotFoundError:
            speak(
                "VS Code was not found on the PATH. Please install VS Code "
                "and enable 'Add to PATH', then try again."
            )
            if platform.system() == "Windows":
                os.startfile(file_path)
            else:
                subprocess.Popen(["xdg-open", file_path])

        speak(f"I have written the {language} code for {topic} and opened it in VS Code.")

    except Exception:
        traceback.print_exc()
        speak("Sorry, I was not able to complete that VS Code task.")


# ---------------------------------------------------------------------------
# 4. System power control (shutdown / restart) + Wake-on-LAN
# ---------------------------------------------------------------------------

def shutdownSystem(delay_seconds=5):
    """Shuts this machine down. Works on Windows, macOS and Linux."""
    from engine.command import speak

    speak("Shutting down the system now. Goodbye.")
    system = platform.system()
    try:
        if system == "Windows":
            os.system(f"shutdown /s /t {delay_seconds}")
        elif system == "Darwin":
            os.system('osascript -e \'tell app "System Events" to shut down\'')
        else:
            os.system(f"shutdown -h +{max(delay_seconds // 60, 0)}" if delay_seconds >= 60 else "shutdown -h now")
    except Exception:
        traceback.print_exc()
        speak("I was unable to shut down the system.")


def restartSystem(delay_seconds=5):
    """Restarts this machine. Works on Windows, macOS and Linux."""
    from engine.command import speak

    speak("Restarting the system now.")
    system = platform.system()
    try:
        if system == "Windows":
            os.system(f"shutdown /r /t {delay_seconds}")
        elif system == "Darwin":
            os.system('osascript -e \'tell app "System Events" to restart\'')
        else:
            os.system("shutdown -r now")
    except Exception:
        traceback.print_exc()
        speak("I was unable to restart the system.")


def wakeOnLan(mac_address, broadcast_ip="255.255.255.255", port=9):
    """
    Sends a Wake-on-LAN 'magic packet' to power ON another PC on the same
    network (that PC must have WOL enabled in BIOS/NIC settings).

    IMPORTANT: A machine that is fully powered OFF cannot run this code
    itself. This only works when Jarvis (running on an always-on device,
    e.g. a Raspberry Pi or phone) wakes up a *different* PC.
    """
    mac_bytes = bytes.fromhex(mac_address.replace(":", "").replace("-", ""))
    magic_packet = b"\xff" * 6 + mac_bytes * 16

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(magic_packet, (broadcast_ip, port))


# ---------------------------------------------------------------------------
# 5. "Open Outlook and mail <email>, write a mail and send it"
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


def _extract_email(text):
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def _send_via_outlook_com(to_address, subject, body):
    """Windows-only: drives the installed Outlook desktop app via COM
    and actually presses Send. Requires pywin32 (already in requirements.txt)
    and a configured Outlook profile."""
    if platform.system() != "Windows":
        return False
    try:
        import win32com.client

        outlook = win32com.client.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # 0 = olMailItem
        mail.To = to_address
        mail.Subject = subject
        mail.Body = body
        mail.Send()
        return True
    except Exception as e:
        print("Outlook COM automation failed:", e)
        return False


def _send_via_smtp(to_address, subject, body):
    """Cross-platform fallback. Configure SMTP_* in engine/config.py."""
    if not (SMTP_USER and SMTP_PASSWORD):
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to_address

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            if SMTP_USE_TLS:
                server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [to_address], msg.as_string())
        return True
    except Exception as e:
        print("SMTP send failed:", e)
        return False


def _open_mailto_draft(to_address, subject, body):
    """Last-resort fallback: opens a pre-filled draft in the default mail
    app / Outlook web. User has to click Send manually."""
    params = urllib.parse.urlencode({"subject": subject, "body": body})
    webbrowser.open(f"mailto:{to_address}?{params}")


def sendOutlookMail(query):
    """
    Handles commands like:
      "jarvis open outlook and mail john@example.com"
      "open outlook and send a mail to john at example dot com"
    Flow: get recipient -> ask subject -> ask body (or "write it for me" to
    let the AI draft it) -> try Outlook COM -> try SMTP -> fallback mailto.
    """
    from engine.command import speak, takecommand

    try:
        to_address = _extract_email(query)

        if not to_address:
            speak("What is the email address of the recipient?")
            spoken = takecommand()
            spoken = (
                spoken.replace(" at the rate ", "@")
                .replace(" at ", "@")
                .replace(" dot ", ".")
                .replace(" ", "")
            )
            to_address = _extract_email(spoken) or spoken

        if not to_address:
            speak("I could not understand the email address. Cancelling.")
            return

        speak("What should be the subject of the mail?")
        subject = takecommand() or "No subject"

        speak(
            "Tell me what to write in the mail, or say 'write it for me' "
            "and I will draft it for you."
        )
        body_request = takecommand()

        if not body_request or "write it for me" in body_request or "use ai" in body_request:
            speak("Alright, drafting the email for you.")
            try:
                body = _ask_ai(
                    f"Write a short, polite, professional email body about: "
                    f"{subject}. Return only the email body text, no subject "
                    f"line and no placeholder signature."
                )
            except Exception:
                body = "Hello,\n\nThis is an automated message sent by Jarvis.\n\nRegards."
        else:
            body = body_request

        speak(f"Sending mail to {to_address}")

        sent = _send_via_outlook_com(to_address, subject, body)
        if not sent:
            sent = _send_via_smtp(to_address, subject, body)

        if sent:
            speak("The mail has been sent successfully.")
        else:
            speak(
                "I could not send the mail automatically, so I have opened "
                "a draft for you to review and send."
            )
            _open_mailto_draft(to_address, subject, body)

    except Exception:
        traceback.print_exc()
        speak("Something went wrong while sending the mail.")


def openOutlook():
    """Just launches Outlook (no mail composed) - used for a plain
    "open outlook" command, as opposed to sendOutlookMail() which composes
    and sends a mail."""
    openApp("outlook")


# ---------------------------------------------------------------------------
# 6. ADVANCED APP LAUNCHER
# ---------------------------------------------------------------------------
# Fixes "open outlook" (and many other apps) returning "not found".
#
# Outlook has no native Linux desktop build, so on Linux this correctly
# falls back to Outlook on the web. On Windows/Mac it first tries the real
# desktop app. Every entry below follows the same pattern:
#   "windows": [exe_name]                     -> tried with `start <exe>`
#   "darwin":  ["open", "-a", "App Name"]      -> tried directly
#   "linux":   [[cmd1], [cmd2], ...]           -> each tried via shutil.which
#   "web":     "https://..."                  -> opened in the browser if
#                                                 no native app was found
#
# Add your own entries here any time you want Jarvis to recognise a new app.

APP_REGISTRY = {
    "outlook": {
        "windows": ["outlook"],
        "darwin": ["open", "-a", "Microsoft Outlook"],
        "linux": [["thunderbird"], ["evolution"]],
        "web": "https://outlook.office.com/mail/",
    },
    "gmail": {"web": "https://mail.google.com"},
    "chrome": {
        "windows": ["chrome"],
        "darwin": ["open", "-a", "Google Chrome"],
        "linux": [["google-chrome"], ["google-chrome-stable"],
                  ["chromium-browser"], ["chromium"]],
    },
    "firefox": {
        "windows": ["firefox"],
        "darwin": ["open", "-a", "Firefox"],
        "linux": [["firefox"]],
    },
    "edge": {
        "windows": ["msedge"],
        "darwin": ["open", "-a", "Microsoft Edge"],
        "linux": [["microsoft-edge"], ["microsoft-edge-stable"]],
    },
    "vs code": {
        "windows": ["code"],
        "darwin": ["open", "-a", "Visual Studio Code"],
        "linux": [["code"]],
        "web": "https://vscode.dev",
    },
    "whatsapp": {"web": "https://web.whatsapp.com"},
    "telegram": {
        "windows": ["telegram"],
        "linux": [["telegram-desktop"]],
        "web": "https://web.telegram.org",
    },
    "spotify": {
        "windows": ["spotify"],
        "darwin": ["open", "-a", "Spotify"],
        "linux": [["spotify"]],
        "web": "https://open.spotify.com",
    },
    "youtube": {"web": "https://www.youtube.com"},
    "youtube music": {"web": "https://music.youtube.com"},
    "netflix": {"web": "https://www.netflix.com"},
    "teams": {
        "windows": ["teams"],
        "linux": [["teams"]],
        "web": "https://teams.microsoft.com",
    },
    "zoom": {
        "windows": ["zoom"],
        "darwin": ["open", "-a", "zoom.us"],
        "linux": [["zoom"]],
        "web": "https://zoom.us/join",
    },
    "slack": {
        "windows": ["slack"],
        "darwin": ["open", "-a", "Slack"],
        "linux": [["slack"]],
        "web": "https://slack.com/signin",
    },
    "discord": {
        "windows": ["discord"],
        "darwin": ["open", "-a", "Discord"],
        "linux": [["discord"]],
        "web": "https://discord.com/app",
    },
    "notion": {"web": "https://www.notion.so"},
    "google drive": {"web": "https://drive.google.com"},
    "google calendar": {"web": "https://calendar.google.com"},
    "google maps": {"web": "https://maps.google.com"},
    "github": {"web": "https://github.com"},
    "chatgpt": {"web": "https://chat.openai.com"},
    "twitter": {"web": "https://twitter.com"},
    "linkedin": {"web": "https://www.linkedin.com"},
    "instagram": {"web": "https://www.instagram.com"},
    "facebook": {"web": "https://www.facebook.com"},
    "amazon": {"web": "https://www.amazon.in"},
    "word": {
        "windows": ["winword"],
        "darwin": ["open", "-a", "Microsoft Word"],
        "linux": [["libreoffice", "--writer"]],
        "web": "https://www.office.com/launch/word",
    },
    "excel": {
        "windows": ["excel"],
        "darwin": ["open", "-a", "Microsoft Excel"],
        "linux": [["libreoffice", "--calc"]],
        "web": "https://www.office.com/launch/excel",
    },
    "powerpoint": {
        "windows": ["powerpnt"],
        "darwin": ["open", "-a", "Microsoft PowerPoint"],
        "linux": [["libreoffice", "--impress"]],
        "web": "https://www.office.com/launch/powerpoint",
    },
    "notepad": {
        "windows": ["notepad"],
        "darwin": ["open", "-a", "TextEdit"],
        "linux": [["gedit"], ["gnome-text-editor"], ["nano"]],
    },
    "calculator": {
        "windows": ["calc"],
        "darwin": ["open", "-a", "Calculator"],
        "linux": [["gnome-calculator"], ["kcalc"]],
    },
    "terminal": {
        "windows": ["cmd"],
        "darwin": ["open", "-a", "Terminal"],
        "linux": [["gnome-terminal"], ["konsole"], ["xterm"]],
    },
    "file manager": {
        "windows": ["explorer"],
        "darwin": ["open", "."],
        "linux": [["nautilus"], ["dolphin"], ["thunar"]],
    },
}


def _try_native_linux(candidate_cmds):
    """Tries each candidate command list on Linux via shutil.which.
    Returns True on the first one that launches successfully."""
    for cmd in candidate_cmds:
        exe = cmd[0]
        if shutil.which(exe):
            try:
                subprocess.Popen(cmd)
                return True
            except Exception as e:
                print(f"Failed to launch {exe}:", e)
    return False


def _lookup_app(name):
    """Exact match first, then a loose substring match (e.g. 'vscode'
    should still find the 'vs code' entry)."""
    if name in APP_REGISTRY:
        return name, APP_REGISTRY[name]
    for key, entry in APP_REGISTRY.items():
        if key in name or name in key:
            return key, entry
    return None, None


def openApp(name):
    """
    Tries, in order:
      1. The real desktop app for the current OS (Windows/Mac/Linux).
      2. A web fallback (e.g. Outlook -> outlook.office.com) if no
         desktop app was found or none is registered for this OS.
    Returns True if something was opened, False otherwise.
    """
    from engine.command import speak

    name = name.strip().lower()
    key, entry = _lookup_app(name)

    if not entry:
        return False

    system = platform.system()

    try:
        if system == "Windows" and "windows" in entry:
            speak(f"Opening {key}")
            os.system(f"start {entry['windows'][0]}")
            return True

        if system == "Darwin" and "darwin" in entry:
            speak(f"Opening {key}")
            subprocess.Popen(entry["darwin"])
            return True

        if system == "Linux" and "linux" in entry:
            if _try_native_linux(entry["linux"]):
                speak(f"Opening {key}")
                return True

    except Exception as e:
        print(f"Native launch failed for {key}:", e)

    # No native app found/registered for this OS -> try the web version
    web_url = entry.get("web")
    if web_url:
        speak(f"Opening {key} in your browser")
        webbrowser.open(web_url)
        return True

    return False


def smartOpenCommand(query):
    """
    Advanced replacement for a plain "open X" command. Tries, in order:
      1. The curated APP_REGISTRY above (desktop app -> web fallback).
      2. The existing sys_command / web_command database
         (engine.features.openCommand) - anything you've added yourself
         via the Settings UI keeps working exactly as before.
      3. engine.features.openCommand's own raw-OS-open attempt as the
         final fallback (this is what used to print "not found").
    """
    from engine.command import speak

    app_name = query
    for word in [ASSISTANT_NAME, "open"]:
        app_name = re.sub(rf"\b{re.escape(word)}\b", "", app_name, flags=re.IGNORECASE)
    app_name = app_name.strip()

    if not app_name:
        speak("What would you like to open?")
        return

    if openApp(app_name):
        return

    # Not in our curated registry - fall back to the original DB-driven logic
    try:
        from engine.features import openCommand
        openCommand(query)
    except Exception:
        traceback.print_exc()
        speak(f"Sorry, I could not find or open {app_name}")
