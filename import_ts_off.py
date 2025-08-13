# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Lennart van den Dool
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

import bpy
import bmesh
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator

# tweak this to control emission brightness for additive glow
EMISSION_MULTIPLIER = 1.5

def _is_color_triplet(vals):
    try:
        for v in vals:
            if v < -1e-6 or v > 255 + 1e-6:
                return False
        return True
    except Exception:
        return False

def _is_normal_triplet(vals):
    try:
        for v in vals:
            if abs(v) > 1.01:
                return False
        return True
    except Exception:
        return False

class ImportTSOFFStreamingAutoMatV2(Operator, ImportHelper):
    bl_idname = "import_scene.ts_off_streaming_auto_mat_v2"
    bl_label = "Import Triangle Splatting OFF"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".off"
    filter_glob: StringProperty(default="*.off", options={'HIDDEN'})

    def execute(self, context):
        path = self.filepath
        try:
            f = open(path, 'r', encoding='utf-8', errors='ignore')
        except Exception as e:
            self.report({'ERROR'}, f"Cannot open file: {e}")
            return {'CANCELLED'}

        def lines_gen():
            for raw in f:
                s = raw.strip()
                if not s:
                    continue
                if s.startswith('#'):
                    continue
                yield s
            return

        gen = lines_gen()

        try:
            header = next(gen).upper()
        except StopIteration:
            f.close()
            self.report({'ERROR'}, "Empty file.")
            return {'CANCELLED'}

        # read counts
        try:
            counts_line = next(gen)
            parts = counts_line.split()
            v_count = int(parts[0])
            f_count = int(parts[1])
        except Exception as e:
            f.close()
            self.report({'ERROR'}, f"Failed to read counts: {e}")
            return {'CANCELLED'}

        bm = bmesh.new()
        bm_verts = []
        vertex_colors = []
        vertex_normals = []

        loop_col_layer = None

        # stream vertices
        for vi in range(v_count):
            try:
                ln = next(gen)
            except StopIteration:
                f.close()
                bm.free()
                self.report({'ERROR'}, f"Unexpected EOF while reading vertex {vi}")
                return {'CANCELLED'}
            tokens = ln.split()
            nums = list(map(float, tokens))
            if len(nums) >= 6:
                trailing = nums[3:6]
                if _is_normal_triplet(trailing):
                    x, y, z = nums[0:3]
                    nx, ny, nz = trailing
                    v = bm.verts.new((x, y, z))
                    bm_verts.append(v)
                    vertex_normals.append((nx, ny, nz))
                    vertex_colors.append(None)
                elif _is_color_triplet(trailing):
                    x, y, z = nums[0:3]
                    r, g, b = trailing
                    v = bm.verts.new((x, y, z))
                    bm_verts.append(v)
                    vertex_colors.append((r/255.0, g/255.0, b/255.0, 1.0))
                    vertex_normals.append(None)
                else:
                    x, y, z = nums[0:3]
                    v = bm.verts.new((x, y, z))
                    bm_verts.append(v)
                    vertex_colors.append(None)
                    vertex_normals.append(None)
            elif len(nums) >= 3:
                x, y, z = nums[0:3]
                v = bm.verts.new((x, y, z))
                bm_verts.append(v)
                vertex_colors.append(None)
                vertex_normals.append(None)
            else:
                f.close()
                bm.free()
                self.report({'ERROR'}, f"Invalid vertex line: '{ln}'")
                return {'CANCELLED'}

        bm.verts.ensure_lookup_table()

        if any(vc is not None for vc in vertex_colors):
            loop_col_layer = bm.loops.layers.color.new("Col")

        # stream faces, assign loop colors on the fly
        face_start_idx = 0
        for fi in range(f_count):
            try:
                ln = next(gen)
            except StopIteration:
                f.close()
                bm.free()
                self.report({'ERROR'}, f"Unexpected EOF while reading face {fi}")
                return {'CANCELLED'}

            parts = ln.split()
            if len(parts) < 1:
                f.close()
                bm.free()
                self.report({'ERROR'}, f"Invalid face line: '{ln}'")
                return {'CANCELLED'}

            cnt = int(parts[0])
            if len(parts) < 1 + cnt:
                f.close()
                bm.free()
                self.report({'ERROR'}, f"Truncated face line: '{ln}'")
                return {'CANCELLED'}

            idx_tokens = parts[1:1 + cnt]
            idxs = [int(t) for t in idx_tokens]

            try:
                verts_for_face = [bm_verts[i] for i in idxs]
            except IndexError:
                f.close()
                bm.free()
                self.report({'ERROR'}, f"Face references invalid vertex index on line: '{ln}'")
                return {'CANCELLED'}

            # create face
            try:
                face = bm.faces.new(verts_for_face)
            except ValueError:
                # face exists already -> try to find and reuse
                face = None
                for ftest in bm.faces:
                    if len(ftest.verts) == len(verts_for_face) and all(ftest.verts[i].co == verts_for_face[i].co for i in range(len(verts_for_face))):
                        face = ftest
                        break
                if face is None:
                    continue

            trailing = parts[1 + cnt:]
            face_color = None
            if len(trailing) in (3, 4):
                vals = list(map(float, trailing))
                r, g, b = vals[0:3]
                a = vals[3] if len(vals) == 4 else 255.0
                face_color = (r/255.0, g/255.0, b/255.0, a/255.0)

            if face_color is not None and loop_col_layer is None:
                loop_col_layer = bm.loops.layers.color.new("Col")

            if loop_col_layer is not None:
                if face_color is not None:
                    for loop in face.loops:
                        try:
                            loop[loop_col_layer] = (face_color[0], face_color[1], face_color[2], face_color[3])
                        except Exception:
                            loop[loop_col_layer] = (face_color[0], face_color[1], face_color[2])
                else:
                    for loop in face.loops:
                        vidx = loop.vert.index
                        vcol = vertex_colors[vidx]
                        if vcol:
                            try:
                                loop[loop_col_layer] = (vcol[0], vcol[1], vcol[2], vcol[3])
                            except Exception:
                                loop[loop_col_layer] = (vcol[0], vcol[1], vcol[2])

            face_start_idx += 1

        # close file
        f.close()

        # convert bmesh to mesh
        mesh = bpy.data.meshes.new("Imported_TS_OFF")
        bm.to_mesh(mesh)
        bm.free()

        # apply custom normals if provided
        if any(vn is not None for vn in vertex_normals):
            try:
                # mesh.vertices corresponds in order to vertices we created
                normals_out = []
                for vn in vertex_normals:
                    if vn is None:
                        normals_out.append((0.0, 0.0, 0.0))
                    else:
                        normals_out.append(vn)
                mesh.normals_split_custom_set_from_vertices(normals_out)
                mesh.use_auto_smooth = True
            except Exception:
                pass

        # create object and link
        obj = bpy.data.objects.new("Imported_TS_OFF", mesh)
        context.collection.objects.link(obj)

        # ---------- material creation and hookup ----------
        def create_and_assign_ts_material(obj, mesh, loop_layer_name="Col", emission_multiplier=EMISSION_MULTIPLIER):
            # Determine which attribute exists
            attr_name = None
            use_loop_attr = False

            if len(mesh.vertex_colors) > 0:
                # vertex_colors are loop-domain layers; prefer the last added
                attr_name = list(mesh.vertex_colors.keys())[-1]
                use_loop_attr = True
            elif hasattr(mesh, "color_attributes") and len(mesh.color_attributes) > 0:
                attr_name = list(mesh.color_attributes.keys())[-1]
                use_loop_attr = False
            else:
                return None

            # material
            mat = bpy.data.materials.new("TS_Additive_Mat")
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # clear nodes
            for n in list(nodes):
                nodes.remove(n)

            # nodes
            output = nodes.new(type='ShaderNodeOutputMaterial'); output.location = (800, 0)
            principled = nodes.new(type='ShaderNodeBsdfPrincipled'); principled.location = (200, 0)
            attr = nodes.new(type='ShaderNodeAttribute'); attr.location = (-400, 0)
            attr.attribute_name = attr_name

            # matte defaults to avoid metallic sheen
            try:
                principled.inputs['Metallic'].default_value = 0.0
                principled.inputs['Roughness'].default_value = 0.7
                principled.inputs['Specular'].default_value = 0.2
            except Exception:
                pass

            # connect color -> base color
            links.new(attr.outputs['Color'], principled.inputs['Base Color'])

            # attempt to connect alpha -> Principled alpha
            alpha_connected = False
            try:
                links.new(attr.outputs['Alpha'], principled.inputs['Alpha'])
                alpha_connected = True
                mat.blend_method = 'BLEND'
                # avoid heavy shadows from translucent splats
                try:
                    mat.shadow_method = 'NONE'
                except Exception:
                    pass
            except Exception:
                mat.blend_method = 'OPAQUE'
                try:
                    mat.shadow_method = 'NONE'
                except Exception:
                    pass

            # Emission node using attribute color
            emission = nodes.new(type='ShaderNodeEmission'); emission.location = (200, -250)
            links.new(attr.outputs['Color'], emission.inputs['Color'])

            # emission strength: prefer Fac output (if present), else use RGB->BW * multiplier
            used_fac = False
            # Attribute node outputs might be 'Fac' - check names
            try:
                fac_socket = attr.outputs.get('Fac')
                if fac_socket is not None:
                    # connect Fac directly to emission strength
                    links.new(attr.outputs['Fac'], emission.inputs['Strength'])
                    used_fac = True
            except Exception:
                used_fac = False

            if not used_fac:
                # create RGB->BW -> multiply chain
                rgb2bw = nodes.new(type='ShaderNodeRGBToBW'); rgb2bw.location = (-200, -250)
                mul = nodes.new(type='ShaderNodeMath'); mul.location = (0, -250)
                mul.operation = 'MULTIPLY'
                mul.inputs[1].default_value = float(emission_multiplier)
                links.new(attr.outputs['Color'], rgb2bw.inputs['Color'])
                links.new(rgb2bw.outputs['Val'], mul.inputs[0])
                links.new(mul.outputs['Value'], emission.inputs['Strength'])

            # Combine Principled + Emission additively
            add_shader = nodes.new(type='ShaderNodeAddShader'); add_shader.location = (500, 0)
            links.new(principled.outputs['BSDF'], add_shader.inputs[0])
            links.new(emission.outputs['Emission'], add_shader.inputs[1])
            links.new(add_shader.outputs[0], output.inputs['Surface'])

            # assign material
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

            # try to set some object/material-level visibility tweaks
            try:
                obj.active_material = mat
            except Exception:
                pass
            try:
                # try to mute shadow casting in cycles/eevee where possible
                obj.cycles_visibility.shadow = False
            except Exception:
                pass
            try:
                obj.hide_render = False
            except Exception:
                pass

            return mat

        # create material if color info exists
        created_mat = None
        if len(mesh.vertex_colors) > 0 or (hasattr(mesh, "color_attributes") and len(mesh.color_attributes) > 0):
            created_mat = create_and_assign_ts_material(obj, mesh)

        # switch viewport to material preview
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
                        break

        # select object and make active
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # report success and return
        self.report({'INFO'}, "Imported object; material applied." if created_mat else "Imported object (no color attribute found).")
        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportTSOFFStreamingAutoMatV2.bl_idname, text="Triangle Splatting Object File Format (.off)")

def register():
    bpy.utils.register_class(ImportTSOFFStreamingAutoMatV2)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportTSOFFStreamingAutoMatV2)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
