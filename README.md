# Dofus Organizer - Outil Comte Harebourg ⏱️❄️

[Français](#français) | [English](#english) | [Español](#español)

---

## Français

### 📝 Description
**Outil Comte Harebourg** est un utilitaire d'assistance conçu pour le MMORPG Dofus. Il a pour but de simplifier le combat de boss du Comte Harebourg en calculant rapidement les décalages angulaires (mécanique de Pi / degrés du cadran) et en affichant les positions de ciblage correctes directement sur votre écran.

Ce projet est une amélioration de l'idée originale publiée sur [LuframeCode/outil_pi](https://github.com/LuframeCode/outil_pi), avec notamment la lecture automatique du pourcentage de santé par OCR.

### ✨ Fonctionnalités
* **Overlay Intégré :** S'affiche par-dessus la fenêtre de jeu en toute transparence (`overlay.py`).
* **Calculateur Automatique :** Gère la gymnastique mentale des rotations et des symétries pour vous (`math_dofus.py`).
* **Interface Graphique :** Une interface utilisateur simple pour configurer vos angles et positions (`gui.py`).
* **Lecture de santé par OCR :** Sélectionnez la zone du pourcentage de santé pour détecter automatiquement le palier du combat (nécessite Tesseract OCR).
* **Sauvegarde des Configurations :** Garde en mémoire le placement de votre interface et vos paramètres de grille (`config_manager.py`).

### 🚀 Comment ça fonctionne
1. Lancez l'application (via Python ou l'exécutable compilé).
2. L'overlay apparaîtra sur votre écran.
3. Dans l'onglet Combat, choisissez un palier manuellement ou sélectionnez la zone affichant le pourcentage de santé puis démarrez la lecture OCR. L'OCR essaie plusieurs modes de lecture et résolutions pour mieux reconnaître les petits chiffres.
4. L'outil calcule mathématiquement la case sur laquelle vous devez cliquer pour que votre sort atterrisse sur la bonne cible.

La lecture OCR nécessite Tesseract OCR installé et accessible dans le `PATH` (ou dans son dossier d'installation Windows standard).

---

## English

### 📝 Description
**Count Harebourg Tool** is an assistance utility designed for the MMORPG Dofus. Its purpose is to simplify the Count Harebourg boss fight by quickly calculating angular shifts (the dial's Pi / degrees mechanic) and displaying the correct targeting positions directly on your screen.

This project builds on the original idea published at [LuframeCode/outil_pi](https://github.com/LuframeCode/outil_pi), adding features including OCR-based automatic health percentage reading.

### ✨ Features
* **Integrated Overlay:** Displays seamlessly over the game window (`overlay.py`).
* **Automatic Calculator:** Handles the mental gymnastics of rotations and symmetries for you (`math_dofus.py`).
* **Graphical Interface:** A simple user interface to configure your angles and positions (`gui.py`).
* **OCR health reading:** Select the health percentage region to automatically detect the fight phase (requires Tesseract OCR).
* **Configuration Saving:** Remembers your interface placement and grid settings (`config_manager.py`).

### 🚀 How it works
1. Launch the application (via Python or the compiled executable).
2. The overlay will appear on your screen.
3. In the Combat tab, either choose a phase manually or select the region containing the health percentage and start OCR. OCR tries multiple recognition modes and resolutions to better read small digits.
4. The tool mathematically calculates the exact cell you need to click on so that your spell hits the intended target.

OCR reading requires Tesseract OCR to be installed and available on `PATH` (or in its standard Windows installation folder).

---

## Español

### 📝 Descripción
**Herramienta Conde Kontatrás (Comte Harebourg)** es una utilidad de asistencia diseñada para el MMORPG Dofus. Su objetivo es simplificar el combate contra el jefe Conde Kontatrás calculando rápidamente los desplazamientos angulares (la mecánica de Pi / grados de la esfera) y mostrando las posiciones de objetivo correctas directamente en tu pantalla.

Este proyecto mejora la idea original publicada en [LuframeCode/outil_pi](https://github.com/LuframeCode/outil_pi), añadiendo, entre otras funciones, la lectura automática del porcentaje de salud mediante OCR.

### ✨ Características
* **Overlay Integrado:** Se muestra de forma transparente sobre la ventana del juego (`overlay.py`).
* **Calculadora Automática:** Maneja la gimnasia mental de rotaciones y simetrías por ti (`math_dofus.py`).
* **Interfaz Gráfica:** Una interfaz de usuario sencilla para configurar tus ángulos y posiciones (`gui.py`).
* **Lectura de salud por OCR:** Selecciona la zona del porcentaje de salud para detectar automáticamente la fase del combate (requiere Tesseract OCR).
* **Guardado de Configuraciones:** Recuerda la ubicación de tu interfaz y los ajustes de la cuadrícula (`config_manager.py`).

### 🚀 Cómo funciona
1. Inicia la aplicación (a través de Python o del ejecutable compilado).
2. El overlay aparecerá en tu pantalla.
3. En la pestaña Combat, elige una fase manualmente o selecciona la zona del porcentaje de salud e inicia el OCR. Se prueban varios modos y resoluciones para reconocer mejor los números pequeños.
4. La herramienta calcula matemáticamente la casilla exacta en la que debes hacer clic para que tu hechizo alcance al objetivo deseado.

La lectura OCR requiere que Tesseract OCR esté instalado y disponible en `PATH` (o en su carpeta de instalación estándar de Windows).
