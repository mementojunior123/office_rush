import pygame
import json
import random
from math import floor
from game.sprite import Sprite
from typing import Any
from collections import deque
from utils.helpers import sign
from utils.my_timer import Timer
import utils.interpolation as interpolation
from core.core import core_object
from typing import Callable

from utils.base_ui_elements import BaseUiElements
import utils.tween_module as TweenModule
from utils.textsprite import TextSprite
from utils.ui_sprite import UiSprite

zero_vector = pygame.Vector2(0,0)

def scale(surf :pygame.Surface, factor : float|tuple[float, float]):
    return pygame.transform.scale_by(surf, factor)

class DraggableLetter(Sprite):
    active_elements : list['DraggableLetter'] = []
    inactive_elements : list['DraggableLetter']  = []
    limbo : list['DraggableLetter'] = []
    #LETTER_SIZE = pygame.Vector2(150, 225)
    #LETTER_SIZE = pygame.Vector2(175, 262)
    LETTER_SIZE = pygame.Vector2(180, 270)
    #LETTER_SIZE = pygame.Vector2(200, 300)

    blank_paper_image : pygame.Surface = pygame.Surface(LETTER_SIZE)
    pygame.draw.rect(blank_paper_image, 'White', (0,0,LETTER_SIZE.x, LETTER_SIZE.y))
    mouse_offset_stream = deque([pygame.Vector2(0,0) for _ in range(8)])
    finger_offset_streams : dict[int, deque[pygame.Vector2]] = {}
    finger_offset_warnings : dict[int, int] = {}
    prev_mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
    prev_finger_pos : dict[int, tuple[int, int]] = {}
    main_font = pygame.font.Font('assets/fonts/Pixeltype.ttf', 40)
    font_35 = pygame.font.Font('assets/fonts/Pixeltype.ttf', 35)
    letter_drag = 0.88
    letter_stop_speed = 0.7
    screen_rect = pygame.Rect(0,0, core_object.main_display.get_width(), core_object.main_display.get_height())

    LETTER_RELEASED = pygame.event.custom_type()
    def __init__(self) -> None:
        Sprite.inactive_elements.append(self)
        DraggableLetter.inactive_elements.append(self)
        self.is_dragged : bool
        self.drag_offset : pygame.Vector2|None
        self.drag_id : int|None

        self.position : pygame.Vector2
        self.image : pygame.Surface
        self.rect : pygame.Rect
        self.mask : pygame.Mask
        self.animation_tracks : dict[str, Any]
        self.zindex : int = 100
        self.velocity : pygame.Vector2
        self.data : LetterInfo|None
        self.slide_timer : Timer|None
        self.slide_start_yvelocity : float|None
        self.valid_area : pygame.Rect

    @classmethod
    def spawn(cls, pos : pygame.Vector2, text : str, font : pygame.Font, data : 'LetterInfo' = None, valid_area : pygame.Rect|None = None):
        if data is None:
            data = LetterInfo(text, None, None, {})
        for letter in cls.active_elements:
            letter.zindex -=1 if letter.zindex > 0 else 0
        new_paper = cls.inactive_elements[0]
        cls.unpool(new_paper)
        new_paper.image = cls.blank_paper_image.copy()
        new_paper.position = pos
        new_paper.rect = new_paper.image.get_rect(center = round(pos))
        new_paper.data = data
        new_paper.render_text(text, font)
        new_paper.stop_drag()
        new_paper.velocity = pygame.Vector2(0,0)
        new_paper.zindex = 99
        new_paper.slide_timer = None
        new_paper.slide_start_yvelocity = None
        new_paper.valid_area = DraggableLetter.screen_rect.copy() if valid_area is None else valid_area
        
        
        return new_paper
    
    @classmethod
    def to_limbo(cls, element):
        '''Transfers the element from whatever state it was to the limbo. 
        Be careful when using the limbo: Elements in the limbo must be removed manually.'''
        if element in cls.active_elements:
            cls.active_elements.remove(element)
        
        if element in Sprite.active_elements:
            Sprite.active_elements.remove(element)
        
        if element in cls.inactive_elements:
            cls.inactive_elements.remove(element)

        if element in Sprite.inactive_elements:
            Sprite.inactive_elements.remove(element)

        if element not in cls.limbo:
            cls.limbo.append(element)
    
    @classmethod
    def pool(cls, element):
        '''Transfers an element from active to inactive state and removes them from the limbo. 
        Nothing changes if the element is already inactive.'''
        if element in cls.active_elements:
            cls.active_elements.remove(element)
        
        if element in Sprite.active_elements:
            Sprite.active_elements.remove(element)
        
        if element not in cls.inactive_elements:
            cls.inactive_elements.append(element)

        if element not in Sprite.inactive_elements:
            Sprite.inactive_elements.append(element)

        if element in cls.limbo:
            cls.limbo.remove(element)
    
    @classmethod
    def unpool(cls, element):
        '''Transfers an element from inactive to active state and removes them from the limbo. 
        Nothing changes if the element is already active.'''
        if element not in cls.active_elements:
            cls.active_elements.append(element)
        
        if element not in Sprite.active_elements:
            Sprite.active_elements.append(element)


        if element in cls.inactive_elements:
            cls.inactive_elements.remove(element)

        if element in Sprite.inactive_elements:
            Sprite.inactive_elements.remove(element)

        if element in cls.limbo:
            cls.limbo.remove(element)
    
    @classmethod
    def cleanup(cls):
        while len(cls.limbo) > 0:
            cls.pool(cls.limbo[0])
    
    def clear_text(self, color = 'White'):
        pygame.draw.rect(self.image, color, (0,0, *DraggableLetter.LETTER_SIZE))

    def render_text(self, text : str, font : pygame.Font):
        color = 'White'
        if self.data:
            if self.data.is_unique:
                color = '#5DE9A2'
        self.clear_text(color)
        new_surf : pygame.Surface = font.render(text, False, 'Black', wraplength=floor(self.image.get_width() - 5))
        self.image.blit(new_surf, (5, 5))

    def stop_drag(self):
        self.is_dragged = False
        self.drag_id = None
        self.drag_offset = None

    @classmethod
    def handle_mouse_event(cls, event : pygame.Event):
        '''
        if event.type == pygame.MOUSEBUTTONDOWN:
            press_pos : tuple = event.pos
            dragged_letters = []
            letter : DraggableLetter
            for letter in cls.active_elements:
                if letter.rect.collidepoint(press_pos):
                    dragged_letters.append(letter)
            
            selected_letter = None
            max_zindex = -909099090
            for letter in dragged_letters:
                if letter.zindex > max_zindex:
                    selected_letter = letter
                    max_zindex = letter.zindex
            if selected_letter:        
                selected_letter.is_dragged = True
                selected_letter.drag_id = -1
                selected_letter.drag_offset = pygame.Vector2(selected_letter.rect.center) - press_pos
                selected_letter.zindex = 100
                for letter in cls.active_elements:
                    letter.zindex -=1 if letter.zindex > 0 else 0
        '''
        if event.type == pygame.MOUSEBUTTONUP:
            if event.touch: return
            for letter in cls.active_elements:
                if letter.drag_id == -1:
                    mouse_velocity = DraggableLetter.get_mouse_velocity()
                    letter.stop_drag()
                    letter.velocity = mouse_velocity * 0.5
                    letter.zindex = 99
                    new_event = pygame.Event(DraggableLetter.LETTER_RELEASED, {'letter' : letter})
                    pygame.event.post(new_event)
        
        elif event.type == pygame.FINGERUP:
            for letter in cls.active_elements:
                if letter.drag_id == event.finger_id:
                    finger_velocity = DraggableLetter.get_finger_speed(event.finger_id)
                    #finger_velocity = pygame.Vector2(0,0)
                    #core_object.set_debug_message(f'({finger_velocity.x}, {finger_velocity.y})')
                    letter.stop_drag()
                    letter.velocity = finger_velocity * 0.5
                    letter.zindex = 99
                    new_event = pygame.Event(DraggableLetter.LETTER_RELEASED, {'letter' : letter})
                    pygame.event.post(new_event)
            cls.finger_offset_streams.pop(event.finger_id, None)
            cls.finger_offset_warnings.pop(event.finger_id, None)
            core_object.set_debug_message(f'Stream {event.finger_id} removed')

        elif event.type == pygame.FINGERDOWN:
            finger_id = event.finger_id
            cls.finger_offset_streams[finger_id] = deque([pygame.Vector2(0, 0) for _ in range(8)])
            cls.finger_offset_warnings[finger_id] = 0
            core_object.set_debug_message(f'Stream {finger_id} added')

        elif event.type == Sprite.SPRITE_CLICKED:
            letter = event.main_hit
            press_pos : tuple = event.pos
            if isinstance(letter, DraggableLetter):
                for unselected_letter in cls.active_elements:
                    unselected_letter.zindex -=1 if unselected_letter.zindex > 0 else 0
        
                letter.is_dragged = True
                letter.drag_id = event.finger_id if event.finger_id >= 0 else -1
                letter.drag_offset = pygame.Vector2(letter.rect.center) - press_pos
                letter.zindex = 100
                

                

    def update(self, delta : float):
        if self.is_dragged:
            drag_pos = pygame.mouse.get_pos() if self.drag_id == -1 else core_object.active_fingers[self.drag_id]
            self.position = drag_pos + self.drag_offset
            
        elif self.velocity != zero_vector:
            self.position += self.velocity
            self.velocity *= DraggableLetter.letter_drag ** delta
            self.position += self.velocity

            if self.velocity.magnitude() < DraggableLetter.letter_stop_speed * delta:
                self.velocity = pygame.Vector2(0,0)
        self.rect.center = round(self.position)
        result = self.clip_to_area(self.valid_area)
        if not result:
            if self.is_dragged:
                self.drag_offset = pygame.Vector2(self.rect.center) - drag_pos
    
    def clip_to_area(self, area : pygame.Rect):
        did_clip = True
        if self.rect.top < area.top: 
            self.rect.top = area.top
            did_clip = False
            if self.velocity.y < 0: self.velocity.y *= -0.8

        if self.rect.bottom > area.bottom: 
            self.rect.bottom = area.bottom
            did_clip = False
            if self.velocity.y > 0: self.velocity.y *= -0.8

        if self.rect.left < area.left: 
            self.rect.left = area.left
            did_clip = False
            if self.velocity.x < 0: self.velocity.x *= -0.8

        if self.rect.right > area.right: 
            self.rect.right = area.right
            did_clip = False
            if self.velocity.x > 0: self.velocity.x *= -0.8

        return did_clip

    
    @classmethod
    def update_class(cls, delta : float):
        cls.update_mouse_stream(delta)
        cls.update_finger_streams(delta)
        
    
    @classmethod
    def update_mouse_stream(cls, delta : float):
        target_lentgh = round(3 / delta)
        current_lentgh = len(cls.mouse_offset_stream)
        new_pos = pygame.Vector2(pygame.mouse.get_pos())
        if current_lentgh == target_lentgh:
            cls.mouse_offset_stream.popleft()
        elif current_lentgh > target_lentgh:
            cls.mouse_offset_stream.popleft()
            cls.mouse_offset_stream.popleft()
        cls.mouse_offset_stream.append(new_pos - cls.prev_mouse_pos)
        cls.prev_mouse_pos = new_pos
    
    @classmethod
    def update_finger_streams(cls, delta : float):
        target_lentgh = round(3 / delta)
        for finger_id in cls.finger_offset_streams:
            if finger_id not in cls.prev_finger_pos:
                continue
            elif finger_id not in core_object.active_fingers:
                continue
            prev_pos = pygame.Vector2(cls.prev_finger_pos[finger_id])
            new_pos = pygame.Vector2(core_object.active_fingers[finger_id])
            stream = cls.finger_offset_streams[finger_id]
            current_lentgh = len(stream)
            if current_lentgh == target_lentgh:
                stream.popleft()
            elif current_lentgh > target_lentgh:
                stream.popleft()
                stream.popleft()
            stream.append(new_pos - prev_pos)
            cls.prev_finger_pos[finger_id] = new_pos
        cls.prev_finger_pos = core_object.active_fingers.copy()

    
    @classmethod
    def get_mouse_velocity(cls) -> pygame.Vector2:
        total = pygame.Vector2(0,0)
        for vec in cls.mouse_offset_stream:
            total += vec
        return total / len(cls.mouse_offset_stream)
    
    @classmethod
    def get_finger_speed(cls, finger_id : int):
        total = pygame.Vector2(0,0)
        if finger_id not in cls.finger_offset_streams:
            core_object.set_debug_message('Stream not found')
            return total
        stream = cls.finger_offset_streams[finger_id]
        
        count = len(stream)
        for vec in stream:
            total += vec
        return total / len(stream) if count > 0 else pygame.Vector2(0,0)

