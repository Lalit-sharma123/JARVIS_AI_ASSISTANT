# from sys import flags
# import time
# import cv2
# import pyautogui as p


# def AuthenticateFace():

#     flag = ""
#     # Local Binary Patterns Histograms
#     recognizer = cv2.face.LBPHFaceRecognizer_create()

#     recognizer.read('engine\\auth\\trainer\\trainer.yml')  # load trained model
#     cascadePath = "engine\\auth\\haarcascade_frontalface_default.xml"
#     # initializing haar cascade for object detection approach
#     faceCascade = cv2.CascadeClassifier(cascadePath)

#     font = cv2.FONT_HERSHEY_SIMPLEX  # denotes the font type


#     id = 2  # number of persons you want to Recognize


#     names = ['', 'Digambar']  # names, leave first empty bcz counter starts from 0


#     cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # cv2.CAP_DSHOW to remove warning
#     cam.set(3, 640)  # set video FrameWidht
#     cam.set(4, 480)  # set video FrameHeight

#     # Define min window size to be recognized as a face
#     minW = 0.1*cam.get(3)
#     minH = 0.1*cam.get(4)

#     # flag = True

#     while True:

#         ret, img = cam.read()  # read the frames using the above created object

#         # The function converts an input image from one color space to another
#         converted_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#         faces = faceCascade.detectMultiScale(
#             converted_image,
#             scaleFactor=1.2,
#             minNeighbors=5,
#             minSize=(int(minW), int(minH)),
#         )

#         for(x, y, w, h) in faces:

#             # used to draw a rectangle on any image
#             cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

#             # to predict on every single image
#             id, accuracy = recognizer.predict(converted_image[y:y+h, x:x+w])

#             # Check if accuracy is less them 100 ==> "0" is perfect match
#             if (accuracy < 100):
#                 id = names[id]
#                 accuracy = "  {0}%".format(round(100 - accuracy))
#                 flag = 1
#             else:
#                 id = "unknown"
#                 accuracy = "  {0}%".format(round(100 - accuracy))
#                 flag = 0

#             cv2.putText(img, str(id), (x+5, y-5), font, 1, (255, 255, 255), 2)
#             cv2.putText(img, str(accuracy), (x+5, y+h-5),
#                         font, 1, (255, 255, 0), 1)

#         cv2.imshow('camera', img)

#         k = cv2.waitKey(10) & 0xff  # Press 'ESC' for exiting video
#         if k == 27:
#             break
#         if flag == 1:
#             break
            

#     # Do a bit of cleanup
    
#     cam.release()
#     cv2.destroyAllWindows()
#     return flag





##face auth 21 oct

import time
import platform
import cv2
import pyautogui as p


def AuthenticateFace():
    flag = 0

    # Load the trained Local Binary Patterns Histograms model
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("engine/auth/trainer/trainer.yml")

    cascade_path = "engine/auth/haarcascade_frontalface_default.xml"
    faceCascade = cv2.CascadeClassifier(cascade_path)

    if faceCascade.empty():
        raise RuntimeError(f"Could not load face cascade: {cascade_path}")

    font = cv2.FONT_HERSHEY_SIMPLEX

    # Names corresponding to the IDs used during training
    names = ["", "Digambar"]

    # Use the appropriate camera backend for the operating system
    if platform.system() == "Windows":
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    else:
        cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        cam.release()
        cv2.destroyAllWindows()
        print("Error: Could not open camera.")
        return 0

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    minW = int(0.1 * cam.get(cv2.CAP_PROP_FRAME_WIDTH))
    minH = int(0.1 * cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

    try:
        while True:
            ret, img = cam.read()

            if not ret:
                print("Error: Could not read from camera.")
                break

            converted_image = cv2.cvtColor(
                img, cv2.COLOR_BGR2GRAY
            )

            faces = faceCascade.detectMultiScale(
                converted_image,
                scaleFactor=1.2,
                minNeighbors=5,
                minSize=(minW, minH),
            )

            for (x, y, w, h) in faces:
                cv2.rectangle(
                    img,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2,
                )

                predicted_id, distance = recognizer.predict(
                    converted_image[y:y + h, x:x + w]
                )

                # LBPH uses lower distance values for better matches.
                # Tune this threshold using your trained model.
                if distance < 100 and 0 < predicted_id < len(names):
                    display_name = names[predicted_id]
                    flag = 1
                else:
                    display_name = "unknown"

                confidence = f"{max(0, min(100, round(100 - distance)))}%"

                cv2.putText(
                    img,
                    display_name,
                    (x + 5, y - 5),
                    font,
                    1,
                    (255, 255, 255),
                    2,
                )

                cv2.putText(
                    img,
                    confidence,
                    (x + 5, y + h - 5),
                    font,
                    1,
                    (255, 255, 0),
                    1,
                )

            cv2.imshow("Face Authentication", img)

            key = cv2.waitKey(10) & 0xFF

            if key == 27 or flag == 1:
                break

    finally:
        cam.release()
        cv2.destroyAllWindows()

    return flag
