import pygame
from typing import Any
from math import floor
from random import shuffle, choice
import random
import utils.tween_module as TweenModule
from utils.ui_sprite import UiSprite
from utils.textbox import TextBox
from utils.textsprite import TextSprite
from utils.base_ui_elements import BaseUiElements
import utils.interpolation as interpolation
from utils.my_timer import Timer
from game.sprite import Sprite
from utils.helpers import average, random_float
from utils.brightness_overlay import BrightnessOverlay

class GameStates:
    def __init__(self) -> None:
        self.transition = 'Transition'
        self.normal = 'Normal'


class Game:
    font_40 = pygame.Font('assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.Font('assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.Font('assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.Font('assets/fonts/Pixeltype.ttf', 70)
    
    def __init__(self) -> None:
        self.active : bool = False
        self.game_state : None|str = None
        self.day_timer : Timer = None
        self.day : int = None
        self.game_data : dict = {}
        self.main_textbox : TextBox|None = None
        self.doing_tutorial : bool |None = None
        self.tutorial_end_timestamp : float|None = None
        self.tutorial_skip_time : float = 0
        self.tutorial_timings : list|None = None
        self.timer_sprite : TextSprite = TextSprite(pygame.Vector2(-500, -500), 'center', 0, 'Time : 0', 'timer', None, None, 0,
                                (Game.font_60, 'Gold', False), ('Black', 2), colorkey=(255, 0,0))
        self.textbox_image = pygame.transform.scale_by(TextBox.main_image, 0.75)

        self.STATES : GameStates = GameStates()

        self.telephone : game.tasks.phone.Telephone|None = None
        self.folders : list[game.tasks.draggable_letter.LetterFolder]|None = None
        self.piles : list[game.tasks.draggable_letter.LetterPile]|None = None

        self.call_history : list[game.tasks.phone.CallerInfo]|None = None
        self.letter_history : list[game.tasks.draggable_letter.LetterInfo]|None = None

        self.letters_sorted : int|None = None
        self.letters_failed : int|None = None
        self.total_letters_sorted : int|None = None

        self.total_calls_ended : int|None = None
        self.calls_failed : int|None = None
        self.sucessful_calls : int|None = None


    

    def start_day(self, day : int):
        self.active= True
        self.day = day
        self.game_state = self.STATES.normal
        self.doing_tutorial : bool|None = True
        self.tutorial_end_timestamp = None
        self.game_data = {}
        
        self.timer_sprite.text = 'Time : 0'
        self.timer_sprite.rect.midtop = (480, 15)
        self.timer_sprite.position = pygame.Vector2(self.timer_sprite.rect.center)
        self.timer_sprite.visible = False
        core_object.main_ui.add(self.timer_sprite)

        window_size = core_object.main_display.get_size()
        new_textbox = TextBox(self.textbox_image, self.textbox_image.get_rect(bottomleft =(50, window_size[1] - 50)), 1, '', 'main_textbox', True, 
                                  zindex=50, text_settings= (TextBox.main_font, 'Black', False), text_alingment= (pygame.Vector2(20, 20), 470, 5))
        new_textbox.visible = False
        new_textbox.text_progress = 0
        core_object.main_ui.add(new_textbox)
        self.main_textbox = new_textbox

        LetterPile = game.tasks.draggable_letter.LetterPile
        LetterFolder = game.tasks.draggable_letter.LetterFolder
        SortingCriteria = game.tasks.draggable_letter.SortingCriteria
        LetterInfo = game.tasks.draggable_letter.LetterInfo
        
        self.letters_sorted = 0
        self.letters_failed = 0
        self.total_letters_sorted = 0

        self.total_calls_ended = 0
        self.calls_failed = 0
        self.sucessful_calls = 0

        self.letter_history = []
        self.call_history = []

        if day == 1:
            self.day_timer = Timer(0)
            pile = LetterPile.spawn(pygame.Vector2(825, 405))
            folder1 = LetterFolder.spawn(pygame.Vector2(150, -200), SortingCriteria.is_category, {'target_type' : 'Spam'}, 
                            'Spam', (Game.font_40, 'Black', False))
            folder2 = LetterFolder.spawn(pygame.Vector2(450, -200), SortingCriteria.dosent_fit, {'other_folders' : [folder1]}, 
                            'Other', (Game.font_40, 'Black', False))
            telephone = game.tasks.phone.Telephone.spawn(pygame.Vector2(850, -200))
            telephone.reunite_telephone()
            
            order = ['Business', 'Spam']
            shuffle(order)
            self.game_data['spawn_order'] = [LetterInfo.random(categories={order[0] : 1}), LetterInfo.random(categories={order[1] : 1})]
            self.game_data['letters_spawned'] = 0
            self.piles = [pile]
            self.folders = [folder1, folder2] 
            self.telephone = telephone
            
            self.game_data['current_tutorial_step'] = -1
            self.game_data['current_textbox_tween'] = None
            self.game_data['other_tweens'] = {}
            self.tutorial_end_timestamp = None
            self.tutorial_skip_time = 0
            self.tutorial_timings = [4, 12, 19, 25, 32, 35]
            self.game_data['call_target'] = 4
            self.game_data['next_call_timer'] = Timer(10)
            self.game_data['next_call_interval'] = [5, 5]
            self.game_data['got_scammed'] = 0

    def connect_taks(self):
        LetterPile = game.tasks.draggable_letter.LetterPile
        LetterFolder = game.tasks.draggable_letter.LetterFolder
        DraggableLetter = game.tasks.draggable_letter.DraggableLetter
        
        #game module connections
        core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event_tutorial)

        #letter task connections
        core_object.event_manager.bind(Sprite.SPRITE_CLICKED, DraggableLetter.handle_mouse_event)
        core_object.event_manager.bind(pygame.MOUSEBUTTONUP, DraggableLetter.handle_mouse_event)
        core_object.event_manager.bind(pygame.FINGERUP, DraggableLetter.handle_mouse_event)
        core_object.event_manager.bind(pygame.FINGERDOWN, DraggableLetter.handle_mouse_event)

        core_object.event_manager.bind(Sprite.SPRITE_CLICKED, LetterPile.handle_mouse_event)

        #phone task connections
        core_object.event_manager.bind(Sprite.SPRITE_CLICKED, game.tasks.phone.Telephone.handle_sprite_clicked_event)
        core_object.event_manager.bind(pygame.KEYDOWN, game.tasks.phone.Telephone.handle_key_event)
        core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, game.tasks.phone.Telephone.handle_mouse_event)

        #task to game module connections
        core_object.event_manager.bind(DraggableLetter.LETTER_RELEASED, LetterFolder.handle_letter_release_event)
        core_object.event_manager.bind(LetterFolder.LETTER_SORTED, LetterFolder.handle_letter_sorted_event)
        core_object.event_manager.bind(LetterFolder.LETTER_SORTED, self.handle_task_event)
        core_object.event_manager.bind(game.tasks.phone.CallerInfo.CALL_ENDED, self.handle_task_event)

    def disconnect_tasks(self):
        LetterPile = game.tasks.draggable_letter.LetterPile
        LetterFolder = game.tasks.draggable_letter.LetterFolder
        DraggableLetter = game.tasks.draggable_letter.DraggableLetter

        #game module connections
        core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event_tutorial)

        #letter task connections
        core_object.event_manager.unbind(Sprite.SPRITE_CLICKED, DraggableLetter.handle_mouse_event)
        core_object.event_manager.unbind(pygame.MOUSEBUTTONUP, DraggableLetter.handle_mouse_event)
        core_object.event_manager.unbind(pygame.FINGERUP, DraggableLetter.handle_mouse_event)
        core_object.event_manager.unbind(pygame.FINGERDOWN, DraggableLetter.handle_mouse_event)
        
        core_object.event_manager.unbind(Sprite.SPRITE_CLICKED, LetterPile.handle_mouse_event)

        #phone task connections
        core_object.event_manager.unbind(Sprite.SPRITE_CLICKED, game.tasks.phone.Telephone.handle_sprite_clicked_event)
        core_object.event_manager.unbind(pygame.KEYDOWN, game.tasks.phone.Telephone.handle_key_event)
        core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, game.tasks.phone.Telephone.handle_mouse_event)

        #task to game module connections and intertask connections
        core_object.event_manager.unbind(DraggableLetter.LETTER_RELEASED, LetterFolder.handle_letter_release_event)
        core_object.event_manager.unbind(LetterFolder.LETTER_SORTED, LetterFolder.handle_letter_sorted_event)
        core_object.event_manager.unbind(LetterFolder.LETTER_SORTED, self.handle_task_event)
        core_object.event_manager.unbind(game.tasks.phone.CallerInfo.CALL_ENDED, self.handle_task_event)   

    def game_start_fadein(self, delay : float = 2, fadein_lentgh = 1.5):
        window_size = core_object.main_display.get_size()
        overlay = BrightnessOverlay(0, pygame.Rect(0,0, *core_object.main_display.get_size()), 0, 'overlay', zindex=99)

        overlay.brightness = -255
        core_object.main_ui.add_temp(overlay, delay + fadein_lentgh + 0.5)
        TI = TweenModule.TweenInfo
        tween_chain = TweenModule.TweenChain(overlay, [(TweenModule.TweenInfo(interpolation.linear, delay), {}), 
                                                    (TI(interpolation.linear, fadein_lentgh), {'brightness' : 0})])
        tween_chain.has_finished = False
        TweenModule.TweenChain.elements.append(tween_chain)
        tween_chain.play()

    def show_day(self, day : int):
        centerx = core_object.main_display.get_width() // 2
        centery = core_object.main_display.get_height() // 2
        
        day_sprite = BaseUiElements.new_text_sprite(f'Day : {day}', (Game.font_60, 'White', False), 0, 'midbottom', (centerx, -5), keep_og_surf=True)
        finaly = day_sprite.surf.get_height() + core_object.main_display.get_height()
        day_sprite.zindex = 200
        TI = TweenModule.TweenInfo
        chain = TweenModule.TweenChain(day_sprite, [(TI(interpolation.quad_ease_out, 0.5), {'position.y' : centery, 'rect.centery' : centery}),
                                            (TI(lambda t:t, 1), {'position.y' : centery, 'rect.centery' : centery}),
                                            (TI(interpolation.quad_ease_in, 1.5), {'position.y' : finaly, 'rect.centery' : finaly})])
        TweenModule.TweenChain.elements.append(chain)
        chain.play()
        core_object.main_ui.add_temp(day_sprite, 3)
 
    

    def main_logic(self, delta : float):
        LetterInfo = game.tasks.draggable_letter.LetterInfo
        CallerInfo = game.tasks.phone.CallerInfo
        current_time = self.day_timer.get_time()
        if self.day == 1:
            if self.game_state == self.STATES.transition: return
            if self.tutorial_end_timestamp:
                self.day1_game_logic()
            else:
                self.day1_tutorial_logic()
    
    def day1_tutorial_logic(self):
        curr_step = self.game_data['current_tutorial_step']
        current_time = self.day_timer.get_time()
        if curr_step < 5:
            if current_time + self.tutorial_skip_time > self.tutorial_timings[curr_step + 1]:
                self.game_data['current_tutorial_step'] += 1
                self.day1_tutorial_step(self.game_data['current_tutorial_step'])
    
    def day1_game_logic(self):
        current_time = self.day_timer.get_time()
        real_time = current_time - self.tutorial_end_timestamp

        rounded_time_str = f'Time : {floor(real_time)}'
        if self.timer_sprite.text != rounded_time_str:
            self.timer_sprite.text = rounded_time_str
        
        if real_time > 300: self.game_end_transition()
            
        self.day1_letter_logic()
        self.day1_phone_logic()
    
    def day1_letter_logic(self,):
        current_time = self.day_timer.get_time()
        real_time = current_time - self.tutorial_end_timestamp
        LetterInfo = game.tasks.draggable_letter.LetterInfo
        if (real_time + 4) // 5 > self.game_data['letters_spawned']:
            pile : game.tasks.draggable_letter.LetterPile = self.piles[0]
            next_letter : game.tasks.draggable_letter.LetterInfo
            if self.game_data['spawn_order']:
                next_letter = self.game_data['spawn_order'][0]
                self.game_data['spawn_order'].pop(0)
            else:
                if self.game_data['letters_spawned'] != 3:
                    while True:
                        call_data = random.choice(LetterInfo.all_messages)
                        if not call_data.get('unique', False):
                            break
                else:
                    call_data = LetterInfo.get_data_by_name("BusinessReport")
                next_letter = LetterInfo.from_message(call_data)
            
            pile.stack.append(next_letter)
            self.game_data['letters_spawned'] += 1
    
    def day1_phone_logic(self):
        telephone : game.tasks.phone.Telephone = self.telephone
        CallerInfo = game.tasks.phone.CallerInfo
        if not self.game_data['next_call_timer'].isover(): return
        if telephone.current_call: return
        new_call_data = choice(CallerInfo.complete_data['Normal'])
        call_name = new_call_data.get("CallName", None)
        if call_name == "PrinterProblem":
            printer_problem_call = self.get_call_from_history("PrinterProblem")
            if printer_problem_call:
                repeat_call = self.get_call_from_history("PrinterProblemRepeat")
                if not repeat_call:
                    new_call_data = CallerInfo.get_call("PrinterProblemRepeat")
                else:
                    while True:
                        new_call_data = choice(CallerInfo.complete_data['Normal'])
                        if new_call_data.get("CallName", None) not in ["PrinterProblem", "PrinterProblemRepeat"]:
                            break
        elif call_name == 'CreditScam':
            if self.game_data['got_scammed']:
                new_call_data = CallerInfo.get_call('CreditScamRepeat')
        elif call_name == 'CreditScamRepeat':
            if not self.game_data['got_scammed']:
                new_call_data = CallerInfo.get_call('CreditScam')


        telephone.new_call(new_call_data)
        self.game_data['next_call_timer'].set_duration(-1)
   
    def day1_tutorial_step(self, step : int):
        folders : list[game.tasks.draggable_letter.LetterFolder] = self.folders
        folder1, folder2 = folders[0], folders[1]
        telephone : game.tasks.phone.Telephone = self.telephone
        TI = TweenModule.TweenInfo
        if step == 0:
            self.main_textbox.text_progress = 0
            self.main_textbox.text = 'Welcome to the office! Here you will be doing a variety of tasks. For today, you will be sorting letters.'
            self.main_textbox.visible = True
            text_len = len(self.main_textbox.text)
            new_tween = TweenModule.new_tween(self.main_textbox, TI(interpolation.linear, 0.05 * text_len), {'text_progress' : 1})
            self.game_data['current_textbox_tween'] = new_tween
        elif step == 1:
            self.main_textbox.rect.midtop = (470, 15)
            self.main_textbox.position = pygame.Vector2(self.main_textbox.rect.center)
            self.main_textbox.text_progress = 0
            self.main_textbox.text = "The process is quite simple for now. Any spam related letter goes in the 'spam' folder."
            text_len = len(self.main_textbox.text)
            new_tween = TweenModule.new_tween(self.main_textbox, TI(interpolation.linear, 0.05 * text_len), {'text_progress' : 1})
            folder_tween = TweenModule.new_tween(folder1, TI(interpolation.smoothstep, 1), {'rect.centery' : 450, 'position.y' : 450})
            self.game_data['current_textbox_tween'] = new_tween
            self.game_data['other_tweens']['folder1'] = folder_tween
        elif step == 2:
            self.main_textbox.text_progress = 0
            self.main_textbox.text = '''Every other letter goes in the 'other' folder. Make sure those letters dont pile up, else you might get a penalty.'''
            text_len = len(self.main_textbox.text)
            new_tween = TweenModule.new_tween(self.main_textbox, TI(interpolation.linear, 0.05 * text_len), {'text_progress' : 1})
            folder_tween = TweenModule.new_tween(folder2, TI(interpolation.quad_ease_out, 1), {'rect.centery' : 450, 'position.y' : 450})
            self.game_data['other_tweens']['folder1'] = None
            self.game_data['other_tweens']['folder2'] = folder_tween
            self.game_data['current_textbox_tween'] = new_tween
        elif step == 3:
            self.main_textbox.text_progress = 0
            self.main_textbox.text = '''One more thing. During your time here, you're going to have to awnser to phone a few times. Today, we want atleast 4 calls awnsered or you are getting a penalty.'''
            text_len = len(self.main_textbox.text)
            new_tween = TweenModule.new_tween(self.main_textbox, TI(interpolation.linear, 0.05 * text_len), {'text_progress' : 1})
            telephone_tween = TweenModule.new_tween(telephone, TI(interpolation.quad_ease_out, 1), {'rect.centery' : 115, 'position.y' : 115})
            self.game_data['other_tweens']['folder2'] = None
            self.game_data['other_tweens']['telephone'] = telephone_tween
            self.game_data['current_textbox_tween'] = new_tween
        elif step == 4:
            self.main_textbox.rect.midtop = (470, 15)
            self.main_textbox.position = pygame.Vector2(self.main_textbox.rect.center)
            self.main_textbox.text_progress = 0
            self.main_textbox.text = '''Good luck!'''
            text_len = len(self.main_textbox.text)
            new_tween = TweenModule.new_tween(self.main_textbox, TI(interpolation.linear, 0.05 * text_len), {'text_progress' : 1})
            self.game_data['current_textbox_tween'] = new_tween
            self.game_data['other_tweens']['telephone'] = None

        elif step == 5:
            self.end_day1_tutorial()
    
    def end_day1_tutorial(self):
        self.set_new_tutorial_end_timestamp()
        self.main_textbox.visible = False
        self.timer_sprite.visible = True
        self.game_data['next_call_timer'].set_duration(4)



    def handle_task_event(self, event : pygame.Event):
        LetterFolder = game.tasks.draggable_letter.LetterFolder
        DraggableLetter = game.tasks.draggable_letter.DraggableLetter
        if event.type == LetterFolder.LETTER_SORTED:
            if self.game_state == self.STATES.transition: return
            folder : game.tasks.draggable_letter.LetterFolder = event.folder
            letter : game.tasks.draggable_letter.DraggableLetter = event.letter
            result = folder.sorting_criteria(folder, letter)

            self.total_calls_ended +=1 
            if result:
                self.letters_sorted += 1
            else:
                self.letters_failed += 1
                self.show_letter_sort_error()

            self.letter_history.append(letter.data)

        elif event.type == game.tasks.phone.CallerInfo.CALL_ENDED:
            if self.game_state == self.STATES.transition: return
            success : bool = event.success
            call : game.tasks.phone.CallerInfo = event.call
            telephone : game.tasks.phone.Telephone = event.telephone
            if success:
                self.sucessful_calls += 1
            else:
                self.calls_failed += 1
                self.show_phone_call_error()
            self.total_calls_ended += 1

            if self.day == 1:
                a, b = self.game_data['next_call_interval']
                self.game_data['next_call_timer'].set_duration(random_float(a, b))

                if call.call_name in ['CreditScam', 'CreditScamRepeat'] and success == False:
                    self.game_data['got_scammed'] += 200
            
            self.call_history.append(call)

    def show_letter_sort_error(self):
        error_sprite = TextSprite(pygame.Vector2(core_object.main_display.get_width() // 2, 90), 'midtop', 0, 'Wrong folder!', 
                                      text_settings=(core_object.menu.font_50, 'Red', False), text_stroke_settings=('Black', 2), colorkey=(0,255,0))
        
        error_sprite.rect.bottom = -5
        error_sprite.position = pygame.Vector2(error_sprite.rect.center)
        temp_y = error_sprite.rect.centery
        core_object.bg_manager.play_sfx(game.tasks.draggable_letter.LetterFolder.error_sfx, 0.15)
        core_object.main_ui.add_temp(error_sprite, 2)
        TInfo = TweenModule.TweenInfo
        goal1 = {'rect.centery' : 50, 'position.y' : 50}
        info1 = TInfo(interpolation.quad_ease_out, 0.3)
        goal2 = {'rect.centery' : temp_y, 'position.y' : temp_y}
        info2 = TInfo(interpolation.quad_ease_in, 0.4)
        
        on_screen_time = 1
        TweenModule.new_tween(error_sprite, info1, goal1)
        core_object.task_scheduler.schedule_task(0.4 + on_screen_time, TweenModule.new_tween, error_sprite, info2, goal2)
    
    def show_phone_call_error(self):
        error_sprite = TextSprite(pygame.Vector2(core_object.main_display.get_width() // 2, 90), 'midtop', 0, 'Call failed!', 
                                      text_settings=(core_object.menu.font_50, 'Red', False), text_stroke_settings=('Black', 2), colorkey=(0,255,0))
        
        error_sprite.rect.bottom = -5
        error_sprite.position = pygame.Vector2(error_sprite.rect.center)
        temp_y = error_sprite.rect.centery
        core_object.bg_manager.play_sfx(game.tasks.draggable_letter.LetterFolder.error_sfx, 0.15)
        core_object.main_ui.add_temp(error_sprite, 2)
        TInfo = TweenModule.TweenInfo
        goal1 = {'rect.centery' : 50, 'position.y' : 50}
        info1 = TInfo(interpolation.quad_ease_out, 0.3)
        goal2 = {'rect.centery' : temp_y, 'position.y' : temp_y}
        info2 = TInfo(interpolation.quad_ease_in, 0.4)
        
        on_screen_time = 1
        TweenModule.new_tween(error_sprite, info1, goal1)
        core_object.task_scheduler.schedule_task(0.4 + on_screen_time, TweenModule.new_tween, error_sprite, info2, goal2)

    def handle_mouse_event_tutorial(self, event : pygame.Event):
        if event.type != pygame.MOUSEBUTTONDOWN: return
        if not self.active : return
        press_pos : tuple = event.pos
        if self.day == 1:
            if not self.main_textbox : return
            if self.tutorial_end_timestamp : return
            if not self.main_textbox.visible: return
            if self.game_data['current_tutorial_step'] > 4: return
            if not self.main_textbox.rect.collidepoint(press_pos): return
            if self.main_textbox.text_progress != 1:
                self.main_textbox.text_progress = 1
                tween : TweenModule.TweenTrack = self.game_data['current_textbox_tween']
                if tween:
                    tween.stop()
            else:
                if self.game_data['current_tutorial_step'] > 4: return
                self.game_data['current_tutorial_step'] += 1
                self.day1_tutorial_step(self.game_data['current_tutorial_step'])
                normal_timinig : float = self.tutorial_timings[self.game_data['current_tutorial_step']]
                current_time : float = self.day_timer.get_time()
                self.tutorial_skip_time = normal_timinig - current_time

    def get_random_call(self) -> dict[str, Any]:
        return choice(game.tasks.phone.CallerInfo.complete_data['Normal'])
    
    def get_call_from_history(self, name : str):
        for call in self.call_history:
            if call.call_name == name:
                return call
        return None
                    
    def set_textbox_visibilty(self, state : bool):
        if not self.main_textbox: return
        self.main_textbox.visible = state
    
    def set_new_tutorial_end_timestamp(self):
        if not self.day_timer: return
        if self.tutorial_end_timestamp : return
        self.tutorial_end_timestamp = self.day_timer.get_time()
    
  
    def get_result(self) -> dict:
        result = {'tasks' : {}, 'final_percentage' : None}
        if self.day == 1:
            letters_sorted : int = self.letters_sorted
            letters_failed : int  = self.letters_failed
            total_letters_sorted : int  = self.total_letters_sorted
            pile : game.tasks.draggable_letter.LetterPile = self.piles[0]
            letters_left : int = len(pile.stack) + len(game.tasks.draggable_letter.DraggableLetter.active_elements)
            succes = letters_sorted
            if letters_left > 1:
                succes -= (letters_left - 1)
            
            letter_percent : float = pygame.math.clamp(succes / total_letters_sorted, 0, 1) if total_letters_sorted > 0 else 0
            result['tasks']['Letters'] = letter_percent
            total_calls : int = self.total_calls_ended
            bad_calls : int = self.calls_failed
            good_calls : int = self.sucessful_calls
            call_target : int = self.game_data['call_target']
            succes = good_calls
            if good_calls < call_target:
                succes -= (call_target - good_calls)
            phone_percent = pygame.math.clamp(succes / total_calls, 0, 1) if total_calls > 0 else 0

            result['tasks']['Phone'] = phone_percent
            result['final_percentage'] = average([letter_percent, phone_percent])

            result['did_pass'] = True if result['final_percentage'] > 0.6 else False
            letter_money : int = 100
            phone_money : int = -30
            final_money : int = 100 - 30
            money_dict : dict[str, int] = {'Letters' : letter_money, 'Phone' : phone_money}
            if self.game_data['got_scammed']:
                money_dict['Scammed'] = self.game_data['got_scammed']
                final_money -= self.game_data['got_scammed']

            money_dict['Final'] = final_money
            result['Money'] = money_dict
        return result
     
    def game_end_transition(self, failed : bool = False):
        self.game_state = self.STATES.transition
        back_arrow = core_object.main_ui.get_sprite('back_arrow')
        if back_arrow:
            core_object.main_ui.remove(back_arrow)
        core_object.main_ui.remove(self.timer_sprite)
        
        font = core_object.menu.font_150
        new_textsprite : TextSprite
        if not failed:
            new_textsprite = TextSprite(pygame.Vector2(0,0), 'midtop', 0, 'Game!', 'end_message', None, None, 100, 
                                        (font, 'Gold', False), ('Black', 3), colorkey=(0, 255, 0))
        else:
            new_textsprite = TextSprite(pygame.Vector2(0,0), 'midtop', 0, 'Fail!', 'end_message', None, None, 100, 
                                        (font, 'Red', False), ('Black', 3), colorkey=(0, 255, 0))
        
        new_textsprite.rect.midbottom = (core_object.main_display.get_width() // 2, -1)
        new_textsprite.position = pygame.Vector2(new_textsprite.rect.center)
        core_object.main_ui.add(new_textsprite)

        centery = core_object.main_display.get_height() // 2
        TweenModule.new_tween(new_textsprite, TweenModule.TweenInfo(interpolation.smoothstep, 1), 
                              {'rect.centery' : centery, 'position.y' : centery})
        
        overlay = BrightnessOverlay(0, pygame.Rect(0, 0, *core_object.main_display.get_size()), 0, 'game_end_overlay', zindex=99)
        core_object.main_ui.add(overlay)
        TweenModule.new_tween(overlay, TweenModule.TweenInfo(lambda t : t, 1), {'brightness' : -100})

        core_object.task_scheduler.schedule_task(3.5, self.fire_gameover_event, True)
    
    def fire_gameover_event(self, goto_result_screen : bool = True):
        new_event = pygame.event.Event(core_object.END_GAME, {'goto_result_screen': goto_result_screen})
        pygame.event.post(new_event)

    def cleanup(self):
        self.day = None
        self.active = False
        self.day_timer = None
        self.game_state = None
        self.main_textbox = None
        self.doing_tutorial = None

        self.tutorial_end_timestamp = None
        self.tutorial_skip_time = 0
        self.tutorial_timings = None

        self.telephone = None
        self.folders = None
        self.piles = None

        self.call_history = None
        self.letter_history = None

        self.game_data.clear()
        game.tasks.draggable_letter.DraggableLetter.cleanup()
        game.tasks.phone.Telephone.cleanup_cls()
        core_object.main_ui.remove(self.timer_sprite)
         

   
    def init(self):
        global game
        import game.tasks.draggable_letter
        import game.tasks.phone
        global core_object
        from core.core import core_object
    