Sprite.register_class(DraggableLetter)


class LetterPile(Sprite):
    active_elements : list['LetterPile'] = []
    inactive_elements : list['LetterPile']  = []
    corner_offset = pygame.Vector2(12,12)
    blank_paper_image = scale(pygame.image.load(r'assets/graphics/tasks/letters/blank_paper.png').convert(), 0.9)
    paper_template_image = scale(pygame.image.load(r'assets/graphics/tasks/letters/mid_dense_paper.png').convert(), 0.9)
    low_density_template_image = scale(pygame.image.load(r'assets/graphics/tasks/letters/low_dense_paper.png').convert(), 0.9)
    high_density_template_image = scale(pygame.image.load(r'assets/graphics/tasks/letters/high_dense_paper.png').convert(), 0.9)
    def __init__(self) -> None:
        LetterPile.inactive_elements.append(self)
        Sprite.active_elements.append(self)
        self.position : pygame.Vector2
        self.image : pygame.Surface
        self.rect : pygame.Rect
        self.mask : pygame.Mask
        self.zindex : int
        self.prev_letter_count : int = 0
        self.letter_count : int = 0
        self.stack : list['LetterInfo']
    
    def update(self, delta : float):
        self.letter_count = len(self.stack)
        if self.letter_count != self.prev_letter_count:
            self.update_apperance()
            self.position += self.get_pos_offset(self.prev_letter_count, self.letter_count)
            self.rect.center = round(self.position)
        self.prev_letter_count = self.letter_count
    
    def get_pos_offset(self,old_letter_count, new_count):
        if old_letter_count == new_count:
            return pygame.Vector2(0,0)
        if old_letter_count <= 1 and new_count <= 1:
            return pygame.Vector2(0,0)
        b = new_count if new_count > 0 else 1
        a = old_letter_count if old_letter_count > 0 else 1
        gap = b-a
        return (gap * LetterPile.corner_offset) / 2
        
    def update_apperance(self):
        if self.letter_count == 0:
            self.image = LetterPile.paper_template_image.copy()
            self.image.fill((90,90,90,0), special_flags=pygame.BLEND_RGBA_SUB)
        elif self.letter_count == 1:
            self.image = LetterPile.paper_template_image
        else:
            initial_size = LetterPile.paper_template_image.get_size()
            corner_offset = LetterPile.corner_offset
            colorkey = (0, 255, 0) #green
            self.image = pygame.Surface((corner_offset * (self.letter_count - 1)) + initial_size)
            self.image.fill(colorkey)
            self.image.set_colorkey(colorkey)
            for i in range(self.letter_count):
                reverse_i = self.letter_count - i - 1
                y = corner_offset.y * i
                x = corner_offset.x * i
                self.image.blit(LetterPile.paper_template_image, (x, y))
        self.rect = self.image.get_rect(center = round(self.position))


    def new_letter_on_click(self, press_pos : tuple, finger_id : int):
        if core_object.game.game_state == core_object.game.STATES.transition: return
        if len(self.stack) <= 0:
            return
            info = None
            text = 'No letters left!'
        else:
            info = self.stack[0]
            text = info.text
            self.stack.remove(info)
        spawn_pos = self.position + ((self.corner_offset * (self.letter_count - 1)) / 2)
        new_letter = DraggableLetter.spawn(spawn_pos, text, DraggableLetter.font_35, data=info)
        new_letter.is_dragged = True
        new_letter.drag_id = finger_id
        new_letter.drag_offset = pygame.Vector2(new_letter.rect.center) - press_pos
        new_letter.zindex = 100
    
    @classmethod
    def handle_mouse_event(cls, event : pygame.Event):
        '''
        if event.type == pygame.MOUSEBUTTONDOWN:
            press_pos : tuple = event.pos
            letter_pile : LetterPile
            for letter_pile in cls.active_elements:
                if letter_pile.rect.collidepoint(press_pos):
                    letter_pile.new_letter_on_click(press_pos)
                    break
        '''
        if event.type == Sprite.SPRITE_CLICKED:
            letter_pile : LetterPile = event.main_hit
            if isinstance(letter_pile, LetterPile):
                letter_pile.new_letter_on_click(event.pos, event.finger_id)
            

    
    @classmethod
    def spawn(cls, pos : pygame.Vector2, template_density : str = 'Normal', start_stack = None):
        if start_stack is None: start_stack = []
        new_pile = cls.inactive_elements[0]
        new_pile.zindex = 50
        cls.unpool(new_pile)
        image_dict = {'Low' : cls.low_density_template_image, 'Normal' : cls.paper_template_image, 'High' : cls.high_density_template_image}
        new_pile.image = image_dict.get(template_density, cls.paper_template_image)
        new_pile.position = pos
        new_pile.rect = new_pile.image.get_rect(center = round(pos))
        new_pile.stack = start_stack
        new_pile.update_apperance()
        return new_pile

