import pygame
from time import perf_counter
from collections import deque

from core.event_manger import EventManger
import core.game_module
from core.settings import Settings
from core.bg_manager import BgManager
from core.ui import Ui
from core.menu import Menu
import core.menu
from core.game_module import Game
from core.task_scheduler import TaskScheduler
from utils.tween_module import TweenTrack, TweenChain
class Core:
    CORE_EVENT = pygame.event.custom_type()
    START_GAME = pygame.event.custom_type() #mandatory args: day(int)
    END_GAME = pygame.event.custom_type() #mandatory args: goto_result_screen(bool)
    def __init__(self) -> None:
        self.FPS = 60
        self.PERFORMANCE_MODE = False
        self.main_display : pygame.Surface
        self.brightness_map = pygame.Surface((2000, 2000), pygame.SRCALPHA)
        pygame.draw.rect(self.brightness_map, (255, 255, 255, 0), (0,0, 2000, 2000))
        self.event_manager = EventManger()
        self.event_manager.bound_actions[pygame.QUIT] = [self.close_game]
        self.active_fingers : dict[int, tuple[float, float]] = {}
        self.platform : str = 'Unknown'
        self.dt : float = 1
        self.last_dt_measurment : float = 0

        self.settings = Settings()
        self.bg_manager = BgManager()
        self.main_ui = Ui()
        self.menu = Menu()
        self.game = Game()
        self.task_scheduler = TaskScheduler()
        self.delta_stream : deque[float] = deque([1 for _ in range(30)])
        self.dirty_display_rects : list[pygame.Rect] = []
        self.brightness_map_blend_mode = pygame.BLENDMODE_NONE

    def init(self, main_display : pygame.Surface):
        self.main_display = main_display
    
    def close_game(self, event):
        self.settings.save()
        pygame.quit()
        exit()
    
    def update_dt(self, target_fps : int|float = 60):
        if self.last_dt_measurment == 0:
            self.dt = 1
        else:
            self.dt = (perf_counter() - self.last_dt_measurment) * target_fps
        self.last_dt_measurment = perf_counter()
    
    def set_debug_message(self, text : str):
        debug_textsprite : TextSprite = core_object.main_ui.get_sprite('debug_sprite')
        if not debug_textsprite: return
        debug_textsprite.text = text
    
    def set_brightness(self, new_val : int):
        brightness = new_val
        abs_brightness = abs(new_val)
        if brightness >= 0:
            pygame.draw.rect(self.brightness_map, (abs_brightness, abs_brightness, abs_brightness), (0,0, 2000, 2000))
            self.brightness_map_blend_mode = pygame.BLEND_RGB_ADD
        else:
            pygame.draw.rect(self.brightness_map, (abs_brightness, abs_brightness, abs_brightness), (0,0, 2000, 2000))
            self.brightness_map_blend_mode = pygame.BLEND_RGB_SUB
    
    def process_touch_event(self, event : pygame.Event):
        if event.type == pygame.FINGERDOWN:
            x = event.x * self.main_display.get_width()
            y = event.y * self.main_display.get_height()
            self.active_fingers[event.finger_id] = (x,y)
        
        elif event.type == pygame.FINGERUP:
            self.active_fingers.pop(event.finger_id, None)
        
        elif event.type == pygame.FINGERMOTION:
            x = event.x * self.main_display.get_width()
            y = event.y * self.main_display.get_height()
            self.active_fingers[event.finger_id] = (x,y)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.active_fingers[10] = (event.pos)
        
        elif event.type == pygame.MOUSEMOTION:
            self.active_fingers[10] = (event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            self.active_fingers.pop(10, None)
    
    def process_core_event():
        pass

    def update(self):
        self.task_scheduler.update()
        TweenTrack.update_all()
        TweenChain.update_all()
        self.update_delta_stream()
    
    def update_delta_stream(self):
        target_lentgh = round(30 / self.dt)
        current_lentgh = len(self.delta_stream)
        if current_lentgh == target_lentgh:
            self.delta_stream.popleft()
        elif current_lentgh > target_lentgh:
            self.delta_stream.popleft()
            self.delta_stream.popleft()
        self.delta_stream.append(self.dt)
    
    def get_fps(self):
        total = 0
        for delta in self.delta_stream:
            total += delta
        
        average = total / len(self.delta_stream)
        return 60 / average
    
    def __hints(self):
        global TextSprite
        from utils.textsprite import TextSprite

core_object = Core()
setattr(core.menu, 'core_object', core_object)