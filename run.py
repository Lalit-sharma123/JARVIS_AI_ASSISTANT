import multiprocessing
import subprocess


# To run Jarvis
def startJarvis():
    # Code for process 1
    print("Process 1 is running.")
    from main import start
    start()


# To run hotword
def listenHotword():
    # Code for process 2
    print("Process 2 is running.")

    # Defensive import: if the hotword feature can't be imported (missing
    # mic hardware, missing pvporcupine/pyaudio dependency, or any other
    # issue), don't crash the whole app - just skip the hotword listener
    # and keep the main assistant running.
    try:
        from engine.features import hotword
    except Exception as e:
        print("Hotword feature unavailable, skipping it:", repr(e))
        return

    try:
        hotword()
    except Exception as e:
        print("Hotword listener stopped due to an error:", repr(e))


# Start both processes
if __name__ == '__main__':
    p1 = multiprocessing.Process(target=startJarvis)
    p2 = multiprocessing.Process(target=listenHotword)
    p1.start()
    p2.start()
    p1.join()

    if p2.is_alive():
        p2.terminate()
        p2.join()

    print("system stop")
