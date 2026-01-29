# -*- coding: utf-8 -*-
import os
import cv2
import math
import time
import random
import numpy as np
import mediapipe as mp
from collections import deque

from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage
from src.utility import parse_model_name

# ===============================
# CONFIG
# ===============================
MODEL_DIR = "./resources/anti_spoof_models"
DEVICE_ID = 0
CAM_ID = 0

EAR_THRESHOLD = 0.19
MOUTH_THRESHOLD = 0.04
MOTION_VAR_THRESHOLD = 1e-5

# ===============================
# MediaPipe Setup
# ===============================
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [263, 387, 385, 362, 380, 373]

# ===============================
# Challenge setup
# ===============================
CHALLENGES = [
    ("blink", "Please Blink"),
    ("open_mouth", "Please Open Your Mouth"),
    ("turn_left", "Turn Your Head Left"),
    ("turn_right", "Turn Your Head Right"),
]

def pick_challenges(n=4):
    return random.sample(CHALLENGES, n)

# ===============================
# Helper Functions
# ===============================
def eye_aspect_ratio(lm, idx):
    p1, p2, p3, p4, p5, p6 = [lm[i] for i in idx]
    v1 = math.dist((p2.x, p2.y), (p6.x, p6.y))
    v2 = math.dist((p3.x, p3.y), (p5.x, p5.y))
    h = math.dist((p1.x, p1.y), (p4.x, p4.y))
    return (v1 + v2) / (2.0 * h + 1e-8)

def mouth_open_ratio(lm):
    return abs(lm[13].y - lm[14].y)

def head_turn(lm):
    c = (lm[234].x + lm[454].x) / 2
    if lm[1].x > c + 0.15:
        return "right"
    if lm[1].x < c - 0.15:
        return "left"
    return "center"

def bbox_from_landmarks(lm, shape, m=20):
    h, w, _ = shape
    xs = [int(p.x * w) for p in lm]
    ys = [int(p.y * h) for p in lm]
    return [
        max(min(xs)-m,0),
        max(min(ys)-m,0),
        min(max(xs)+m,w)-max(min(xs)-m,0),
        min(max(ys)+m,h)-max(min(ys)-m,0)
    ]

def motion_variance(hist):
    if len(hist) < 5:
        return 0
    d = [np.mean(np.linalg.norm(hist[i]-hist[i-1], axis=1)) for i in range(1,len(hist))]
    return np.var(d)

# ===============================
# Init
# ===============================
spoof_model = AntiSpoofPredict(DEVICE_ID)
cropper = CropImage()
model_list = os.listdir(MODEL_DIR)

challenges = pick_challenges()
challenge_idx = 0
queue = deque(maxlen=3)
motion_hist = deque(maxlen=15)
challenge_passed = False
LIVENESS_RESULT = None

cap = cv2.VideoCapture(CAM_ID)

with mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
) as face_mesh:

    print("[i] Press Q or ESC to exit")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame,1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)

        color = (0,255,255)  # <<< FIX: default color

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark

            motion_hist.append(np.array([[p.x,p.y] for p in lm]))
            motion_live = motion_variance(motion_hist) > MOTION_VAR_THRESHOLD

            ear = (eye_aspect_ratio(lm,LEFT_EYE)+eye_aspect_ratio(lm,RIGHT_EYE))/2
            blink = ear < EAR_THRESHOLD
            mouth = mouth_open_ratio(lm) > MOUTH_THRESHOLD
            head = head_turn(lm)

            bbox = bbox_from_landmarks(lm, frame.shape)

            pred = np.zeros((1,3))
            for m in model_list:
                h,w,t,s = parse_model_name(m)
                img = cropper.crop(frame, bbox, s, w, h, crop=s is not None)
                pred += spoof_model.predict(img, os.path.join(MODEL_DIR,m))

            is_real = np.argmax(pred) == 1

            if challenge_idx < len(challenges):
                act, txt = challenges[challenge_idx]
                ok = (
                    (act=="blink" and blink) or
                    (act=="open_mouth" and mouth) or
                    (act=="turn_left" and head=="left") or
                    (act=="turn_right" and head=="right")
                )
                queue.append(ok)
                cv2.putText(frame,f"Challenge {challenge_idx+1}: {txt}",
                            (10,120),0,0.8,(255,255,0),2)
                if len(queue)==3 and all(queue):
                    challenge_idx+=1
                    queue.clear()
                    time.sleep(0.6)
            else:
                challenge_passed = True

            final_real = is_real and challenge_passed and motion_live

            if challenge_passed:
                if final_real:
                    LIVENESS_RESULT = "LIVENESS PASSED"
                    color = (0,255,0)
                else:
                    LIVENESS_RESULT = "LIVENESS FAILED"
                    color = (0,0,255)

            x,y,w,h = bbox
            cv2.rectangle(frame,(x,y),(x+w,y+h),color,2)

            if LIVENESS_RESULT:
                cv2.putText(frame,LIVENESS_RESULT,(10,70),0,1.0,color,3)

            mp_drawing.draw_landmarks(
                frame,res.multi_face_landmarks[0],
                mp_face_mesh.FACEMESH_TESSELATION,
                None,mp_styles.get_default_face_mesh_tesselation_style()
            )

        cv2.imshow("eKYC Anti-Spoof + Challenge", frame)
        if cv2.waitKey(1)&0xFF in [27,ord('q')]:
            break

cap.release()
cv2.destroyAllWindows()
