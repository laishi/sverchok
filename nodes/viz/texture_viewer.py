# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from mathutils import Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, StringProperty, BoolProperty

import blf
import bgl

from sverchok.data_structure import updateNode, node_id
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import nodeview_bgl_viewer_draw_mk2 as nvBGL2

palette_dict = {
    "default": (
        (0.243299, 0.590403, 0.836084, 1.00),  # back_color
        (0.390805, 0.754022, 1.000000, 1.00),  # grid_color
        (1.000000, 0.330010, 0.107140, 1.00)   # line_color
    ),
    "scope": (
        (0.274677, 0.366253, 0.386430, 1.00),  # back_color
        (0.423268, 0.558340, 0.584078, 1.00),  # grid_color
        (0.304762, 1.000000, 0.062827, 1.00)   # line_color
    )

}


def simple_screen(x, y, args):
    #func = args[0]
    back_color, grid_color, line_color = args[0]
    data = args[1]

    texture = 1
    width = 64
    height = 64
    texname = 0

    def draw_texture(x=0, y=0, w=30, h=10, color=(0.0, 0.0, 0.0, 1.0),texname=texname):

        #bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)
        bgl.glEnable(bgl.GL_TEXTURE_2D)
        bgl.glTexEnvf(bgl.GL_TEXTURE_ENV, bgl.GL_TEXTURE_ENV_MODE, bgl.GL_REPLACE)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, texname)

        #bgl.glColor4f(*color)
        bgl.glBegin(bgl.GL_QUADS)

        for coord in [(x, y), (x, y+1), (x+1, y+1), (x+1, y)]:
            bgl.glTexCoord2f(*coord)
        for coord in [(x, y), (x+w, y), (w+x, y-h), (x, y-h)]:
            bgl.glVertex2f(*coord)

        bgl.glEnd()

        bgl.glDisable(bgl.GL_TEXTURE_2D)
        #bgl.glDeleteTextures( 1, Buffer )
        bgl.glFlush()

    def init_texture(width,height,texname,data):

        #bgl.glClearColor(0.0,0.0,0.0,0.0)
        bgl.glShadeModel(bgl.GL_FLAT)
        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glEnable(bgl.GL_TEXTURE_2D)
        Buffer = bgl.Buffer(bgl.GL_FLOAT, [width,height], data)
        bgl.glPixelStorei(bgl.GL_UNPACK_ALIGNMENT,1)

        bgl.glGenTextures(1,Buffer)
        #bgl.glEnable(bgl.GL_TEXTURE_2D)
        #glBindTexture(target, texture): texture (unsigned int) – Specifies the name of a texture.
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, texname)

        bgl.glActiveTexture(bgl.GL_TEXTURE0)

        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP)
        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP)
        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)

        #bgl.glEnable(bgl.GL_BLEND)
        #bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
        #bgl.glShadeModel(bgl.GL_SMOOTH)

        bgl.glTexImage2D(
               bgl.GL_TEXTURE_2D, 0, bgl.GL_LUMINANCE, width, height, 0,
               bgl.GL_LUMINANCE, bgl.GL_FLOAT, Buffer
           )

    init_texture(width,height,texname,data)

    draw_texture(x=x, y=y, w=64, h=64, color=back_color,texname=texname)

class SvTextureViewerNode(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvTextureViewerNode'
    bl_label = 'Texture viewer'

    n_id = StringProperty(default='')
    activate = BoolProperty(
        name='Show', description='Activate texture drawing',
        default=True,
        update=updateNode)

    in_float = FloatProperty(
        min=0.0, max=1.0, default=0.0, name='Float Input',
        description='input for texture', update=updateNode
    )

    theme_mode_options = [(m, m, '', idx) for idx, m in enumerate(["default", "scope"])]
    selected_theme_mode = EnumProperty(
        items=theme_mode_options, default="default", update=updateNode
    )

    def draw_buttons(self, context, l):
        c = l.column()
        c.prop(self, 'activate')

    def draw_buttons_ext(self, context, l):
        l.prop(self, "selected_theme_mode")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Float").prop_name = 'in_float'

    def process(self):
        p = self.inputs['Float'].sv_get()
        n_id = node_id(self)

        # end early
        nvBGL2.callback_disable(n_id)

        _data = p[0]
        #print(_data)
        if self.activate:

            palette = palette_dict.get(self.selected_theme_mode)[:]
            x, y = [int(j) for j in (self.location + Vector((self.width + 20, 0)))[:]]

            draw_data = {
                'tree_name': self.id_data.name[:],
                'mode': 'custom_function',
                'custom_function': simple_screen,
                'loc': (x, y),
                'args': (palette, _data)
            }
            nvBGL2.callback_enable(n_id, draw_data)



    # reset n_id on copy
    def copy(self, node):
        self.n_id = ''


def register():
    bpy.utils.register_class(SvTextureViewerNode)


def unregister():
    bpy.utils.unregister_class(SvTextureViewerNode)