Sprite.register_class(LetterPile)

class LetterInfo:
    with open(r'assets/data/letters/messages.json', 'r') as file:
        messages : dict = json.load(file)
    with open(r'assets/data/letters/tokens.json', 'r') as file:
        tokens : dict = json.load(file)
    all_messages : list[dict] = []

    def __init__(self, text : str, letter_type : str, subtype : str, data : dict, name : str|None, is_unique : bool) -> None:
        self.text : str = text
        self.type : str = letter_type
        self.subtype : str = subtype
        self.data : dict = data
        self.name : str|None = name
        self.is_unique : bool = is_unique
    
    @classmethod
    def get_data_by_name(cls, name : str) -> dict|None:
        for message in cls.all_messages:
            if message.get('name', None) == name:
                return message
        return None

    @classmethod
    def from_message(cls, message_data : dict, other_data : dict|None = None):
        if other_data is None: other_data = {}
        text : str = message_data['text']
        tokens : dict[str, str] = message_data['tokens']
        for token in tokens:
            token_type = tokens[token]
            replacement : str = random.choice(LetterInfo.tokens[token_type])
            text = text.replace(token,replacement)
        type : str = message_data['type']
        subtype : str|None = message_data['subtype']
        name : str|None = message_data.get('name', None)
        is_unique : bool = message_data.get('unique', None)
        return LetterInfo(text, type, subtype, other_data, name, is_unique)

    
    @classmethod
    def random(cls, categories : dict[str, float]|None = None, other_data = None):
        valid_messages : list[dict]

        if categories is not None:
            selected_categories = [key for key in categories]
            weights = [categories[key] for key in categories]
            chosen_category = random.choices(selected_categories, weights)[0]
            valid_messages = cls.messages[chosen_category]
        else:
            valid_messages = cls.all_messages
            #print(valid_messages)
        chosen_message : dict = random.choice(valid_messages)
        return LetterInfo.from_message(chosen_message, other_data)
    
