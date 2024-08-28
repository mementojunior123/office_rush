import pygame
import json
import random
from game.sprite import Sprite
from core.core import core_object
from typing import Any, Callable
from utils.helpers import rotate_around_center
from utils.my_timer import Timer
import utils.tween_module as TweenModule
import utils.interpolation as interpolation
from utils.pivot_2d import Pivot2D
from utils.ui_sprite import UiSprite
from utils.textbox import TextBox

class Telephone(Sprite):
    inactive_elements : list['Telephone'] = []
    active_elements : list['Telephone'] = []

    #full_image = pygame.image.load_sized_svg(r'assets/graphics/tasks/phone/vectorized_telephone.svg', (300, 253)).convert_alpha()
    full_image = pygame.image.load(r'assets/graphics/tasks/phone/final_telephone.png').convert()
    full_image = pygame.transform.scale_by(full_image, 200 / full_image.get_width())
    full_image.set_colorkey((0,0,0))

    #no_phone_image = pygame.image.load_sized_svg(r'assets/graphics/tasks/phone/telephone_base.svg', (300, 300)).convert_alpha()

    no_phone_image = pygame.image.load(r'assets/graphics/tasks/phone/good_telephone_base_red_colorkey.png').convert()
    no_phone_image = pygame.transform.scale_by(no_phone_image, 200.3 / no_phone_image.get_width())
    no_phone_image.set_colorkey((255, 0, 0))

    phone_ring_sfx = pygame.mixer.Sound(r'assets/audio/tasks/phone/phone_ring.ogg')
    short_ring_sfx = pygame.mixer.Sound(r'assets/audio/tasks/phone/short_ring.ogg')

    PROMPT_SCALE : float = 0.5
    PROMPT_START_HEIGHT : int = 120

    green_outline_textbox_image = pygame.image.load(r'assets/graphics/general/green_outline_textbox_red_colorkey.png').convert()
    green_outline_textbox_image = pygame.transform.scale_by(green_outline_textbox_image, PROMPT_SCALE)
    green_outline_textbox_image.set_colorkey((255, 0, 0))

    dark_blue_outline_textbox_image = pygame.image.load(r'assets/graphics/general/dark_blue_outline_textbox_red_colorkey.png').convert()
    dark_blue_outline_textbox_image = pygame.transform.scale_by(dark_blue_outline_textbox_image, PROMPT_SCALE)
    dark_blue_outline_textbox_image.set_colorkey((255, 0, 0))
    
    font_30 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 30)
    font_35 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 35)
    font_38 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 38)
    font_39 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 39)
    font_40 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)

    def __init__(self) -> None:
        super().__init__()
        Telephone.inactive_elements.append(self)
        self.phone_part_seprated : bool
        self.top_part : TelephoneTopPart
        self.is_ringing : bool
        self.ring_timer : Timer #Time between rings
        self.ring_channel : pygame.mixer.Channel|None
        self.current_call : CallerInfo|None
        self.caller_prompt : TextBox|None
        self.prompts : list[TextBox]
        self.prompt_tweens : dict[str, TweenModule.TweenTrack]
    
    def cleanup_call(self):
        if self.caller_prompt:
            core_object.main_ui.remove(self.caller_prompt)
            self.caller_prompt = None
        self.current_call = None
        self.prompt_tweens.clear()
        for propmt in self.prompts:
            if isinstance(propmt, UiSprite):
                core_object.main_ui.remove(propmt)
        self.prompts.clear()
        
    
    def separate_telephone(self):
        self.phone_part_seprated = True
        self.top_part.visible = True
        self.image = Telephone.no_phone_image
        self.rect = self.image.get_rect(midbottom = self.rect.midbottom)
    
    def reunite_telephone(self):
        self.phone_part_seprated = False
        self.top_part.visible = False
        self.image = Telephone.full_image
        self.rect = self.image.get_rect(midbottom = self.rect.midbottom)

    @classmethod
    def spawn(cls, pos : pygame.Vector2):
        new_part = cls.inactive_elements[0]
        cls.unpool(new_part)
        new_part.image = Telephone.full_image
        new_part.rect = new_part.image.get_rect(center = round(pos))
        new_part.position = pos
        new_part.zindex = 200

        new_part.phone_part_seprated = True
        new_part.is_ringing = False
        new_part.ring_timer = Timer(0)

        new_part.current_call = None
        new_part.caller_prompt = None
        new_part.prompts = []
        new_part.prompt_tweens = {}

        top_part_pos = pos + pygame.Vector2(-120, 48)
        new_part.top_part = TelephoneTopPart.spawn(top_part_pos, new_part)
        new_part.top_part.reset()
        new_part.top_part.visible = False
        
        new_part.separate_telephone()
        return new_part
    @classmethod
    def cleanup_cls(cls):
        for element in cls.active_elements:
            element.stop_ringing()
    
    def update(self, delta : float):
        for key in self.prompt_tweens:
            tween = self.prompt_tweens[key]
            if tween is None: continue
            if tween.has_finished: self.prompt_tweens[key] = None
        if self.current_call:
            if not self.current_call.has_ended:
                self.current_call.update()
        if not self.is_ringing: return
        if self.ring_timer.isover():
            self.ring_channel = core_object.bg_manager.play_sfx(Telephone.short_ring_sfx, 0.15)
            self.ring_timer.set_duration(3)
            self.top_part.start_shake()
        elif self.ring_channel.get_busy() == False:
            if self.top_part.is_shaking:
                self.top_part.end_shake()
    
    def draw(self, display : pygame.Surface):
        #print('hi')
        display.blit(self.image, self.rect)
    
    def start_ringing(self):
        self.ring_channel = core_object.bg_manager.play_sfx(Telephone.short_ring_sfx, 0.15)
        self.separate_telephone()
        self.is_ringing = True
        self.top_part.cancel_shake()
        self.top_part.start_shake()
        self.ring_timer.set_duration(3)
    
    def stop_ringing(self):
        self.is_ringing = False
        self.top_part.cancel_shake()
        self.ring_timer.set_duration(0)
        if self.ring_channel:
            self.ring_channel.stop()
            self.ring_channel = None

    def on_click(self, event : pygame.Event):

        if self.is_ringing and self.current_call:
            self.stop_ringing()
            self.current_call.start_call()
            self.top_part.goto_side() 

    def show_client_response(self, text : str):
        if core_object.game.active == False: return
        if self.caller_prompt is None:
            img = Telephone.green_outline_textbox_image
            self.caller_prompt = TextBox(img, img.get_rect(midright = (-1, Telephone.PROMPT_START_HEIGHT)), 0, text, 'caller_textbox', 
                                         text_settings=(Telephone.font_35, 'Black', False), 
                                         text_alingment=(pygame.Vector2(10,15), round(640 * Telephone.PROMPT_SCALE), 50))
            core_object.main_ui.add(self.caller_prompt)
        self.caller_prompt.text = text
        self.caller_prompt.rect.midright = (-1, Telephone.PROMPT_START_HEIGHT)
        self.caller_prompt.text_progress = 1
        self.caller_prompt.text = text
        self.caller_prompt.position = pygame.Vector2(self.caller_prompt.rect.center)
        target_midleft = pygame.Vector2(0, Telephone.PROMPT_START_HEIGHT)
        target_pos = target_midleft - self.caller_prompt.rect.midleft + self.caller_prompt.position
        new_tween = TweenModule.new_tween(self.caller_prompt, TweenModule.TweenInfo(interpolation.smoothstep, 0.4), 
                              {'position' : target_pos, 'rect.midleft' : target_midleft}, time_source=core_object.game.game_timer.get_time)
        self.prompt_tweens['show_caller_textbox'] = new_tween
        opposite_tween = self.prompt_tweens.get('hide_caller_textbox', None)
        if opposite_tween:
            opposite_tween.destroy()

        if self.caller_prompt not in core_object.main_ui.complete_list or self.caller_prompt not in core_object.main_ui.elements:
            core_object.main_ui.add(self.caller_prompt)
        self.caller_prompt._render()
        
        
    
    def hide_client_response(self):
        if self.caller_prompt is None: return
        self.caller_prompt.position = pygame.Vector2(self.caller_prompt.rect.center)
        target_midright = pygame.Vector2(0, self.caller_prompt.rect.centery)
        target_pos = target_midright - self.caller_prompt.rect.midright + self.caller_prompt.position
        new_tween = TweenModule.new_tween(self.caller_prompt, TweenModule.TweenInfo(interpolation.smoothstep, 0.4), 
                              {'position' : target_pos, 'rect.midright' : target_midright}, time_source=core_object.game.game_timer.get_time)

        self.prompt_tweens['hide_caller_textbox'] = new_tween
        opposite_tween = self.prompt_tweens.get('show_caller_textbox', None)
        if opposite_tween:
            opposite_tween.destroy()
    
    def show_prompts(self, options : list[str]):
        if core_object.game.active == False: return
        self.clear_prompts()
        self.prompts = [None for _ in options]
        for i, option in enumerate(options):
            y_pos : int = (Telephone.PROMPT_START_HEIGHT + 20) + (i + 1) * (200 * Telephone.PROMPT_SCALE)
            img = Telephone.dark_blue_outline_textbox_image
            new_prompt = TextBox(img, img.get_rect(midright = (-1, y_pos)), 0, option, f'prompt{i}', 
                                        text_settings=(Telephone.font_35, 'Black', False), 
                                        text_alingment=(pygame.Vector2(10,15), round(640 * Telephone.PROMPT_SCALE), 50))
            core_object.main_ui.add(new_prompt)
            new_prompt.text = option
            new_prompt.rect.midright = (-1, y_pos)
            new_prompt.text_progress = 1
            new_prompt.text = option
            new_prompt.position = pygame.Vector2(new_prompt.rect.center)
            target_midleft = pygame.Vector2(0, y_pos)
            target_pos = target_midleft - new_prompt.rect.midleft + new_prompt.position
            new_tween = TweenModule.new_tween(new_prompt, TweenModule.TweenInfo(interpolation.smoothstep, 0.4), 
                                {'position' : target_pos, 'rect.midleft' : target_midleft}, time_source=core_object.game.game_timer.get_time)
            self.prompt_tweens[f'show_prompt{i}'] = new_tween
            opposite_tween = self.prompt_tweens.get(f'hide_prompt{i}', None)
            if opposite_tween:
                opposite_tween.destroy()

            if new_prompt not in core_object.main_ui.complete_list or new_prompt not in core_object.main_ui.elements:
                core_object.main_ui.add(new_prompt)
            new_prompt._render()
            self.prompts[i] = new_prompt

    def hide_prompt(self, prompt_index : int):
        if prompt_index >= len(self.prompts): return
        prompt = self.prompts[prompt_index]
        prompt.position = pygame.Vector2(prompt.rect.center)
        target_midright = pygame.Vector2(0, prompt.rect.centery)
        target_pos = target_midright - prompt.rect.midright + prompt.position
        new_tween = TweenModule.new_tween(prompt, TweenModule.TweenInfo(interpolation.smoothstep, 0.4), 
                              {'position' : target_pos, 'rect.midright' : target_midright}, time_source=core_object.game.game_timer.get_time)

        self.prompt_tweens[f'show_prompt{prompt_index}'] = new_tween
        opposite_tween = self.prompt_tweens.get(f'hide_prompt{prompt_index}', None)
        if opposite_tween:
            opposite_tween.destroy()

    def hide_prompts(self):
        prompt : TextBox
        for i, prompt in enumerate(self.prompts):
            self.hide_prompt(i)

    def clear_prompts(self):
        for prompt in self.prompts:
            core_object.main_ui.remove(prompt)
        self.prompts.clear()

    @classmethod
    def handle_mouse_event(cls, event: pygame.Event):
        if core_object.game.state == core_object.game.STATES.transition: return
        if event.type != pygame.MOUSEBUTTONDOWN: return
        press_pos : tuple[int, int] = event.pos
        for telephone in cls.active_elements:
            if not telephone.current_call: continue
            for i, prompt in enumerate(telephone.prompts):
                if prompt.rect.collidepoint(press_pos):
                    telephone.current_call.on_choice_made(i)
                    break
    
    @classmethod
    def handle_key_event(cls, event : pygame.Event):
        if core_object.game.state == core_object.game.STATES.transition: return
        if event.type != pygame.KEYDOWN: return
        conversion_dict = {pygame.K_1 : 0, pygame.K_2 : 1 ,pygame.K_3 : 2, pygame.K_4 : 3, pygame.K_5 : 4, pygame.K_6 : 5, pygame.K_7 : 6}
        index = conversion_dict.get(event.key, None)
        if index is None: return
        for telephone in cls.active_elements:
            if not telephone.current_call: continue
            telephone.current_call.on_choice_made(index)

    @classmethod
    def handle_sprite_clicked_event(cls, event : pygame.Event):
        if core_object.game.state == core_object.game.STATES.transition: return
        if event.type != Sprite.SPRITE_CLICKED: return
        target : Telephone|TelephoneTopPart = event.main_hit
        if isinstance(target, (Telephone, TelephoneTopPart)):
            target.on_click(event)
    
    def new_call(self, call_data : dict[str, Any]):
        if self.current_call: return
        self.current_call = CallerInfo(call_data, self)
        self.current_call.start_waiting()
        self.start_ringing()

