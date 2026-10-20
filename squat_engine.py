"""Web adapter for the user's ORIGINAL squat scoring functions.

The original_squat_coach.py file is a byte-for-byte copy and is NEVER edited.
We load only its function definitions, without running its interactive input()
main program. Its ten original functions, formulas, weights and thresholds are
executed unchanged.
"""

import ast
import math
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

ORIGINAL_PATH = Path(__file__).with_name("original_squat_coach.py")
_source = ORIGINAL_PATH.read_text(encoding="utf-8")
_module = ast.parse(_source, filename=str(ORIGINAL_PATH))
_definitions = [node for node in _module.body if isinstance(node, ast.FunctionDef)]
_original_functions = compile(
    ast.fix_missing_locations(ast.Module(body=_definitions, type_ignores=[])),
    str(ORIGINAL_PATH),
    "exec",
)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

NAMES = ["Depth", "Core", "Coordination", "Posture", "Hip Load", "Knee Track"]


def original_functions_for_photo():
    """Create an isolated copy of unchanged user functions for one photo.

    In the original script, score_hip_load() reads the module-global 'shoulder'
    set in MAIN. We provide that SAME global in this private context, rather
    than changing any original function/signature. This also keeps users/photos
    isolated from each other on a shared web server.
    """
    namespace = {"math": math, "mp_pose": mp_pose}
    exec(_original_functions, namespace)
    return namespace


def _existing_feedback(sc, knee_angle, torso_angle, low, high, posture_dir):
    """Keep the original first-photo feedback wording and thresholds."""
    s1, s2, s3, s4, s5, s6 = (sc[k] for k in NAMES)
    notes = []
    if s3 >= 80:
        notes.append(("[GOOD] Coordination", "Stable torso angle"))
    elif s3 >= 60:
        if torso_angle < low:
            notes.append(("[OK] Coordination", "Torso too small (lean too upright / backward bias)"))
        elif torso_angle > high:
            notes.append(("[OK] Coordination", "Torso too large (lean too forward)"))
        else:
            notes.append(("[OK] Coordination", "Acceptable coordination but needs refinement"))
    else:
        if torso_angle < low:
            notes.append(("[LOW] Coordination", "Torso too small (lean too upright)"))
        elif torso_angle > high:
            notes.append(("[LOW] Coordination", "Torso too large (lean too forward)"))
        else:
            notes.append(("[LOW] Coordination", "Poor coordination control"))

    if s4 >= 80:
        notes.append(("[GOOD] Posture", "Stable body alignment"))
    elif s4 >= 60:
        if posture_dir == "FORWARD":
            notes.append(("[OK] Posture", "Leaning a little FORWARD"))
        elif posture_dir == "BACKWARD":
            notes.append(("[OK] Posture", "Leaning a little BACKWARD"))
        else:
            notes.append(("[OK] Posture", "Slight imbalance, can improve"))
    else:
        if posture_dir == "FORWARD":
            notes.append(("[LOW] Posture", "Leaning too FORWARD"))
        elif posture_dir == "BACKWARD":
            notes.append(("[LOW] Posture", "Leaning too BACKWARD"))
        else:
            notes.append(("[LOW] Posture", "Poor posture control"))

    f = original_functions_for_photo()["feedback"]
    for name, score, good, mid, bad in [
        ("Depth", s1, "Good depth control", "Slightly shallow", "Too shallow"),
        ("Core", s2, "Stable core", "Moderate instability", "Poor balance"),
        ("Hip Load", s5, "Hip dominant", "Moderate knee use", "Knee dominant"),
        ("Knee Track", s6, "Safe knee position", "Slight forward knee", "Unsafe forward knee position"),
    ]:
        notes.append(f(name, score, good, mid, bad))
    return notes


