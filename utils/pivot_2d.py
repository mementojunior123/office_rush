import pygame
from typing import Any
def rotate_around_pivot_accurate(image : pygame.Surface, pos : pygame.Vector2, angle : float, 
                        anchor : pygame.Vector2 = None, offset : pygame.Vector2 = None, debug = False):
    
    real_anchor_point : pygame.Vector2
    if anchor is not None:
        real_anchor_point = anchor
        offset = offset or (real_anchor_point - pos)

    elif offset is not None:
        real_anchor_point = pos
        offset = offset
    else:
        raise ValueError('Either offset or anchor must be provided')
    new_offset = offset.rotate(angle)

    new_image = pygame.transform.rotate(image, -angle)  
    new_pos = real_anchor_point - new_offset


    new_rect = new_image.get_rect(center = round(new_pos))
    if debug:
        return new_image, new_rect, new_pos, [real_anchor_point]
    else:
        return new_image, new_rect, new_pos

def rotate_around_pivot_pos_only(pos : pygame.Vector2, angle : float, offset : pygame.Vector2):
    return pos - offset.rotate(angle)


class Pivot2D:
    def __init__(self, pos : pygame.Vector2) -> None:
        self._origin : pygame.Vector2 = pos
        self._pivot_offset : pygame.Vector2 = pygame.Vector2(0,0)
        self._angle : float = 0
        self._position : pygame.Vector2 = self._origin.copy()
        self.is_cached : bool = True
    
    @property
    def origin(self):
        return self._origin
    
    @origin.setter
    def origin(self, new_val : pygame.Vector2):
        self._origin = new_val
        self.is_cached = False
    
    @property
    def angle(self):
        return self._angle
    
    @angle.setter
    def angle(self, new_val : float):
        self._angle = new_val
        self.is_cached = False
    
    @property
    def pivot_offset(self):
        return self._pivot_offset
    
    @pivot_offset.setter
    def pivot_offset(self, new_val : pygame.Vector2):
        self._pivot_offset = new_val
        self.is_cached = False

    
    @property
    def position(self) -> pygame.Vector2:
        if not self.is_cached: 
            self._position = rotate_around_pivot_pos_only(self._origin, self._angle, self._pivot_offset)
        return self._position
    
    def rotate_image(self, image : pygame.Surface) -> tuple[pygame.Surface, pygame.Rect, pygame.Vector2]:
        return rotate_around_pivot_accurate(image, self._origin, self._angle, None, self._pivot_offset, debug=False)
    
    def rotate_image_debug(self, image : pygame.Surface) -> tuple[pygame.Surface, pygame.Rect, pygame.Vector2, Any]:
        return rotate_around_pivot_accurate(image, self._origin, self._angle, None, self._pivot_offset, debug=True)