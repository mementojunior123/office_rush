import pygame
from utils.animation import AnimationTrack, Animation
from typing import Any
from utils.helpers import is_sorted
class Sprite:
    '''Base class for all game objects.'''
    active_elements : list['Sprite'] = []
    inactive_elements : list['Sprite']  = []
    ordered_sprites : list['Sprite'] = []
    registered_classes : list['Sprite'] = []
    SPRITE_CLICKED : int = pygame.event.custom_type()

    def __init__(self) -> None:
        self.position : pygame.Vector2
        self.image : pygame.Surface
        self.rect : pygame.Rect
        self.mask : pygame.Mask
        self.zindex : int
        self.animation_tracks : dict[str, AnimationTrack]
        Sprite.inactive_elements.append(self)

    @classmethod
    def register_class(cls, class_to_register : 'Sprite'):
        if class_to_register not in cls.registered_classes:
            cls.registered_classes.append(class_to_register)
    
    @classmethod
    def pool(cls, element):
        '''Transfers an element from active to inactive state. Nothing changes if the element is already inactive.'''
        if element in cls.active_elements:
            cls.active_elements.remove(element)
        
        if element in Sprite.active_elements:
            Sprite.active_elements.remove(element)
        
        if element not in cls.inactive_elements:
            cls.inactive_elements.append(element)

        if element not in Sprite.inactive_elements:
            Sprite.inactive_elements.append(element)
    
    @classmethod
    def unpool(cls, element):
        '''Transfers an element from inactive to active state. Nothing changes if the element is already active.'''

        if element not in cls.active_elements:
            cls.active_elements.append(element)
        
        if element not in Sprite.active_elements:
            Sprite.active_elements.append(element)


        if element in cls.inactive_elements:
            cls.inactive_elements.remove(element)

        if element in Sprite.inactive_elements:
            Sprite.inactive_elements.remove(element)


    
    @classmethod
    def clear_elements(cls):
        '''Pools every element of the class'''
        while len(cls.active_elements) > 0:
            cls.pool(cls.active_elements[0])
    
    @staticmethod
    def clear_all_sprites():
        while len(Sprite.active_elements) > 0:
            element = Sprite.active_elements[0]
            cls = element.__class__
            cls.pool(element)


    @classmethod
    def spawn(cls):
        pass
    
    def update(self, delta : float):
        pass
    
    @classmethod
    def update_class(cls, delta : float):
        pass

    def self_destruct(self):
        cls = self.__class__
        cls.pool(self)

    @classmethod
    def update_all(cls, delta : float):
        element : cls
        for element in cls.active_elements:
            element.update(delta)
    
    @classmethod
    def update_all_sprites(cls, delta : float):
        element : Sprite
        for element in Sprite.active_elements:
            element.update(delta)
    
    @classmethod
    def update_all_registered_classes(cls, delta : float):
        element : Sprite
        for element in Sprite.active_elements:
            element.update_class(delta)
    
    def play_animation(self, animation : Animation, time_scale = 1):
        track = animation.load(self)
        track.play()
        if time_scale != 1:
            track.set_time_scale(time_scale)
        
        self.animation_tracks[animation.name] = track

    def animate(self):
        for name in self.animation_tracks:
            val = self.animation_tracks[name]
            val.update()
    
    def draw(self, display : pygame.Surface):
        display.blit(self.image, self.rect)
    
    @classmethod
    def draw_all(cls, display):
        element : cls
        for element in cls.active_elements:
            element.draw(display)

    @property
    def x(self):
       return self.position.x
    @x.setter
    def x(self, value):
        self.position.x = value
    @property
    def y(self):
        return self.position.y
    @y.setter
    def y(self, value):
        self.position.y = value
    
    def align_rect(self):
        self.rect.center = round(self.position)

    def get_colliding(self, collision_group : list['Sprite'], reqs : dict[str,Any] = None):
        if reqs is None: reqs = {}
        '''Returns the first sprite colliding this sprite within collision_group or None if there arent any. Uses mask collision.'''
        for cls in collision_group:
            for element in cls.active_elements:
                if not self.rect.colliderect(element.rect): continue
                if self.mask.overlap(element.mask,(element.rect.x - self.rect.x ,element.rect.y - self.rect.y)):
                    has_reqs = True
                    for req in reqs:
                        if not hasattr(self, req): 
                            has_reqs = False
                        if getattr(self, req) != reqs[req]: 
                            has_reqs = False
                    if has_reqs == False: continue
                    return element
        
        return None
    
    def get_rect_colliding(self, collision_group : list['Sprite']):
        '''Returns the first sprite colliding this sprite within collision_group or None if there arent any. Uses a bounding box check.'''
        for cls in collision_group:
            for element in cls.active_elements:
                if self.rect.colliderect(element.rect): return element
        return None
    
    def get_all_colliding(self, collision_group : list['Sprite']) -> list['Sprite']:
        '''Returns all entities colliding this sprite within collision_group. Uses mask collision.'''
        return_val = []
        for cls in collision_group:
            for element in cls.active_elements:
                if not self.rect.colliderect(element.rect): continue
                if self.mask.overlap(element.mask,(element.rect.x - self.rect.x ,element.rect.y - self.rect.y)): 
                    return_val.append(element)
        return return_val

    def get_all_rect_colliding(self, collision_group : list['Sprite']):
        '''Returns all entities colliding this sprite within collision_group. Uses a bounding box check.'''
        return_val = []
        for cls in collision_group:
            for element in cls.active_elements:
                if self.rect.colliderect(element.rect): return_val.append(element)
        return return_val

    def on_collision(self, other : 'Sprite'):
        pass

    def is_active(self):
        return self in self.__class__.active_elements
    
    @classmethod
    def draw_all_sprites(cls, display):
        #if not is_sorted(cls.active_elements, key=lambda sprite : sprite.zindex):
        cls.active_elements.sort(key=lambda sprite : sprite.zindex)
        element : Sprite
        for element in cls.active_elements:
            element.draw(display)

    
    @classmethod
    def get_sprite_class_by_name(cls, name : str) -> 'Sprite':
        for sprite_class in cls.registered_classes:
            if sprite_class.__name__ == name:
                return sprite_class
        return None
    
    @classmethod
    def handle_mouse_event(cls, event : pygame.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.touch: return
            press_pos : tuple = event.pos
            hit = [sprite for sprite in Sprite.active_elements if sprite.rect.collidepoint(press_pos)]
            if len(hit) == 0: return
            hit.sort(key = lambda sprite : sprite.zindex)
            new_event = pygame.event.Event(Sprite.SPRITE_CLICKED, {'main_hit' : hit[-1], 'all_hit' : hit, 'pos' : press_pos,
                                                                   'finger_id' : -1})
            pygame.event.post(new_event)
    
    @classmethod
    def handle_touch_event(cls, event : pygame.Event):
        if event.type == pygame.FINGERDOWN:
            x = event.x * core_object.main_display.get_width()
            y = event.y * core_object.main_display.get_height()
            press_pos : tuple[int, int] = (round(x), round(y))
            hit = [sprite for sprite in Sprite.active_elements if sprite.rect.collidepoint(press_pos)]
            if len(hit) == 0: return
            hit.sort(key = lambda sprite : sprite.zindex)
            new_event = pygame.event.Event(Sprite.SPRITE_CLICKED, {'main_hit' : hit[-1], 'all_hit' : hit, 'pos' : press_pos,
                                                                   'finger_id' : event.finger_id})
            pygame.event.post(new_event)
    
    @classmethod
    def _core_hint(cls):
        global core_object
        from core.core import core_object
            