Sprite.register_class(Telephone)

class TelephoneTopPart(Sprite):
    inactive_elements : list['TelephoneTopPart'] = []
    active_elements : list['TelephoneTopPart'] = []

    #image = pygame.image.load_sized_svg(r'assets/graphics/tasks/phone/telehpone_top.svg', (300, 300)).convert_alpha()
    image = pygame.image.load(r'assets/graphics/tasks/phone/telephone_top.png').convert()
    image = pygame.transform.scale_by(image, 200.3 / image.get_width())
    image.set_colorkey((0, 0, 0))
    def __init__(self) -> None:
        super().__init__()
        TelephoneTopPart.inactive_elements.append(self)

        self.visible : bool
        self.base_part : Telephone
        self.is_shaking : bool
        self.shake_timer : Timer
        self.shake_tween : TweenModule.TweenTrack|None
        self.pivot : Pivot2D
        
    @classmethod
    def spawn(cls, pos : pygame.Vector2, base : Telephone):
        new_part = cls.inactive_elements[0]
        cls.unpool(new_part)
        new_part.image = TelephoneTopPart.image
        new_part.rect = new_part.image.get_rect(center=round(pos))
        new_part.position = pos
        new_part.pivot = Pivot2D(pos.copy())
        new_part.zindex = 201
        new_part.visible = False
        new_part.pivot.angle = 0
        new_part.base_part = base
        new_part.is_shaking = False
        new_part.shake_tween = None
        new_part.shake_timer = Timer(0)
        return new_part

    def cancel_shake(self):
        self.is_shaking = False
        self.shake_timer.set_duration(0)
        if self.shake_tween:
            self.shake_tween.destroy()
            self.shake_tween = None
        self.reset()
    
    def end_shake(self):
        self.is_shaking = False
        self.shake_timer.set_duration(0)
        new_pivot = self.base_part.position + pygame.Vector2(0, -52)
        if self.shake_tween:
            self.shake_tween.destroy()
            self.shake_tween = None
        self.set_angle(0)

        TweenModule.new_tween(self, TweenModule.TweenInfo(interpolation.cubic_ease_out, 0.1), {'pivot.origin' : new_pivot}, 
                              time_source=core_object.game.game_timer.get_time)
    def start_shake(self, shake_speed = 1):
        self.shake_timer.set_duration(0.2 / shake_speed)
        self.is_shaking = True
        self.shake_tween = TweenModule.new_tween(self, TweenModule.TweenInfo(interpolation.cubic_ease_out, 0.1), 
                                                 {'pivot.origin' : self.pivot.origin + pygame.Vector2(0, -20)}, 
                                                 time_source=core_object.game.game_timer.get_time)

    def update(self, delta : float):
        if not self.is_shaking or not self.shake_timer.duration: 
            self.position = self.pivot.position
            self.rect.center = round(self.position)
            return
        shake_progress = self.shake_timer.get_time() / self.shake_timer.duration
        self.set_angle(self.get_angle(shake_progress))
    
    @staticmethod
    def get_angle(shake_progress : float):
        cycle_progress = shake_progress % 1
        if cycle_progress <= 0.5:
            return -15
        else:
            return 15

    
    def on_click(self, event : pygame.Event):
        telephone = self.base_part
        telephone.on_click(event)

    def reset(self):
        self.set_angle(0)
        self.pivot.origin = self.base_part.position + pygame.Vector2(0, -52)
        self.position = self.pivot.position
        self.rect.center = round(self.position)
        #25

    def goto_side(self):
        self.set_angle(-90)
        self.pivot.origin = self.base_part.position + pygame.Vector2(-120, 48)
        self.position = self.pivot.position
        self.rect.center = round(self.position)

    def set_angle(self, angle : float):
        self.pivot.angle = angle
        self.image, self.rect, self.position = self.pivot.rotate_image(TelephoneTopPart.image)

    def rotate(self, angle : float):
        self.pivot.angle += angle
        self.image, self.rect, self.position = self.pivot.rotate_image(TelephoneTopPart.image)

    def draw(self, display: pygame.Surface):
        if not self.visible: return
        #print('hi')
        display.blit(self.image, self.rect)

