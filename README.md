<div align="center">

# OptTac: <ins>low-cost</ins> <ins>triaxial</ins> <ins>distributed</ins> deform-force-torque tactile sensing kit for generalizeable robotic manipulation

[![Project](https://img.shields.io/badge/Page_and_Guide-GitHub-green)](https://wangzivector.github.io/OptTacPage/)
[![Project](https://img.shields.io/badge/Hardware-CAD-purple)](./manicapture/hardware/)
[![License](https://img.shields.io/badge/Software-ROS-red)](./manicapture/)
[![Pretrain Model](https://img.shields.io/badge/Pretrain_model-Numpy-yellow)](./manicapture/misc)
[![License](https://img.shields.io/badge/License-PolyForm-blue)](./LICENSE)


We introduce OptTac, optoelectronic sensing kit enabled triaxial deformation-force-torque generalization for contact-aware manipulation.
The hardware manufacture and software package are open-sourced for tactile reproduction towards relevant manipulation research. [[Project page]](https://wangzivector.github.io/opttacpage)

<img src="assets/media/system@3x-80.jpg" width="95%" title="opttac_system">

<ins>**Features of OptTac**</ins>

| Key characteristics | Functional description | Further reference |
|---------|-------------|-------------|
| ✨ **Open-source** | Hardware fabrication and software solution| Refer to [Maintenance schedule](#project-release-schedule) |
| 💰 **Low-cost** | Less 10 USD for each OptPad | Refer to [BOM details](#device-manufacture) |
| 🛠 **Reproducible** | Simplified steps with detailed guides | Refer to [Device manufacture](#device-manufacture)  |
| 📐 **Triaxial** | Three-dimensional *deformation* and forces| Refer to [Project page](https://wangzivector.github.io/OptTacPage/)  |
| 🕸️ **Distributed**| Locally reconstructed load distribution | Refer to [Project page](https://wangzivector.github.io/OptTacPage/)  |
| 💪 **Deform, force, torque** | Both positional and wrench modalities | Refer to [Project page](https://wangzivector.github.io/OptTacPage/)  |

</div>

## Maintenance schedule
<mark>This work is gradually available in scheduled steps, under continuous preparation:</mark>

> **The full hardware scheme, including PCB schemetic, BOM, FPCB Assembly, and fabrication guides, <br>will be publicly available after careful preparation and patent organization within Nov. 2026.** 

✅ Establishment of project page [2026-10-06]
<br>⬜ Release hardware solution of OptTac [Est. 2026-11]
<br>⬜ Fabrication guidance for OptTac [Est. 2026-10]
<br>✅ Exoskeleton hand sensing kit: CAD and ROS package [2026-09-29]
<br>✅ ROS package for tactile computation and visualization [2026-09-29]
<br>⬜ Software setup, usage, and examples [Est. 2026-10-07]
<br>✅ Pre-trained checkpoints for wrench models [2026-09-29]
<br>⬜ LeapHand extension using OptTac [Est. 2026-10]
<br>⬜ LeapHand retargeting using OptTac [Est. 2026-10]

## Device manufacture
### OptPad FPCB manufacture
- EasyEDA project link for PCB schmetic design.
- BOM files
- Assembly service reference

### Elastomer casting
- 3D-printed CAD files of casting molds: [Project pages](page1)
- Manufacture video guidance: [Project pages](page2)

## Software environment
### Step 1: conda env establishment
```
# Create conda environment
conda create -n manicapture python=3.10
conda activate manicapture
```



## License

**This project is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE).**

Researchers and practitioners are welcome to implement this project by complying the noncommercial license.
You may use, copy, and modify this code for noncommercial purposes, such as academic research, personal study, or experimentation.


## Citation
If you want to cite this work, please find reference below:
```
@article{wang2026opttac,
  title={OptTac: Reproducible optoelectronic tactile sensing of distributed triaxial deformation, force, and torque for robotic manipulation},
  author={Wang, Xianli and Wu, zehao and Xu, Qingsong},
  journal={Manuscript},
  year={2026}
}
```