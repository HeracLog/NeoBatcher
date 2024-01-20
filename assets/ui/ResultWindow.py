from typing import Any, List, Optional, Union
import flet as ft
from flet_core.control import Control, OptionalNumber
from flet_core.ref import Ref
from flet_core.types import AnimationValue, CrossAxisAlignment, MainAxisAlignment, OffsetValue, ResponsiveNumber, RotateValue, ScaleValue, ScrollMode


class ResultWindow(ft.Column):
    def __init__(self,src,text,textSize,name,imWid,imHigh,on_click=None, controls: List[Control] | None = None, ref: Ref | None = None, key: str | None = None, width: OptionalNumber = None, height: OptionalNumber = None, left: OptionalNumber = None, top: OptionalNumber = None, right: OptionalNumber = None, bottom: OptionalNumber = None, expand: bool | int | None = None, col: ResponsiveNumber | None = None, opacity: OptionalNumber = None, rotate: RotateValue = None, scale: ScaleValue = None, offset: OffsetValue = None, aspect_ratio: OptionalNumber = None, animate_opacity: AnimationValue = None, animate_size: AnimationValue = None, animate_position: AnimationValue = None, animate_rotation: AnimationValue = None, animate_scale: AnimationValue = None, animate_offset: AnimationValue = None, on_animation_end=None, visible: bool | None = None, disabled: bool | None = None, data: Any = None, scroll: ScrollMode | None = None, auto_scroll: bool | None = None, on_scroll_interval: OptionalNumber = None, on_scroll: Any = None, alignment: MainAxisAlignment = MainAxisAlignment.NONE, horizontal_alignment: CrossAxisAlignment = CrossAxisAlignment.NONE, spacing: OptionalNumber = None, tight: bool | None = None, wrap: bool | None = None, run_spacing: OptionalNumber = None):
        super().__init__(controls, ref, key, width, height, left, top, right, bottom, expand, col, opacity, rotate, scale, offset, aspect_ratio, animate_opacity, animate_size, animate_position, animate_rotation, animate_scale, animate_offset, on_animation_end, visible, disabled, data, scroll, auto_scroll, on_scroll_interval, on_scroll, alignment, horizontal_alignment, spacing, tight, wrap, run_spacing)
        self.src = src
        self.name = name
        self.controls.append(
            ft.Image(
                src = self.src,
                width = imWid,
                height=imHigh,
                fit=ft.ImageFit.FILL,
                repeat=ft.ImageRepeat.NO_REPEAT,
                border_radius=ft.border_radius.all(10)
            )
        )
        if len(name) > 16:
            altName = name[:13]
            altName += '...'
            altName = altName.replace('\n','')
        else:
            altName = name
        self.controls.append(
            ft.TextButton(text=altName,on_click=on_click,tooltip=name)
        )