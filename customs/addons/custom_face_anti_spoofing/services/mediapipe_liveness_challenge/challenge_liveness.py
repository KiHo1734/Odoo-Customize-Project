class ChallengeLiveness:
    def __init__(self, challenges, ear_th, mouth_th, motion_th):
        self.challenges = challenges
        self.idx = 0
        self.queue = deque(maxlen=3)
        self.motion_hist = deque(maxlen=15)

        self.ear_th = ear_th
        self.mouth_th = mouth_th
        self.motion_th = motion_th

    def update_motion(self, landmarks):
        self.motion_hist.append(np.array([[p.x,p.y] for p in landmarks]))

    def motion_live(self):
        if len(self.motion_hist) < 5:
            return False
        d = [
            np.mean(np.linalg.norm(
                self.motion_hist[i]-self.motion_hist[i-1], axis=1))
            for i in range(1,len(self.motion_hist))
        ]
        return np.var(d) > self.motion_th

    def check_action(self, landmarks):
        ear = (eye_aspect_ratio(landmarks,LEFT_EYE)
              +eye_aspect_ratio(landmarks,RIGHT_EYE))/2
        blink = ear < self.ear_th
        mouth = mouth_open_ratio(landmarks) > self.mouth_th
        head = head_turn(landmarks)

        act, _ = self.challenges[self.idx]
        return (
            (act=="blink" and blink) or
            (act=="open_mouth" and mouth) or
            (act=="turn_left" and head=="left") or
            (act=="turn_right" and head=="right")
        )

    def step(self, landmarks):
        self.update_motion(landmarks)

        if self.idx >= len(self.challenges):
            return True, "DONE"

        ok = self.check_action(landmarks)
        self.queue.append(ok)

        if len(self.queue)==3 and all(self.queue):
            self.idx += 1
            self.queue.clear()
            time.sleep(0.4)

        return False, self.challenges[self.idx][1]

    def passed(self):
        return self.idx >= len(self.challenges) and self.motion_live()