Sprite.register_class(TelephoneTopPart)

class CallerInfo:
    CALL_ENDED : int = pygame.event.custom_type()
    with open(r'assets/data/phone/phone_calls.json', 'r') as openfile:
        complete_data : dict[str, list[dict[str, Any]]] = json.load(openfile)
    all_calls : list[dict[str, Any]] = []
    
    @classmethod
    def new_test_call(cls, parent : Telephone):
        call_data = random.choice(cls.complete_data['Normal'])
        return CallerInfo(call_data, parent)

    @classmethod
    def get_call(cls, name : str) -> dict[str, Any]|None:
        for call in cls.all_calls:
            if call.get("CallName", None) == name:
                return call
        return None

    def __init__(self, call_data : dict, parent : Telephone) -> None:
        self.wait_timer : Timer = Timer(call_data.get('WaitPatience', 10))
        self.patience_timer : Timer = Timer(call_data.get('CallPatience', 10))
        self.call_timer : Timer = Timer(0)
        self.current_node : str = call_data.get('CallStartNode', '0')
        self.dialouge_tree : dict[str, tuple[str, dict[str,str]|str]] = call_data['CallerTree']
        self.call_type : str = call_data['CallType']
        self.call_name : str|None = call_data['CallName']
        self.caller_behavior : Callable[[CallerInfo, str|None], None] = getattr(CallerBehavior, call_data['CallerBehavior'])
        self.special_nodes : dict[str , str] = call_data.get('SpecialNodes', None) or {}
        self.telephone = parent
        self.response_timer : dict[Timer, str] = {}
        self.options_timer : dict[Timer, list[str]] = {}
        self.has_ended = False
        self.call_active = False
        self.can_progress_call = False
        self.is_waiting = False
    
    def on_choice_made(self, choice_index : int):
        if not self.call_active: return
        response, options = self.dialouge_tree[self.current_node]
        if type(options) != dict: return
        true_options = list(options.keys())
        if choice_index >= len(true_options): return
        option_chosen = true_options[choice_index]
        self.progress_call(option_chosen)
    
    def update(self):
        if self.call_active == False:
            if self.is_waiting:
                if self.wait_timer.isover():
                    self.telephone.stop_ringing()
                    self.end_call(False, 'You took too long to pick up!')
            return
        if self.patience_timer.isover():
            self.end_call(False, 'You took too long to awnser!')
            return
        to_del = []
        for timer in self.response_timer:
            if timer.isover():
                self.telephone.show_client_response(self.response_timer[timer])
                to_del.append(timer)
        for timer in to_del:
            self.response_timer.pop(timer)
        
        to_del.clear()
        for timer in self.options_timer:
            if timer.isover():
                self.telephone.show_prompts(self.options_timer[timer])
                to_del.append(timer)
        for timer in to_del:
            self.options_timer.pop(timer)

    def progress_call(self, choice : str|None):
        if not self.can_progress_call: return
        self.patience_timer.restart()
        self.caller_behavior(self, choice)
    
    def start_waiting(self):
        self.wait_timer.restart()
        self.is_waiting = True
    
    def start_call(self):
        self.wait_timer.pause()
        self.call_timer.restart()
        self.patience_timer.restart()
        self.call_active = True
        self.can_progress_call = True
        self.progress_call(None)
    
    def end_call(self, success : bool, final_text : str|None = None):
        new_event = pygame.event.Event(CallerInfo.CALL_ENDED, {'success' : success, 'telephone' : self.telephone, 'call' : self})
        pygame.event.post(new_event)
        if final_text:
            self.telephone.hide_client_response()
            core_object.task_scheduler.schedule_task(0.5, self.telephone.show_client_response, final_text)

        core_object.task_scheduler.schedule_task(2.5, self.telephone.hide_client_response)
        core_object.task_scheduler.schedule_task(3.1, self.telephone.cleanup_call)
        self.telephone.hide_prompts()
        self.options_timer.clear()
        self.response_timer.clear()
        self.call_active = False
        self.has_ended = True
        self.telephone.top_part.cancel_shake()
        self.telephone.top_part.reset()
        

    def abort_call(self):
        pass
    
