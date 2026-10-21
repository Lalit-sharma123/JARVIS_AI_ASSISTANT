import platform
import pyttsx3
import speech_recognition as sr
import eel
import time
import traceback
import threading


engine_lock = threading.Lock()
def _speak_worker(text):

    with engine_lock:

        eel.DisplayMessage(text)
        eel.receiverText(text)

        engine.say(text)
        engine.runAndWait()

        
# -------------------------
# Initialize Text-to-Speech
# -------------------------
if platform.system() == "Windows":
    engine = pyttsx3.init("sapi5")
else:
    engine = pyttsx3.init()

voices = engine.getProperty("voices")
if voices:
    engine.setProperty("voice", voices[0].id)

engine.setProperty("rate", 174)

# -------------------------
# Speech Interrupt
# -------------------------

stop_speaking = False
speech_thread = None


# -------------------------
# Speak Function
# -------------------------
# NOTE: speak() now delegates to speak_bilingual() (engine/advanced_features.py)
# so Jarvis automatically speaks Hindi text in Hindi (via gTTS) and English
# text in the normal pyttsx3 voice, without you needing to change anything
# elsewhere in the codebase.
# def speak(text):
#     text = str(text)
#     try:
#         from engine.advanced_features import speak_bilingual
#         speak_bilingual(text)
#     except Exception:
#         # Fall back to the original English-only behaviour if the
#         # advanced_features module or its dependencies are unavailable.
#         eel.DisplayMessage(text)
#         eel.receiverText(text)
#         engine.say(text)
#         engine.runAndWait()
def _speak_worker(text):
    global stop_speaking

    stop_speaking = False

    eel.DisplayMessage(text)
    eel.receiverText(text)

    engine.say(text)

    # while engine.isBusy():

    #     if stop_speaking:
    #         engine.stop()
    #         break

    #     engine.iterate()

    try:
        engine.runAndWait()
    except:
        pass


def speak(text):

    global speech_thread

    if speech_thread and speech_thread.is_alive():
        engine.stop()

    speech_thread = threading.Thread(
        target=_speak_worker,
        args=(str(text),),
        daemon=True
    )

    speech_thread.start()



def stopSpeaking():

    global stop_speaking

    stop_speaking = True

    try:
        engine.stop()
    except:
        pass


# -------------------------
# Speech Recognition (bilingual: Hindi + English)
# -------------------------
def takecommand():

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:

        print("Listening...")
        eel.DisplayMessage("Listening...")

        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 1

        try:
            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )
        except sr.WaitTimeoutError:
            return ""

    print("Recognizing...")
    eel.DisplayMessage("Recognizing...")

    # Try bilingual recognition (Hindi first, then Indian English) via
    # advanced_features. Falls back to plain English recognition if the
    # advanced_features module can't be imported for some reason.
    try:
        # from engine.advanced_features import recognize_bilingual
        # query = recognize_bilingual(recognizer, audio)

        from engine.advanced_features import recognize_english

        query = recognize_english(recognizer, audio)

        
        if query:
            print("User said:", query)
            eel.DisplayMessage(query)
            return query

    except Exception:
        traceback.print_exc()

    try:
        query = recognizer.recognize_google(audio, language="en-IN")

        if query.lower() in [

            "stop",

            "jarvis stop",

            "stop speaking",

            "cancel",

            "enough",

        ]:

            stopSpeaking()

            return ""
        

        print("User said:", query)
        eel.DisplayMessage(query)
        return query.lower().strip()

    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""

    except sr.RequestError as e:
        print("Speech Recognition Error:", e)
        return ""

    except Exception:
        traceback.print_exc()
        return ""


