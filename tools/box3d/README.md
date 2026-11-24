# Kit box 3D model

Builds the Praaniva kit box (base and lid as separate objects) in Blender from code, and exports it as GLB.

- `lidart.py` draws the lid artwork. To use the real print file, save it as a square image named `tex/lidtop_col.png` and skip this script. You can also set gold foil areas in `tex/lidtop_mr.png` (blue = metal, green = roughness).
- `textures.py` makes the paper, lining and board textures.
- `build_box.py` builds the model, exports `praaniva-kit-box.glb` (both pieces), `-base.glb` and `-lid.glb`, and renders preview stills.

Sizes are in metres at the top of `build_box.py` (box 26 x 26 x 8.5 cm, lid 3.4 cm deep). Change them to the real box.

Run, with Blender's Python module (`pip install bpy`) and the brand fonts from npm (`@fontsource/cormorant-garamond`, `@fontsource/tiro-devanagari-hindi`, `@fontsource/hind`):

    python textures.py tex <fonts dir>
    python lidart.py tex <fonts dir>
    python build_box.py -- out            # add --no-render to only export