for category in LetterInfo.messages:
    LetterInfo.all_messages += LetterInfo.messages[category]

class LetterFolder(Sprite):
    LETTER_SORTED = pygame.event.custom_type()
    #folder_image = scale(pygame.image.load(r'assets/graphics/tasks/letters/folder.png').convert_alpha(), 0.75)
    #top_part_image = scale(pygame.image.load(r'assets/graphics/tasks/letters/folder_top.png').convert_alpha(), 0.75)
    folder_image_wcolorkey = scale(pygame.image.load('assets/graphics/tasks/letters/folder_red_colorkey.png').convert(), 0.75)
    folder_image_wcolorkey.set_colorkey((255, 0, 0))
    top_part_image_wcolorkey = scale(pygame.image.load('assets/graphics/tasks/letters/folder_top_red_colorkey.png').convert(), 0.75)
    top_part_image_wcolorkey.set_colorkey((255, 0, 0))
    active_elements : list['LetterFolder'] = []
    inactive_elements : list['LetterFolder'] = []

    letter_sorted_sfx = pygame.mixer.Sound(r'assets/audio/tasks/letters/letter_sorted.ogg')
    error_sfx = pygame.mixer.Sound(r'assets/audio/tasks/letters/error_sfx.ogg')
    def __init__(self) -> None:
        self.position : pygame.Vector2
        self.image : pygame.Surface
        self.top_part : LetterFolderTopPart
        self.rect : pygame.Rect
        self.mask : pygame.Mask
        self.zindex : int
        self.sliding_letters : list[DraggableLetter]
        self.sorting_criteria : Callable[['LetterFolder', DraggableLetter], bool]
        self.sorting_data : dict
        Sprite.inactive_elements.append(self)
        LetterFolder.inactive_elements.append(self)
    
    @classmethod
    def spawn(cls, pos : pygame.Vector2, sort_criteria : Callable[['LetterFolder', DraggableLetter], bool], sorting_data : dict = None,
              sticker_text : str|None = None, sticker_text_settings : tuple[pygame.Font, pygame.Color|str, bool] = None, 
              sticker_surf : pygame.Surface|None = None, rel_sticker_pos : pygame.Vector2|None = None):
        if sorting_data is None: sorting_data = {}
        new_folder = cls.inactive_elements[0]
        new_folder.zindex = 30
        cls.unpool(new_folder)
        new_folder.position = pos
        new_folder.image = cls.folder_image_wcolorkey
        new_folder.rect = new_folder.image.get_rect(center = round(pos))
        new_folder.sliding_letters = []
        new_folder.top_part = LetterFolderTopPart.spawn(None, sticker_text, sticker_text_settings, sticker_surf, rel_sticker_pos)
        new_folder.top_part.rect.midbottom = new_folder.rect.midbottom
        new_folder.top_part.position = pygame.Vector2(new_folder.top_part.rect.center)
        new_folder.sorting_criteria = sort_criteria
        new_folder.sorting_data = sorting_data
        return new_folder
    

    def collide_letter(self, other : DraggableLetter) -> bool:
        if not self.rect.colliderect(other.rect): return False
        if core_object.game.game_state == core_object.game.STATES.transition: return False
        left_peek : float = self.rect.left + abs(other.velocity.x) if sign(other.velocity.x) == -1 else self.rect.left
        right_peek : float = self.rect.right + abs(other.velocity.x) if sign(other.velocity.x) == 1 else self.rect.right
        if not (left_peek <= other.position.x <= right_peek):
            return False

        y_overlap : float = abs(other.rect.bottom - self.rect.top)
        if y_overlap > 45 and self.rect.bottom > other.rect.bottom:
            return True
        return False
    

    @classmethod
    def handle_letter_release_event(cls, event : pygame.Event):
        if event.type != DraggableLetter.LETTER_RELEASED: return
        letter : DraggableLetter = event.letter
        result : LetterFolder|None = None
        folder : LetterFolder
        for folder in LetterFolder.active_elements:
            if folder.collide_letter(letter):
                result = folder
                break
        
        if result is None: return
        result.take_letter(letter)
    
    @classmethod
    def handle_letter_sorted_event(cls, event : pygame.Event):
        if event.type != LetterFolder.LETTER_SORTED:
            return
        letter : DraggableLetter = event.letter
        folder : LetterFolder = event.folder
        result = folder.sorting_criteria(folder, letter)
        if result:
            pass
        else:
            pass
    
    def draw(self, display : pygame.Surface):
        if len(self.sliding_letters) <= 0:
            display.blit(self.image, self.rect)
            #pygame.draw.circle(display, 'Red', self.rect.midtop, 4)
            #pygame.draw.circle(display, 'Green', (self.position.x, self.rect.top), 4)
            return
        
        display.blit(self.image, self.rect)
        for letter in self.sliding_letters:
            height_to_remove : float = letter.rect.bottom - self.rect.bottom
            display.blit(letter.image, letter.rect, (0, 0, letter.rect.width, letter.rect.height - height_to_remove - 5))
        
    
    def take_letter(self, letter : DraggableLetter):
        if core_object.game.game_state == core_object.game.STATES.transition: return
        DraggableLetter.to_limbo(letter)
        self.sliding_letters.append(letter)
        letter.slide_timer = Timer(0.6)
        letter.slide_start_yvelocity = letter.velocity.y
        if abs(letter.velocity.x) < 0.01: letter.velocity.x = 0
        core_object.bg_manager.play_sfx(LetterFolder.letter_sorted_sfx, 0.15)

    def update(self, delta : float):
        self.top_part.rect.midbottom = self.rect.midbottom
        self.top_part.position = pygame.Vector2(self.top_part.rect.center)
        to_remove : list[DraggableLetter] = []
        for letter in self.sliding_letters:
            result = self.update_sliding_letter(delta, letter)
            if result == True:
                to_remove.append(letter)
                self.confrim_letter_sorted(letter)
        
        for letter in to_remove:
            DraggableLetter.pool(letter)
            self.sliding_letters.remove(letter)
        
    
    def confrim_letter_sorted(self, letter : DraggableLetter):
        new_event : pygame.Event = pygame.event.Event(LetterFolder.LETTER_SORTED, {'letter' : letter, 'folder' : self})
        pygame.event.post(new_event)

    def update_sliding_letter(self, delta : float, letter : DraggableLetter):
        if letter.slide_timer.get_time() > 0.55 : return True
        letter.position += letter.velocity * 0.5 * delta
        current_side = sign(letter.position.x - self.position.x)
        velocity_direction = sign(letter.velocity.x)
        x_offset = letter.position.x - self.position.x

        if abs(x_offset) < 25:
            letter.velocity.x = 0
        elif current_side == -1:

            if abs(letter.velocity.x) < 0.5 * delta:
                letter.velocity.x = 8 
            
            elif velocity_direction == -1: #wrong direction (We are to the left and going to the left)
                
                predicted_speed_loss : float = abs((letter.velocity.x) - (letter.velocity.x * (0.5 ** delta)))
                if predicted_speed_loss > (1 * delta):
                    letter.velocity.x += predicted_speed_loss
                else:
                    letter.velocity.x += 1 * delta
                    
            elif velocity_direction == 1:#We are to the left and going to the right
                
                if abs(x_offset) < 25:
                    letter.velocity.x = 0
                elif abs(x_offset) < 65:
                    letter.velocity.x *= 0.85 ** delta
                else:
                    if letter.velocity.x > 4: letter.velocity.x = 4
                    letter.velocity.x *= 1.05 ** delta

        elif current_side == 1:
            if abs(letter.velocity.x) < 0.5 * delta:
                letter.velocity.x = -8

            elif velocity_direction == 1: #wrong direction (We are to the right and going to the right)
                
                predicted_speed_loss : float = abs((letter.velocity.x) - (letter.velocity.x * (0.5 ** delta)))
                if (predicted_speed_loss) > (1 * delta):
                    letter.velocity.x -= predicted_speed_loss
                else:
                    letter.velocity.x -= 1 * delta

            elif velocity_direction == -1: #We are to the right and going to the left

                if abs(x_offset) < 25:
                    letter.velocity.x = 0
                elif abs(x_offset) < 65:
                    letter.velocity.x *= 0.85 ** delta
                else:
                    if letter.velocity.x < 4: letter.velocity.x = -4
                    letter.velocity.x *= 1.05 ** delta
       
        alpha = letter.slide_timer.get_time() / letter.slide_timer.duration
        if alpha > 1: alpha = 1
        letter.velocity.y = interpolation.lerp(letter.slide_start_yvelocity, 14, interpolation.cubic_ease_out(alpha))
        letter.position += letter.velocity * 0.5 * delta
        letter.rect.center = round(letter.position)
        return False
        
