# import os
# import eel

# from engine.features import *
# from engine.command import *
# from engine.auth import recoganize
# def start():
    
#     eel.init("www")

#     playAssistantSound()
#     @eel.expose
#     def init():
#         subprocess.call([r'device.bat'])
#         eel.hideLoader()
#         speak("Ready for Face Authentication")
#         flag = recoganize.AuthenticateFace()
#         if flag == 1:
#             eel.hideFaceAuth()
#             speak("Face Authentication Successful")
#             eel.hideFaceAuthSuccess()
#             speak("Hello, Welcome Sir, How can i Help You")
#             eel.hideStart()
#             playAssistantSound()
#         else:
#             speak("Face Authentication Fail")
#     os.system('start msedge.exe --app="http://localhost:8000/index.html"')

#     eel.start('index.html', mode=None, host='localhost', block=True)









import os
import platform
import subprocess
import webbrowser
import eel

from engine.features import *
from engine.command import *
from engine.auth import recoganize


def start():

    eel.init("www")

    playAssistantSound()

    @eel.expose
    def init():

        # Only run device.bat on Windows
        if platform.system() == "Windows":
            subprocess.call(["device.bat"])

        eel.hideLoader()

        speak("Ready for Face Authentication")

        flag = 1

        if flag == 1:
            eel.hideFaceAuth()
            speak("Face Authentication Successful")
            eel.hideFaceAuthSuccess()
            speak("Hello, Welcome. How can I help you?")
            eel.hideStart()
            playAssistantSound()
        else:
            speak("Face Authentication Failed")

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