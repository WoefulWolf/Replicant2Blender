# Replicant2Blender

## CURRENTLY IN ALPHA:
* Armature/Bones imports aren't perfect (only seems to work on certain models at the moment).
* Not all DXGI texture formats have been identified yet, so if you find any broken textures or textures failing to extract, please let me know! 
* Please let me know of any other issues too (contact me here with an issue or on the [NieR:Modding Discord Server](https://discord.gg/7F76ZVv)).

## What does support right now?
* Character meshes.
* Weapon meshes.
* World/Map meshes.
* Honestly, any mesh pack I could find. (Let me know if you find one that doesn't work!)
* Automatic texture extraction, conversion & material node setup (make sure you have Noesis path set in Add-on Preferences).
* Multiple UV maps.
* Vertex groups.
* Basic armature (only for certain models).
* Materials.
* Extracting textures.

## Installation Instructions:
1. Install [Blender](https://www.blender.org/) (also available on Steam).
2. Download this repository as a ZIP (Green button labelled "Code" near the top-right, `Download ZIP`).
3. Launch Blender.
4. Go to `Edit > Preferences`.
5. Go to the `Add-ons` section and press `Install...` near the top-right.
6. Select the ZIP you downloaded in step 2 and press `Install Add-on`.
7. Check the tickbox next to `Import-Export: Replicant2Blender (NieR Replicant ver.1.2247... Mesh Pack Importer)`.
8. (Optional) If you want texture extraction, conversion & material node setup: open the preferences drop-down for the add-on and set your path to `Noesis.exe` (download if you don't have it yet).

## Usage:
* `File > Import > NieR Replicant Mesh Pack`
* Select a mesh PACK (usually prefixed with `msh_`) or PACK containing textures (if you wish to extract them).
* Have fun!

## How do I get extracted mesh packs?
https://github.com/yretenai/kaine/releases

## Extra Credits
* Kerilk for structure reversing help.
* yretenai for `kaine` tool and other help.