class SortingCriteria:
    @staticmethod
    def everything(folder : LetterFolder, letter : DraggableLetter):
        return True
    
    @staticmethod
    def nothing(folder : LetterFolder, letter : DraggableLetter):
        return False
    
    @staticmethod
    def contains_string(folder : LetterFolder, letter : DraggableLetter):
        if letter.data.text.find(folder.sorting_data['target_string']):
            return True
        return False
    
    @staticmethod
    def is_category(folder : LetterFolder, letter : DraggableLetter):
        if letter.data.type == folder.sorting_data['target_type']:
            return True
        return False
    
    @staticmethod
    def is_subtype(folder : LetterFolder, letter : DraggableLetter):
        if letter.data.subtype == folder.sorting_data['target_subtype']:
            return True
        return False
    
    @staticmethod
    def dosent_fit(folder : LetterFolder, letter : DraggableLetter):
        other_folder : LetterFolder
        for other_folder in folder.sorting_data['other_folders']:
            if other_folder.sorting_criteria(other_folder, letter):
                return False
        return True
    
Sprite.register_class(LetterFolder)

class LetterFolderTopPart(Sprite):
    active_elements : list['LetterFolderTopPart'] = []
    inactive_elements : list['LetterFolderTopPart'] = []

    def __init__(self) -> None:
        self.position : pygame.Vector2
        self.image : pygame.Surface
        self.rect : pygame.Rect
        self.mask : pygame.Mask
        self.zindex : int
        Sprite.inactive_elements.append(self)
        LetterFolderTopPart.inactive_elements.append(self)
    
    @classmethod
    def spawn(cls, pos : pygame.Vector2|list|tuple = None, sticker_text : str|None = None, 
              sticker_text_settings : tuple[pygame.Font, pygame.Color|str, bool] = None, sticker_surf : pygame.Surface|None = None,
              rel_sticker_pos : pygame.Vector2|None = None):
        
        if pos is None:
            pos = pygame.Vector2(500,500)
        if type(pos) != pygame.Vector2:
            pos = pygame.Vector2(pos)
        
        new_part : LetterFolderTopPart = cls.inactive_elements[0]
        cls.unpool(new_part)
        new_part.zindex = 150
        new_part.image = LetterFolder.top_part_image_wcolorkey
        if sticker_text is not None or sticker_surf is not None:
            sticker_size = pygame.Vector2(140, 35)
            if rel_sticker_pos is None: rel_sticker_pos = pygame.Vector2(-40, -15)
            if sticker_surf is None: 
                sticker_surf = pygame.surface.Surface(sticker_size)
                pygame.draw.rect(sticker_surf, 'White', (0,0, sticker_size.x, sticker_size.y))
                pygame.draw.rect(sticker_surf, 'Black', (0,0, sticker_size.x, sticker_size.y), width=4)
            if sticker_text is not None:
                font, color, use_AA = (DraggableLetter.main_font, 'Black', False) if sticker_text_settings is None else sticker_text_settings
                text_surf = font.render(sticker_text, use_AA, color)
                text_rect = text_surf.get_bounding_rect()
                text_rect.center = sticker_size // 2
                sticker_surf.blit(text_surf, text_rect)

            new_part.image = new_part.image.copy()
            top_part_center = pygame.Vector2(new_part.image.get_size()) / 2
            sticker_center = round(top_part_center + rel_sticker_pos)
            new_part.image.blit(sticker_surf, sticker_surf.get_rect(center = sticker_center))
            
        new_part.rect = new_part.image.get_rect(center = round(pos))
        new_part.position = pos
        return new_part

Sprite.register_class(LetterFolderTopPart)