"""Mobile-friendly two-photo Streamlit UI, leaving original_squat_coach.py untouched."""

import streamlit as st

from squat_engine import NAMES, analyze_squat, compare_squats

st.set_page_config(page_title="AI Squat Coach", page_icon="🏋️", layout="centered")
st.markdown("""
<style>
.block-container {max-width: 900px; padding-top: 1.5rem;}
[data-testid="stMetricValue"] {font-size: 2rem;}
</style>
""", unsafe_allow_html=True)

st.title("🏋️ AI Squat Coach")
st.caption("Take a photo → Get feedback → Adjust → Retake → Compare")
st.write("An accessible squat practice tool powered by your original pose-scoring algorithm.")

if "widget_round" not in st.session_state:
    st.session_state.widget_round = 0
if "first_result" not in st.session_state:
    st.session_state.first_result = None
if "second_result" not in st.session_state:
    st.session_state.second_result = None


def photo_input(prefix):
    round_id = st.session_state.widget_round
    camera = st.camera_input("Take a photo", key=f"{prefix}_{round_id}_camera")
    upload = st.file_uploader(
        "Or upload a photo", type=["jpg", "jpeg", "png"], key=f"{prefix}_{round_id}_upload"
    )
    # A newly captured camera image takes precedence over uploaded photo.
    return camera if camera is not None else upload


def show_analysis(result):
    st.image(result["annotated_image"], caption="Original score and pose landmarks", use_container_width=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total", f'{result["total"]}/100')
    col2.metric("Knee angle", f'{result["knee_angle"]:.0f}°')
    col3.metric("Torso angle", f'{result["torso_angle"]:.0f}°')
    st.write("**Your original feedback:**")
    for status, message in result["feedback"]:
        st.write(f"**{status}** — {message}")


def run_analysis(file, key):
    try:
        with st.spinner("Analyzing your squat..."):
            result = analyze_squat(file.getvalue())
        st.session_state[key] = result
        return True
    except ValueError as exc:
        st.error(str(exc))
        return False
    except Exception as exc:
        st.error("Analysis could not run. Please retry with a clear side-view photo.")
        # Expanded error available for local development without exposing it in the main UI.
        with st.expander("Technical details"):
            st.code(f"{type(exc).__name__}: {exc}")
        return False


with st.expander("📷 Photo tips (important for fair comparison)", expanded=True):
    st.write("Use a **full-body side view** at the bottom of your squat. Keep the phone at roughly the **same height, distance and angle** for both photos. Keep lighting and exercise conditions similar. Avoid hiding your hip, knee or ankle.")

if st.session_state.first_result is None:
    st.subheader("Step 1 · First squat photo")
    first_photo = photo_input("first")
    if st.button("Analyze first photo", type="primary", disabled=first_photo is None, use_container_width=True):
        if run_analysis(first_photo, "first_result"):
            st.rerun()
else:
    st.subheader("Step 1 · Your first results")
    show_analysis(st.session_state.first_result)

    if st.session_state.second_result is None:
        st.info("Now adjust your squat using the feedback above, then take another picture.")
        st.subheader("Step 2 · Second squat photo")
        second_photo = photo_input("second")
        if st.button("Analyze second photo & compare", type="primary", disabled=second_photo is None, use_container_width=True):
            if run_analysis(second_photo, "second_result"):
                st.rerun()
    else:
        st.divider()
        st.subheader("Step 2 · Your second results")
        show_analysis(st.session_state.second_result)

        st.divider()
        st.subheader("Step 3 · Compare your progress")
        before, after = st.session_state.first_result, st.session_state.second_result
        comparison = compare_squats(before, after)
        delta = comparison["total_change"]
        st.metric("Overall score change", f'{before["total"]} → {after["total"]}',
                  delta=f"{delta:+d} points", delta_color="normal")
        if not comparison["consistent_view"]:
            st.warning("The two photos show opposite facing directions. Retake from the same side for a more reliable comparison.")

        rows = [
            {
                "Metric": name,
                "Before": round(before["scores"][name], 1),
                "After": round(after["scores"][name], 1),
                "Change": f'{comparison["changes"][name]:+0.1f}',
            }
            for name in NAMES
        ]
        st.dataframe(rows, hide_index=True, use_container_width=True)

        st.write("**What improved:** " + (", ".join(comparison["improved"]) or "No clear score increases this time."))
        st.write("**What decreased:** " + (", ".join(comparison["declined"]) or "No substantial decreases."))
        st.write("**What stayed similar:** " + (", ".join(comparison["similar"]) or "None."))
        st.success(f'**Next focus: {comparison["next_focus"]}**\n\n{comparison["next_advice"]}')
        st.caption("Comparison reflects the current scoring model, not a clinical safety or injury assessment. Compare photos from the same angle and squat phase.")

    if st.button("🔄 Start over with two new photos", use_container_width=True):
        st.session_state.first_result = None
        st.session_state.second_result = None
        # New widget keys prevent old uploads from being reused, and avoid
        # altering widget state after the widgets were already instantiated.
        st.session_state.widget_round += 1
        st.rerun()

st.caption("Demo MVP · No account needed · Images are processed for this session; the app does not add permanent photo storage.")