# import os
# import platform
# import subprocess
# import webbrowser
# import eel

# from engine.features import *
# from engine.command import *
# from engine.auth import recoganize

# # --- Explicit imports (fix for "NameError: name 'playAssistantSound' is not
# # defined") ---
# # `from engine.features import *` should already bring this in, but if the
# # wildcard import ever silently misses it (stale __pycache__, partial import
# # during a crash, etc.) main.py would crash the moment start() runs. Importing
# # it explicitly guarantees the name exists no matter what.
# try:
#     from engine.features import playAssistantSound
# except Exception as e:
#     print("Warning: could not import playAssistantSound, using a no-op fallback:", e)

#     def playAssistantSound():
#         pass


# def start():

#     eel.init("www")

#     playAssistantSound()

#     @eel.expose
#     def init():

#         # Only run device.bat on Windows
#         if platform.system() == "Windows":
#             subprocess.call(["device.bat"])

#         eel.hideLoader()

#         speak("Ready for Face Authentication")

#         flag = 1

#         if flag == 1:
#             eel.hideFaceAuth()
#             speak("Face Authentication Successful")
#             eel.hideFaceAuthSuccess()
#             speak("Hello, Welcome. How can I help you?")
#             eel.hideStart()
#             playAssistantSound()
#         else:
#             speak("Face Authentication Failed")

#     url = "http://localhost:8000/index.html"

#     if platform.system() == "Windows":
#         os.system(f'start msedge.exe --app="{url}"')
#     else:
#         try:
#             subprocess.Popen(["google-chrome", "--app=" + url])
#         except FileNotFoundError:
#             webbrowser.open(url)

#     eel.start(
#         "index.html",
#         mode=None,
#         host="localhost",
#         port=8000,
#         block=True,
#     )


# if __name__ == "__main__":
#     start()




##face auth 21oct 

import os
import platform
import subprocess
import webbrowser
import eel

from engine.features import *
from engine.command import *
from engine.auth.recoganize import AuthenticateFace


try:
    from engine.features import playAssistantSound
except Exception as e:
    print("Warning: could not import playAssistantSound:", e)

    def playAssistantSound():
        pass


def start():
    eel.init("www")

    @eel.expose
    def init():
        # Run device.bat only on Windows
        if platform.system() == "Windows":
            subprocess.call(["device.bat"])

        eel.hideLoader()

        speak("Ready for Face Authentication")

        try:
            flag = AuthenticateFace()
        except Exception as e:
            print("Face authentication error:", e)
            flag = 0

        if flag == 1:
            eel.hideFaceAuth()
            speak("Face Authentication Successful")
            eel.hideFaceAuthSuccess()
            speak("Hello, Welcome. How can I help you?")
            eel.hideStart()
            playAssistantSound()
        else:
            speak("Face Authentication Failed")
            print("Authentication failed. Access not granted.")

    url = "http://localhost:8000/index.html"

    if platform.system() == "Windows":
        os.system(f'start msedge.exe --app="{url}"')
    else:
        try:
            subprocess.Popen(["google-chrome", "--app=" + url])
        except FileNotFoundError:
            webbrowser.open(url)

    eel.start(
        "index.html",
        mode=None,
        host="localhost",
        port=8000,
        block=True,
    )


if __name__ == "__main__":
    start()
