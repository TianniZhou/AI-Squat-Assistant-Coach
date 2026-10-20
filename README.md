# AI Squat Coach

### Making Movement Coaching More Accessible Through AI and Computer Vision

## Overview

AI Squat Coach is a mobile-friendly web application designed to help people improve their squat technique through computer vision and personalized movement feedback.

Many individuals want to exercise effectively but lack access to professional coaching. This project aims to bridge that gap by providing an accessible tool for movement analysis, progress tracking, and actionable feedback.

## How It Works

1. **Take Your First Photo:** Capture a side-view image of your squat.
2. **Receive Feedback:** The application analyzes your posture, calculates movement scores, and identifies areas for improvement.
3. **Adjust Your Technique:** Use the feedback to make corrections.
4. **Take Your Second Photo:** Capture another squat after making adjustments.
5. **Compare Your Progress:** See which movement metrics improved, declined, or remained similar.
6. **Get Your Next Coaching Focus:** Receive a specific recommendation for your next attempt.

## Movement Analysis

Using MediaPipe Pose Estimation and a custom Python scoring algorithm, the application evaluates six movement metrics:

- **Squat Depth (25%)**
- **Core / Balance Estimate (15%)**
- **Coordination (20%)**
- **Posture (15%)**
- **Hip Load Estimate (10%)**
- **Knee Track (15%)**

Each metric contributes to an overall score out of 100.

The application compares the scores from two photos to help users understand their progress.

## Technologies

- **Python 3.12** — Core programming language
- **MediaPipe 0.10.21** — Human pose estimation
- **OpenCV** — Image processing and pose visualization
- **NumPy** — Numerical operations
- **Streamlit** — Mobile-friendly web interface

## Getting Started

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Launch the application:

```bash
streamlit run app.py
```

For deployment on Streamlit Community Cloud, select **Python 3.12** in Advanced Settings.

## Project Structure

- `original_squat_coach.py` — Original squat evaluation algorithm
- `squat_engine.py` — Photo analysis and comparison functions
- `app.py` — Interactive web application
- `requirements.txt` — Python dependencies
- `packages.txt` — System dependencies

## Current Development Stage

This project is an early-stage prototype.

The current version supports two-photo comparison, rule-based movement evaluation, progress tracking, and coaching suggestions.

Future development may include video-based movement analysis, longitudinal progress tracking, and more adaptive coaching recommendations.

## Mission

**To make movement coaching more accessible, personalized, and actionable for people who want to improve but do not have access to professional coaching.**

*Disclaimer: This application is an experimental educational tool and is not a substitute for professional coaching, medical assessment, or individualized injury-prevention advice.*