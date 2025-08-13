# Blender Add-on: Triangle Splatting Object File Format (.off) Importer

This Blender add-on allows you to import 3D geometry, splats, or radiance field data generated using the [**Triangle Splatting for Real-Time Radiance Field Rendering**](https://github.com/trianglesplatting/triangle-splatting) method. Perhaps it can import other OFF files as well.

It is designed for artists, researchers, and developers who want to bring advanced neural rendering outputs directly into Blender for visualization, animation, or further processing.
It works in Blender 4.4, perhaps in later or earlier versions too, but this has not been tested.


## Features
- Import triangle splatting output files into Blender, streaming large files.
- Preserve material and shading information where possible.
- Compatible with Blender's **Cycles** and **Eevee** renderers.
- Simple and streamlined UI in the **Import** menu.


## Installation
1. Download this repository as a `.zip` file.
2. Open Blender and go to: Edit → Preferences → Add-ons → Install...
3. Select the `.zip` file and click **Install Add-on**.
4. Enable the add-on by checking the box next to its name.


## Usage
1. Go to: *File* → *Import* → *Triangle Splatting Object File Format (.off)*
2. Select your exported file from the Triangle Splatting pipeline.
3. Adjust import settings as needed.
4. Click **Import** to load the scene into Blender.


## License
This add-on is released under the MIT License.
Please note that the Triangle Splatting method itself may have its own license and terms — check the original repository or paper for details.


## Acknowledgements
This add-on builds upon the work presented in:

**Held, Jan, Vandeghen, Renaud, Deliège, Adrien, Hamdi, Abdullah, Cioppa, Anthony, Giancola, Silvio, Vedaldi, Andrea, Ghanem, Bernard, Tagliasacchi, Andrea, & Van Droogenbroeck, Marc.**
*Triangle Splatting for Real-Time Radiance Field Rendering.* arXiv, 2025.
If you use this add-on in research or publications, please cite the *original* Triangle Splatting paper:

```bibtex
@article{Held2025Triangle,
title   = {Triangle Splatting for Real-Time Radiance Field Rendering},
author  = {Held, Jan and Vandeghen, Renaud and Deliege, Adrien and Hamdi, Abdullah and Cioppa, Anthony and Giancola, Silvio and Vedaldi, Andrea and Ghanem, Bernard and Tagliasacchi, Andrea and Van Droogenbroeck, Marc},
journal = {arXiv},
year    = {2025},
}
```
