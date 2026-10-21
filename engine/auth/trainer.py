# import cv2
# import numpy as np
# from PIL import Image #pillow package
# import os

# path = 'engine\\auth\\samples' # Path for samples already taken

# recognizer = cv2.face.LBPHFaceRecognizer_create() # Local Binary Patterns Histograms
# detector = cv2.CascadeClassifier("engine\\auth\\haarcascade_frontalface_default.xml")
# #Haar Cascade classifier is an effective object detection approach


# def Images_And_Labels(path): # function to fetch the images and labels

#     imagePaths = [os.path.join(path,f) for f in os.listdir(path)]     
#     faceSamples=[]
#     ids = []

#     for imagePath in imagePaths: # to iterate particular image path

#         gray_img = Image.open(imagePath).convert('L') # convert it to grayscale
#         img_arr = np.array(gray_img,'uint8') #creating an array

#         id = int(os.path.split(imagePath)[-1].split(".")[1])
#         faces = detector.detectMultiScale(img_arr)

#         for (x,y,w,h) in faces:
#             faceSamples.append(img_arr[y:y+h,x:x+w])
#             ids.append(id)

#     return faceSamples,ids

# print ("Training faces. It will take a few seconds. Wait ...")

# faces,ids = Images_And_Labels(path)
# recognizer.train(faces, np.array(ids))

# recognizer.write('engine\\auth\\trainer\\trainer.yml')  # Save the trained model as trainer.yml

# print("Model trained, Now we can recognize your face.")




import cv2
import numpy as np
from PIL import Image
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
CASCADE_PATH = os.path.join(
    BASE_DIR, "haarcascade_frontalface_default.xml"
)
MODEL_DIR = os.path.join(BASE_DIR, "trainer")
MODEL_PATH = os.path.join(MODEL_DIR, "trainer.yml")

if not hasattr(cv2, "face"):
    raise RuntimeError(
        "cv2.face is unavailable. Install opencv-contrib-python "
        "in your active Python environment."
    )

recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier(CASCADE_PATH)

if detector.empty():
    raise FileNotFoundError(
        f"Could not load face detector: {CASCADE_PATH}"
    )


def Images_And_Labels(path):
    face_samples = []
    ids = []

    for filename in os.listdir(path):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        image_path = os.path.join(path, filename)

        try:
            image = Image.open(image_path).convert("L")
            img_array = np.array(image, dtype="uint8")
        except Exception as error:
            print(f"Skipping {filename}: {error}")
            continue

        # Expected filename format: face.ID.NUMBER.jpg
        parts = filename.split(".")
        if len(parts) < 3 or not parts[1].isdigit():
            print(f"Skipping unexpected filename: {filename}")
            continue

        face_id = int(parts[1])
        detected_faces = detector.detectMultiScale(
            img_array,
            scaleFactor=1.2,
            minNeighbors=5
        )

        for (x, y, w, h) in detected_faces:
            face_samples.append(img_array[y:y+h, x:x+w])
            ids.append(face_id)

    return face_samples, ids


print("Training faces. Please wait...")

faces, ids = Images_And_Labels(SAMPLES_DIR)

if not faces:
    raise RuntimeError(
        "No faces detected in the sample images. "
        "Capture your face again before training."
    )

os.makedirs(MODEL_DIR, exist_ok=True)

recognizer.train(faces, np.array(ids, dtype=np.int32))
recognizer.write(MODEL_PATH)

print(f"Training complete. Model saved to: {MODEL_PATH}")
print(f"Face samples used: {len(faces)}")
print(f"IDs trained: {sorted(set(ids))}")
