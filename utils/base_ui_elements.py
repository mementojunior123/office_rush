import pygame
from utils.ui_sprite import UiSprite

class BaseUiElements:
    green_button_surf = pygame.image.load("assets/graphics/button_templates/green_button.png").convert_alpha()
    blue_button_surf = pygame.image.load("assets/graphics/button_templates/blue_button.png").convert_alpha()
    red_button_surf = pygame.image.load("assets/graphics/button_templates/red_button.png").convert_alpha()

    left_button_surf = pygame.image.load("assets/graphics/button_templates/left_button.png").convert_alpha()
    right_button_surf = pygame.image.load("assets/graphics/button_templates/right_button.png").convert_alpha()

    hover_icon_surf = pygame.image.load("assets/graphics/button_templates/hover_icon.png").convert_alpha()
    hover_icon_clean_surf = pygame.image.load("assets/graphics/button_templates/hover_icon_clean.png").convert_alpha()
    hover_icon_blue_surf = pygame.image.load("assets/graphics/button_templates/hover_icon_blue.png").convert_alpha()
    home_icon_surf = pygame.image.load("assets/graphics/button_templates/home_icon.png").convert_alpha()
    
    back_icon_surf = pygame.image.load("assets/graphics/button_templates/back_icon_green_colorkey.png").convert()
    back_icon_surf.set_colorkey((0, 255, 0))
    left_arrow_surf = pygame.image.load("assets/graphics/button_templates/left_arrow.png").convert_alpha()
    right_arrow_surf = pygame.image.load("assets/graphics/button_templates/right_arrow.png").convert_alpha()

    font_40 = pygame.font.Font("assets/fonts/Pixeltype.ttf", 40)

    tag_event = pygame.event.custom_type()
    

    @classmethod
    def new_button(cls, color, text, tag, alignment, pos, scale : float|tuple = 1, attributes = None, text_settings : tuple = None, 
                   name : str|None = None):
        if text_settings is None: text_settings = (cls.font_40, "Black", False)
        font : pygame.Font
        text_color : pygame.Color|str
        AA_enabled : bool
        font, text_color, AA_enabled = text_settings

        colorkeys = {
            "Green": cls.green_button_surf,
            "Blue": cls.blue_button_surf,
            "Red": cls.red_button_surf,
        }
        text_scale : float
        surf_scale : float
        if type(scale) == float or type(scale) == int:
            text_scale = surf_scale = scale
        else:
            surf_scale, text_scale = scale

        surface = colorkeys[color]
        surface = pygame.transform.scale_by(surface, surf_scale)
        
        surface_rect = surface.get_bounding_rect()
        
        text_surface = font.render(text, AA_enabled, text_color)
        text_surface = pygame.transform.scale_by(text_surface, text_scale)
        text_surface_rect = text_surface.get_bounding_rect()
        text_surface_rect.center = (surface_rect.centerx, surface_rect.centery) 
        
        surface_rect.__setattr__(alignment, pos)
        
        surface.blit(text_surface, text_surface_rect)
        
        return UiSprite(surface, surface_rect, tag, attributes = attributes, name=name)

    @classmethod
    def new_textless_button(cls, type, tag, alignment, pos, scale : float|tuple = 1, attributes = None, name : str|None = None):
        button_types = {
            "Left" : cls.left_button_surf,
            "Right" : cls.right_button_surf,
            "Pointer": cls.hover_icon_surf,
            "CleanPointer": cls.hover_icon_clean_surf,
            "BluePointer": cls.hover_icon_blue_surf,
            "Home" : cls.home_icon_surf,
            "LeftArrow" : cls.left_arrow_surf,
            "RightArrow" : cls.right_arrow_surf,
            "BackIcon" : cls.back_icon_surf

        }

        surface = pygame.transform.scale_by(button_types[type], scale)
        surface_rect = surface.get_bounding_rect()
        surface_rect.__setattr__(alignment, pos)
        
        
        
        return UiSprite(surface, surface_rect, tag, attributes = attributes, name=name)


    @classmethod
    def new_text_sprite(cls, text : str, settings : tuple, tag : int, alignment : str, pos : tuple, 
                        attributes = None, newline_settings = None, keep_og_surf : bool = False, forced_og_surf : pygame.Surface|None= None,
                        name : str|None = None, scale : float|tuple = 1):
        """
        Returns an UiSprite.
        Settings is a tuple of (font, color, AA).
        If the text has newlines, set newline_settings to a tuple of (newline_height(int), text_alignment(str)).
        """
        font : pygame.Font
        color : pygame.Color|str
        AA_enabled : bool
        font, color, AA_enabled = settings
        color : pygame.Color = pygame.color.Color(color)
        if newline_settings is None:

            
            surf = font.render(text, AA_enabled, color).convert_alpha()
            surf = pygame.transform.scale_by(surf, scale)
            rect = surf.get_bounding_rect()
            rect.__setattr__(alignment, pos)
            return UiSprite(surf, rect, tag, attributes=attributes, name=name, keep_og_surf=keep_og_surf, forced_og_surf=forced_og_surf)
        else:
            newline_height, text_alignment = newline_settings
            if newline_height is None: newline_height = 5
            if text_alignment is None: text_alignment = 'center'

            lines = text.split('/n')
            line_count = len(lines)
            surfaces : list[pygame.Surface] = [font.render(line, AA_enabled, color).convert_alpha() for line in lines]

            line_heights = [surf.get_height() for surf in surfaces]
            line_widths = [surf.get_width() for surf in surfaces]

            total_height = sum(line_heights) + newline_height * (line_count - 1)
            total_width = max(line_widths)
            final_surf = pygame.surface.Surface((total_width, total_height), pygame.SRCALPHA)
            current_top = 0
            for surf in surfaces:
                rect = surf.get_rect()
                if text_alignment == 'left':
                    rect.topleft = (0, current_top)
                elif text_alignment == 'right':
                    rect.topright = (total_width, current_top)
                elif text_alignment == 'center':
                    rect.midtop = (int(total_width / 2), current_top)
                else:
                    rect.midtop = (int(total_width / 2), current_top)
                    
                final_surf.blit(surf, rect)
                current_top += surf.get_height()
                current_top += newline_height
            final_surf = pygame.transform.scale_by(final_surf, scale)
            final_rect = final_surf.get_bounding_rect()
            final_rect.__setattr__(alignment, pos)
            return UiSprite(final_surf, final_rect, tag, attributes=attributes, name=name, keep_og_surf=keep_og_surf, forced_og_surf=forced_og_surf)

            


    