for category in CallerInfo.complete_data:
    CallerInfo.all_calls += CallerInfo.complete_data[category]

class CallerBehavior:
    @staticmethod
    def normal(self : CallerInfo, choice : str|None):
        if self.call_active == False: return
        if choice is None:

            if self.current_node in self.special_nodes:
                pass
                
            response, options = self.dialouge_tree[self.current_node]
            true_options = list(options.keys())
            delay_timer1 = Timer(0)
            delay_timer2 = Timer(0.4)
            
            self.response_timer[delay_timer1] = response
            self.options_timer[delay_timer2] = true_options
        else:
            current_options = self.dialouge_tree[self.current_node][1]
            if type(current_options) != dict:
                if type(current_options) == str:
                    match current_options:
                        case "Sucess"|"Success":
                            end_text = self.dialouge_tree[self.current_node][0]
                            self.end_call(True, end_text)
                            return
                        case "Fail":
                            end_text = self.dialouge_tree[self.current_node][0]
                            self.end_call(False, end_text)
                            return
            else:
                result = current_options[choice]
                if result in self.special_nodes:
                    pass
                    
                self.current_node = result
                
                
                response, options = self.dialouge_tree[self.current_node]
                if type(options) == str:
                    match options:
                        case "Sucess"|"Success":
                            end_text = self.dialouge_tree[self.current_node][0]
                            self.end_call(True, end_text)
                            return
                        case "Fail":
                            end_text = self.dialouge_tree[self.current_node][0]
                            self.end_call(False, end_text)
                            return
                        
                self.telephone.hide_client_response()
                self.telephone.hide_prompts()
                true_options = list(options.keys())
                delay_timer1 = Timer(0.5)
                delay_timer2 = Timer(0.9)
                
                self.response_timer[delay_timer1] = response
                self.options_timer[delay_timer2] = true_options
                self.can_progress_call = False
                core_object.task_scheduler.schedule_task(delay_timer2.duration, setattr, self, 'can_progress_call', True)