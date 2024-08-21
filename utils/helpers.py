import pygame
from math import copysign
from typing import Callable, Any
from random import random

def rotate_around_pivot(image : pygame.Surface, rect : pygame.Rect, angle : float, 
                        anchor : pygame.Vector2 = None, offset : pygame.Vector2= None, return_new_pos = False):
    
    if anchor:
        real_anchor_point = anchor or pygame.Vector2(rect.center) + offset
        offset= offset or real_anchor_point - pygame.Vector2(rect.center)

    elif offset:
        real_anchor_point = offset + pygame.Vector2(rect.center)
        offset = offset

    new_offset = offset.rotate(angle)
    old_center = rect.center

    new_image = pygame.transform.rotate(image, -angle)
    new_rect = new_image.get_rect(center = old_center)
    new_pos = real_anchor_point - new_offset
    new_rect.center = round(new_pos)
    if return_new_pos:
        return new_image, new_rect, new_pos
    else:
        return new_image, new_rect

def rotate_around_center(image : pygame.Surface, pos : pygame.Vector2, angle : float) -> tuple[pygame.Surface, pygame.Rect]:
    new_image = pygame.transform.rotate(image, -angle)
    new_rect = new_image.get_rect(center = round(pos))
    return new_image, new_rect

def rotate_around_pivot_accurate(image : pygame.Surface, pos : pygame.Vector2, angle : float, 
                        anchor : pygame.Vector2 = None, offset : pygame.Vector2 = None, debug = False):
    
    if anchor is not None:
        real_anchor_point = anchor
        offset = offset or (real_anchor_point - pos).rotate(-angle)

    elif offset is not None:
        real_anchor_point = pos + offset.rotate(angle)
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

def sign(x):
    return copysign(1, x)
def is_sorted(iterable : list[object], key : Callable[[object], float|int]):
    current_val = key(iterable[0])
    for obj in iterable:
        val = key(obj)
        if val < current_val: return False
    return True

def average(values : list[float]):
    return sum(values) / len(values)

def random_float(a : float, b : float):
    return pygame.math.lerp(a, b, random())
