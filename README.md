# Rhino Copilot // AIA25_Studio

A local AI assistant for Rhino 3D — powered by CLIP.  
Copilot classifies design outputs like *towers*, *lines*, and *components* based on a visual dataset.


This is the repo for AIA 25 Studio at IAAC for MaCAD.

Team:
- Andres Espinosa
- Aymeric Brouez
- César Diego Herbosa
- Joaquin Broquedis
- Marco Durand
  

## Features (WIP)

- Launchable from a Rhino toolbar button 🖱️
- Local web UI for interaction 🌐
- Fast CLIP-based image classification (using your own dataset)
- Offline-friendly — no cloud dependencies
- Modular architecture: Frontend ↔ Backend ↔ Rhino

---

## Folder Structure (WIP)
Rhino Copilot
|main.py
|readme.md
├─ UI
├─ UTILS
├─ KNOWLEDGE
├─ SERVER

## How to use
1. Open Rhino
2. Run this command:
_RunPythonScript ("C:/path/to/Copilot/launchCopilot.py")
3. A browser tab will open
4. The backend (main.py) will start and load the copilot. Let's play!



All rights reserved.