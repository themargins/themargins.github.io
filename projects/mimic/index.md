---
title: MIMIC
description: A robot arm and hand that copy my own movements, watched through a single depth camera. No markers, no gloves, nothing to wear.
status: ongoing
started: 2026
updated: October 15, 2026
draft: true
---

::: todo
**Hero video.** 10–20 s split-screen loop: my arm and hand on one side, the UR3e and Mia Hand mirroring them on the other. Muted, so it can autoplay. Drop the clip in this folder and replace this box with `![What it shows](hero.mov){.loop}`. Fallback: a photo of me mid-gesture with the robot copying in the background.
:::

**MIMIC** stands for *Motion Imitation via Markerless Image Capture*. I move my arm and hand in front of a depth camera, and a robot arm with a dexterous hand does the same thing.

- **What:** live teleoperation of a Universal Robots UR3e arm and a Prensilia Mia Hand, driven by my own arm and hand movements.
- **How:** an Intel RealSense D435 sees me in colour and depth. Software finds my arm and hand keypoints, lifts them into 3D, and retargets them onto the robot.
- **Why:** markerless teleoperation is a cheap way to collect human demonstrations for robot learning, and building it end to end teaches perception, kinematics and real robot control all at once.

## Why markerless

Robots learn a lot from watching people, but showing them usually means motion-capture suits, data gloves, or a second robot to puppet. Those are expensive, fiddly, and they change how you move. A single depth camera is cheap and asks nothing of the person in front of it: you just move. If that's good enough to drive a real arm and hand, it's good enough to record demonstrations at scale.

I'm a PhD student interested in embodied robotics, and I wanted to get my hands dirty connecting perception to a real machine, not just a simulator. Underneath it is a conviction I keep coming back to: we should build intelligent robots that are amazing and charming, and that actually help serve the world. A robot that waves back when you wave at it is a small, good start.

[Context to confirm: built as a side project during my visiting PhD exchange at Chalmers University of Technology in Gothenburg; home institution the University of Chicago.]{.tbd}

## The system

- **Arm:** Universal Robots UR3e, a 6-DoF collaborative arm
- **Hand:** Prensilia Mia Hand as the end effector, with three motors: thumb, index, and the middle, ring and little fingers together
- **Eyes:** Intel RealSense D435 depth camera (RGB + depth)
- **Brain:** a MacBook running the pipeline

The data flows one way: **D435 → pose estimation → 3D lifting → retargeting → UR3e and Mia Hand.**

::: todo
**Setup photo.** The whole rig: camera on its tripod, UR3e, Mia Hand, laptop. Labelled callouts help. A block diagram of the pipeline could sit next to it.
:::

## How it works

### 1. Capture

The D435 streams aligned colour and depth frames, so every pixel I see in the image also has a distance.

::: todo
**Raw frame next to depth.** One RGB frame beside the same frame as a depth colormap.
:::

### 2. Pose estimation

A pose model finds keypoints on my arm and hand in each colour frame. [TBD: which model or library, e.g. MediaPipe.]{.tbd}

::: todo
**Keypoint overlay.** A short clip of the skeleton tracking my arm and hand.
:::

### 3. Lifting to 3D

Each 2D keypoint is paired with the depth at that pixel and projected into 3D with the camera's intrinsics, giving a 3D skeleton of my arm and hand.

::: todo
**3D view.** The point cloud or 3D keypoints in a viewer (RViz, Open3D or similar).
:::

### 4. Retargeting

My arm isn't a UR3e and my hand isn't a Mia Hand, so the motion has to be translated. The arm pose becomes joint or Cartesian targets for the UR3e. [TBD: IK approach.]{.tbd} The finger pose is reduced to the Mia Hand's three motors. [TBD: how finger curl maps to each motor.]{.tbd}

::: todo
**Four hand poses.** Open, fist, pinch and point, each next to the Mia Hand's version.
:::

### 5. Control

Commands go to the UR3e over [TBD: RTDE / ROS 2 / other]{.tbd} and to the Mia Hand over [TBD: interface]{.tbd}.

### 6. Safety

[TBD: workspace limits, speed limits, and the filtering or smoothing that keeps the arm from following every jitter.]{.tbd}

## Results

[TBD: latency, control rate, tracking accuracy, and the tasks it can do.]{.tbd}

::: todo
**Task demo.** Picking something up and placing it, waving, or handing an object to a person. A plot of commanded vs. actual joint angles, or a latency histogram, would back it up. A slowed-down clip shows the delay between me and the robot honestly.
:::

## What was hard

[TBD. Likely suspects: depth noise, fingers hiding each other from the camera, the mismatch between a human arm and a robot's, and jitter.]{.tbd}

::: todo
**A failure clip.** Tracking dropping out when fingers are hidden, or jitter before and after smoothing, side by side. Failures make the page more honest and more interesting.
:::

## What's next

[To confirm: recording demonstrations for imitation learning, a two-armed setup, force feedback.]{.tbd}

::: todo
**Something charming.** The robot waving hello, a high-five, a thumbs-up, or a round of rock-paper-scissors.
:::

## Stack and links

UR3e, Mia Hand, RealSense D435, MacBook. [TBD: languages and libraries.]{.tbd}

Code: [TBD: public repo link, or "available on request".]{.tbd}

## Updates

**Oct 15, 2026.** Started this page.
