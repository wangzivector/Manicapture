<div align="center">

# OptTac: <ins>low-cost</ins> <ins>triaxial</ins> <ins>distributed</ins> deform-force-torque tactile sensing kit for generalizeable robotic manipulation

[![](https://img.shields.io/badge/Guide-Page-green)](https://wangzivector.github.io/OptTacPage/)
[![](https://img.shields.io/badge/Hardware-CAD-purple)](#device-manufacture)
[![](https://img.shields.io/badge/Software-ROS-red)](./manicapture/)
[![](https://img.shields.io/badge/Pretrain_model-Numpy-yellow)](./manicapture/misc)
[![](https://img.shields.io/badge/License-PolyForm-blue)](./LICENSE)


We introduce [OptTac](https://wangzivector.github.io/OptTacPage/), optoelectronic tactile sensing kit enabled triaxial deformation-force-torque generalization for contact-rich robotic hardware augmentation.
The device manufacture and software package are open-sourced for tactile reproduction towards relevant embodied manipulation research. 

<img src="assets/media/system@3x-80.jpg" width="95%" title="opttac_system">

<br>
<!-- <ins>**OptTac System**</ins> -->

| Key characteristics | Functional description | Further reference |
|---------|-------------|-------------|
| ✨ **Open-source** | Hardware fabrication and software solution| Refer to [Maintenance schedule](#project-release-schedule) |
| 💰 **Low-cost** | Less 10 USD for each OptPad | Refer to [BOM details](#device-manufacture) |
| 🛠 **Reproducible** | Simplified steps with detailed guides | Refer to [Device manufacture](#device-manufacture)  |
| 📐 **Triaxial** | Three-dimensional *deformation* and forces| Refer to [Project page](https://wangzivector.github.io/OptTacPage/)  |
| 🕸️ **Distributed**| Locally reconstructed load distribution | Refer to [Project page](https://wangzivector.github.io/OptTacPage/)  |
| 💪 **Deform, force, torque** | Both positional and wrench modalities | Refer to [Project page](https://wangzivector.github.io/OptTacPage/)  |

</div>

## 0. Maintenance schedule
<mark>This work is gradually available in scheduled steps, under continuous preparation:</mark>

> **The full hardware scheme, including PCB schemetic, BOM, FPCB Assembly, and fabrication guides, <br>will be publicly available after careful preparation and patent organization within Nov. 2026.** 

✅ Establishment of project page [2026-10-06]
<br>⬜ Release hardware solution of OptTac [Est. 2026-11]
<br>⬜ Fabrication guidance for OptTac [Est. 2026-10]
<br>✅ Exoskeleton hand sensing kit: CAD and ROS package [2026-09-29]
<br>✅ ROS package for tactile computation and visualization [2026-09-29]
<br>✅ Software setup, usage, and examples [2026-10-07]
<br>✅ Pre-trained checkpoints for wrench models [2026-09-29]
<br>⬜ LeapHand extension and retargeting with OptTac [Est. 2026-10]

## 1. Manufacture
### Step 1: OptPad FPCB manufacture
- EasyEDA project link for FPCB schmetic design
- BOM files
- FPCB assembly service

### Step 2: Elastomer casting
- CAD files of 3D-printed casting molds: [Project pages](page1)
- Videos of manufacture guidance

### Step 3: Modular assembly
- Connecting board manufacture
- Controller connection

### Step 4 (Extended): Hand exoskeleton
- Fabrication of mechanical links
- Preparation of angular encoders
- Joint-controller assembly

### Step 5 (Extended): Visual 6D pose tracking
- Assembly of Apriltags marker
- Establishment of visual camera 

## 2. Software
### A: OptTac sensing pad
<!-- ```
# Create conda environment
conda create -n manicapture python=3.10
conda activate manicapture
``` -->
```
# Activate USB Port connection
# Launch tactile system module

```

### B: Exoskeleton articulation
```
# Launch joint encoding module

```
### C: Visual pose tracking
```
# Install apriltag_ros Package

```

## -2. License

**This project is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE).**

Researchers and practitioners are welcome to implement this project by complying the noncommercial license.
You may use, copy, and modify this code for noncommercial purposes, such as academic research, personal study, or experimentation.


## -1. Citation
If you want to cite this work, please find reference below:
```
@article{wang2026opttac,
  title={OptTac: Reproducible optoelectronic tactile sensing of distributed triaxial deformation, force, and torque for robotic manipulation},
  author={Wang, Xianli and Wu, zehao and Xu, Qingsong},
  journal={Manuscript},
  year={2026}
}
```

## -0. Acknowledgement
We welcome your valuable suggestions on enhancing this project.
