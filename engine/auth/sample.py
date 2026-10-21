# import cv2

# cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) #create a video capture object which is helpful to capture videos through webcam
# cam.set(3, 640) # set video FrameWidth
# cam.set(4, 480) # set video FrameHeight


# detector = cv2.CascadeClassifier('engine\\auth\\haarcascade_frontalface_default.xml')
# #Haar Cascade classifier is an effective object detection approach

# face_id = input("Enter a Numeric user ID  here:  ")
# #Use integer ID for every new face (0,1,2,3,4,5,6,7,8,9........)

# print("Taking samples, look at camera ....... ")
# count = 0 # Initializing sampling face count

# while True:

#     ret, img = cam.read() #read the frames using the above created object
#     converted_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #The function converts an input image from one color space to another
#     faces = detector.detectMultiScale(converted_image, 1.3, 5)

#     for (x,y,w,h) in faces:

#         cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2) #used to draw a rectangle on any image
#         count += 1

        
#         cv2.imwrite("engine\\auth\\samples\\face." + str(face_id) + '.' + str(count) + ".jpg", converted_image[y:y+h,x:x+w])
#         # To capture & Save images into the datasets folder

#         cv2.imshow('image', img) #Used to display an image in a window

#     k = cv2.waitKey(100) & 0xff # Waits for a pressed key
#     if k == 27: # Press 'ESC' to stop
#         break
#     elif count >= 100: # Take 50 sample (More sample --> More accuracy)
#          break

# print("Samples taken now closing the program....")
# cam.release()
# cv2.destroyAllWindows()



##21oct

import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CASCADE_PATH = os.path.join(
    BASE_DIR, "haarcascade_frontalface_default.xml"
)
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")

os.makedirs(SAMPLES_DIR, exist_ok=True)

# Check that the face detector exists and loads
detector = cv2.CascadeClassifier(CASCADE_PATH)
if detector.empty():
    raise FileNotFoundError(
        f"Cannot load face detector: {CASCADE_PATH}"
    )

# Open the default webcam on Ubuntu
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cam.isOpened():
    cam.release()
    raise RuntimeError(
        "Cannot open webcam. Check camera permissions or try another camera index."
    )

face_id = input("Enter a numeric user ID (use 1 for your face): ").strip()
if not face_id.isdigit():
    cam.release()
    raise ValueError("User ID must be a number.")

print("Look at the camera. Press ESC to stop capturing.")
count = 0

try:
    while count < 100:
        ret, img = cam.read()

        # Prevent the empty-frame error
        if not ret or img is None:
            print("Could not read webcam frame. Retrying...")
            if cv2.waitKey(100) & 0xFF == 27:
                break
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(
            gray, scaleFactor=1.3, minNeighbors=5
        )

        for (x, y, w, h) in faces:
            count += 1
            face_crop = gray[y:y+h, x:x+w]

            filename = os.path.join(
                SAMPLES_DIR, f"face.{face_id}.{count}.jpg"
            )
            cv2.imwrite(filename, face_crop)

            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(
                img, f"Samples: {count}/100",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (255, 0, 0), 2
            )

        cv2.imshow("Face Capture", img)

        if cv2.waitKey(100) & 0xFF == 27:
            break

finally:
    cam.release()
    cv2.destroyAllWindows()

print(f"Capture finished. Saved {count} face samples.")