# -------------------------
# Main Command Router
# -------------------------
@eel.expose
def allCommands(message=1):

    # Voice Input
    if message == 1:
        query = takecommand()

    # Typed Input
    else:
        query = str(message)

    # Normalize query
    query = query.lower().strip()

    # Empty query
    if not query:
        speak("Sorry, I didn't catch that.")
        eel.ShowHood()
        return
    

    if query in [

        "stop",

        "jarvis stop",

        "cancel",

        "enough",

    ]:

        stopSpeaking()
        return

    eel.senderText(query)

    print("=" * 60)
    print("Query:", repr(query))
    print("=" * 60)

    try:

        # -----------------------------
        # Play on YouTube
        # -----------------------------
        if "play" in query:

            print(">>> PlayYoutube()")

            from engine.features import PlayYoutube
            PlayYoutube(query)

        # -----------------------------
        # Google Search
        # -----------------------------
        elif "search" in query:

            print(">>> searchGoogle()")

            from engine.features import searchGoogle,searchWeather
            searchGoogle(query)

        # -----------------------------
        # Weather Search
        # -----------------------------
        elif "weather" in query:

            print(">>> searchWeather()")

            from engine.features import searchWeather

            # Remove common words
            location = query
            for word in [
                "weather",
                "what is",
                "what's",
                "today",
                "in",
                "at",
                "of",
                "tell me",
                "show me",
            ]:
                location = location.replace(word, "")

            location = location.strip()

            if not location:
                speak("Which location would you like to know the weather for?")
                location = takecommand()

            searchWeather(location)

        # -----------------------------
        # NEW: Open VS Code and write code
        # e.g. "open vs code and write a python code for bubble sort"
        # -----------------------------
        elif ("vs code" in query or "vscode" in query or "visual studio code" in query):

            print(">>> openVSCodeAndWriteCode()")

            from engine.advanced_features import openVSCodeAndWriteCode
            openVSCodeAndWriteCode(query)

        # -----------------------------
        # NEW: Shutdown the system
        # e.g. "shutdown my system", "shut down the computer"
        # -----------------------------
        elif "shutdown" in query or "shut down" in query or "power off" in query:

            print(">>> shutdownSystem()")

            from engine.advanced_features import shutdownSystem
            shutdownSystem()

        # -----------------------------
        # NEW: Restart the system
        # e.g. "restart my system", "reboot the computer"
        # (Note: a machine that is fully OFF cannot power itself back on;
        # "restart" is the closest real equivalent to "turn my system on".)
        # -----------------------------
        elif "restart" in query or "reboot" in query:

            print(">>> restartSystem()")

            from engine.advanced_features import restartSystem
            restartSystem()

        # -----------------------------
        # NEW: Outlook - either just open it, or compose + send a mail
        # e.g. "open outlook"                       -> just launches Outlook
        # e.g. "open outlook and mail john@x.com"    -> composes and sends
        # -----------------------------
        elif "outlook" in query:

            if "mail" in query or "email" in query or "send" in query:
                print(">>> sendOutlookMail()")
                from engine.advanced_features import sendOutlookMail
                sendOutlookMail(query)
            else:
                print(">>> openOutlook()")
                from engine.advanced_features import openOutlook
                openOutlook()

        # -----------------------------
        # Open Commands (advanced - curated app registry with a
        # desktop-app-first + web-fallback strategy, falling back to the
        # existing sys_command / web_command database if an app isn't in
        # the curated list)
        # -----------------------------
        elif "open" in query:

            print(">>> smartOpenCommand()")

            from engine.advanced_features import smartOpenCommand
            smartOpenCommand(query)

        # -----------------------------
        # WhatsApp / Mobile Commands
        # -----------------------------
        elif (
            "send message" in query
            or "phone call" in query
            or "video call" in query
        ):

            from engine.features import (
                findContact,
                whatsApp,
                makeCall,
                sendMessage,
            )

            contact_no, name = findContact(query)

            if contact_no != 0:

                speak("Which mode do you want to use? WhatsApp or Mobile?")

                preference = takecommand()

                if "mobile" in preference:

                    if "send message" in query:

                        speak("What message should I send?")
                        message = takecommand()

                        sendMessage(
                            message,
                            contact_no,
                            name
                        )

                    elif "phone call" in query:

                        makeCall(
                            name,
                            contact_no
                        )

                elif "whatsapp" in preference:

                    mode = ""

                    if "send message" in query:

                        mode = "message"

                        speak("What message should I send?")
                        msg = takecommand()

                        whatsApp(
                            contact_no,
                            msg,
                            mode,
                            name
                        )

                    elif "phone call" in query:

                        whatsApp(
                            contact_no,
                            "",
                            "call",
                            name
                        )

                    elif "video call" in query:

                        whatsApp(
                            contact_no,
                            "",
                            "video call",
                            name
                        )

        # -----------------------------
        # AI Chat
        # -----------------------------
        else:

            print(">>> geminai()")

            from engine.features import geminai
            geminai(query)

    except Exception:
        traceback.print_exc()

    eel.ShowHood()