def analyze_squat(file_data: bytes):
    """Return ORIGINAL scores and annotations for one camera/uploaded JPG/PNG.

    Raises ValueError with a readable message if a valid squat cannot be found.
    """
    photo = np.frombuffer(file_data, dtype=np.uint8)
    img = cv2.imdecode(photo, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("The image could not be read. Try JPG or PNG.")

    # Preserve original calculations, including integer pixel coordinates.
    fn = original_functions_for_photo()
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    with mp_pose.Pose(static_image_mode=True) as pose:
        results = pose.process(img_rgb)
    if not results.pose_landmarks:
        raise ValueError("No person detected. Please show your full body from the side.")

    h, w, _ = img.shape
    lm = results.pose_landmarks.landmark
    get_point = fn["get_average_point"]
    shoulder = get_point(lm, w, h, "SHOULDER", "SHOULDER")
    hip = get_point(lm, w, h, "HIP", "HIP")
    knee = get_point(lm, w, h, "KNEE", "KNEE")
    ankle = get_point(lm, w, h, "ANKLE", "ANKLE")

    knee_angle = fn["calculate_angle"](hip, knee, ankle)
    leg_len = fn["calculate_distance"](knee, ankle)
    dx, dy = abs(shoulder[0] - hip[0]), abs(shoulder[1] - hip[1])
    torso_angle = math.degrees(math.atan2(dx, dy)) if dy > 0 else 0
    facing_right = knee[0] > hip[0]
    if knee_angle >= 150:
        raise ValueError("Not a squat: please photograph your squat position, not standing upright.")

    fn["shoulder"] = shoulder  # Original MAIN establishes this same global.
    s1 = fn["score_depth"](knee_angle)
    s2 = fn["score_core"](shoulder, hip, knee, ankle, leg_len, facing_right)
    s3 = fn["score_coordination"](knee_angle, torso_angle)
    s4, diff, low, high, posture_dir = fn["score_posture"](
        shoulder, knee, leg_len, facing_right, knee_angle
    )
    s5 = fn["score_hip_load"](hip, knee, ankle)
    s6 = fn["score_knee_track"](knee, ankle, leg_len, facing_right, knee_angle)

    # EXACT original scoring weights and total truncation.
    total = int(s1 * .25 + s2 * .15 + s3 * .20 + s4 * .15 + s5 * .10 + s6 * .15)
    scores = dict(zip(NAMES, [s1, s2, s3, s4, s5, s6]))
    notes = _existing_feedback(scores, knee_angle, torso_angle, low, high, posture_dir)

    # Original skeleton + original on-photo text/colors/positions.
    annotated = img.copy()
    mp_drawing.draw_landmarks(annotated, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
    cv2.putText(annotated, f"TOTAL: {total}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (180,150,200), 2)
    for caption, value, y, color in [
        ("Depth", s1, 90, (110,160,130)),
        ("Core", s2, 120, (160,140,100)),
        ("Coord", s3, 150, (100,190,190)),
        ("Posture", s4, 180, (120,140,210)),
        ("HipLoad", s5, 210, (180,120,160)),
        ("KneeTrk", s6, 240, (100,100,200)),
    ]:
        cv2.putText(annotated, f"{caption}: {int(value)}", (50, y), cv2.FONT_HERSHEY_SIMPLEX, .6, color, 2)

    ok, encoded = cv2.imencode(".jpg", annotated)
    if not ok:
        raise ValueError("Could not create an annotated result image.")
    return {
        "scores": scores, "total": total, "feedback": notes,
        "knee_angle": knee_angle, "torso_angle": torso_angle,
        "facing": "RIGHT" if facing_right else "LEFT",
        "annotated_image": encoded.tobytes(),
    }


def compare_squats(before, after):
    """Comparison does not modify or recalculate original photo scores."""
    changes = {name: after["scores"][name] - before["scores"][name] for name in NAMES}
    better = [name for name, delta in changes.items() if delta > 1]
    lower = [name for name, delta in changes.items() if delta < -1]
    similar = [name for name, delta in changes.items() if -1 <= delta <= 1]

    # New advice is text-only, not part of the user's original scoring algorithm.
    advice_by_metric = {
        "Depth": "Next attempt: Try a slow, controlled squat to a comfortable depth, keeping your feet grounded.",
        "Core": "Next attempt: Keep your whole foot grounded and check your balance with a controlled tempo.",
        "Coordination": "Next attempt: Move slowly and find a torso position that feels controlled throughout your squat.",
        "Posture": "Next attempt: Try a controlled descent and check your torso position from the same camera angle.",
        "Hip Load": "Next attempt: Explore comfortable hip and knee bending together; avoid forcing a particular loading pattern.",
        "Knee Track": "Next attempt: Check your knee movement during a slow squat and keep the same side-view camera position.",
    }
    if lower:
        focus = min(lower, key=lambda name: changes[name])
    else:
        focus = min(NAMES, key=lambda name: after["scores"][name])
    return {
        "changes": changes, "improved": better, "declined": lower, "similar": similar,
        "total_change": after["total"] - before["total"],
        "next_focus": focus,
        "next_advice": advice_by_metric[focus],
        "consistent_view": before["facing"] == after["facing"],
    }
