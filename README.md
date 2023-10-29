# Greeble Tool

A simple Blender tool providing a non-destructive workflow for procedurally generating detailing/greebles on an object. The tool was developed to speed up the time-consuming portion of modeling sci-fi objects. Detailing can be exported as geometry, or baked to textures and exported within the tool.

![GreebleScreenshot](https://github.com/DanielAskerov/Greeble-Tool/assets/140186597/7d9ac37a-9f1f-4423-8562-61ef2a90170e)

This is an ongoing project; it began as a means of creating quick prototypes of space ships, but my aim is to make it more substantial and universally useful in the future. Some of the things I'm currently exploring include displacement map generation, an interface to create a pool of unique greeble objects, and a number of more useful parameters. 

While the tool works efficiently at reasonable levels of geometry, it can get quite slow with more complex objects. I have made optimizations where I can, but some parts require refactoring.


## Installation

1. Download Greeble Tool from master as ZIP.
2. In Blender, go to **Edit** > **Preferences** > **Add-ons**.
3. Hit **Install** at top of window and select the ZIP file.
4. Enable **Generic: Greeble Tool** from Add-on list.
5. Select any object/face(s), hit **N** and Greeble Tool interface can be found to the right.
