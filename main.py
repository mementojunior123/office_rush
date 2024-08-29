import pygame
import asyncio

import sys
pygame.init()

GAME_ICON = pygame.image.load('icon.png')
pygame.display.set_icon(GAME_ICON)

window_size = (960, 540)
#window_size = (1280, 720)
window = pygame.display.set_mode(window_size)



pygame.mixer.set_num_channels(32)

from core.core import Core, core_object
from random import shuffle

core = core_object
core.init(window)
core.FPS = 120
if core.is_web(): core.setup_web(1)
else: print("This is not the web version.")
pygame.display.set_caption('Office Rush')

from utils.base_ui_elements import BaseUiElements, UiSprite
from utils.textsprite import TextSprite
from utils.animation import Animation, AnimationTrack
from utils.helpers import rotate_around_pivot_accurate, copysign
from utils.particle_effects import ParticleEffect, Particle
from utils.my_timer import Timer
import utils.interpolation as interpolation

from game.tasks.draggable_letter import DraggableLetter, LetterPile, LetterInfo, LetterFolder, LetterFolderTopPart, SortingCriteria
from game.tasks.phone import Telephone, TelephoneTopPart
import utils.tween_module as TweenModule

from game.sprite import Sprite
Sprite._core_hint()

core.settings.set_defualt({'Brightness' : 0})
core.settings.load()

core.set_brightness(core.settings.info['Brightness'])

core.menu.init()
core.game.init()

clock = pygame.Clock()
font_40 = pygame.font.Font('assets/fonts/Pixeltype.ttf', 40)

for _ in range(8):
    DraggableLetter()

LetterPile()

Telephone()
TelephoneTopPart()
for _ in range(5):
    LetterFolder()
    LetterFolderTopPart()









def start_game(event : pygame.Event):
    
    if event.type != core.START_GAME: return
    day : int|None = event.day
    
    core.menu.prepare_exit()
    core.game.active = True
    core.game.start_day(day)
    core.task_scheduler.schedule_task(0.5, core.game.show_day, day)
    core.game.game_start_fadein()
    core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, Sprite.handle_mouse_event)
    core_object.event_manager.bind(pygame.FINGERDOWN, Sprite.handle_touch_event)
    core_object.event_manager.bind(pygame.KEYDOWN, detect_game_over)
    core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, detect_game_over)

    core.game.connect_taks()
    

    
    back_arrow_sprite = BaseUiElements.new_textless_button('BackIcon', 1, 'topleft', (10, 10), 0.2, None, 'back_arrow')
    core.main_ui.add(fps_sprite)
    core.main_ui.add(back_arrow_sprite)
    core.main_ui.add(debug_sprite)

    
    
def detect_game_over(event : pygame.Event):
    if core.game.game_timer.get_time() < 3.5: return
    if core.game.state == 'Transition': return
    if core.game.state == core.game.STATES.paused: return
    if event.type == pygame.KEYDOWN: 
        if event.key == pygame.K_ESCAPE: 
            end_game(None, False)
    
    elif event.type == pygame.MOUSEBUTTONDOWN:
        press_pos : tuple = event.pos
        back_arrow = core.main_ui.get_sprite('back_arrow')
        if back_arrow.rect.collidepoint(press_pos):
            end_game(None, True)

def end_game(event : pygame.Event = None, goto_result_screen = False):
    if event:
        goto_result_screen = getattr(event, 'goto_result_screen', goto_result_screen)
    if goto_result_screen:
        result = core.game.get_result()
    else:
        result = None
    core.game.active = False
    Sprite.clear_all_sprites()
    core.game.cleanup()
    core.game.disconnect_tasks()
    core.main_ui.clear_all()
    core_object.bg_manager.stop_all_music()
    core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, Sprite.handle_mouse_event)
    core_object.event_manager.unbind(pygame.FINGERDOWN, Sprite.handle_touch_event)
    core.event_manager.unbind(pygame.KEYDOWN, detect_game_over)
    core.event_manager.unbind(pygame.MOUSEBUTTONDOWN, detect_game_over)
    
    if goto_result_screen:
        core.menu.stage = 2
        core.menu.enter_stage2_result_screen(result, core.main_display.copy())
    else:
        core.menu.stage = 1
    
    core.menu.prepare_entry()

core.game.active = False
core.menu.add_connections()
core.event_manager.bind(core.START_GAME, start_game)
core.event_manager.bind(core.END_GAME, end_game)

core.event_manager.bind(pygame.FINGERDOWN, core.process_touch_event)
core.event_manager.bind(pygame.FINGERMOTION, core.process_touch_event)
core.event_manager.bind(pygame.FINGERUP, core.process_touch_event)

fps_sprite = TextSprite(pygame.Vector2(78, 20), 'topleft', 0, 'FPS : 0', 'fps_sprite', 
                        text_settings=(font_40, 'White', False), text_stroke_settings=('Black', 2),
                        text_alingment=(9999, 5), colorkey=(255, 0,0))

debug_sprite = TextSprite(pygame.Vector2(15, 200), 'midright', 0, '', 'debug_sprite', 
                        text_settings=(font_40, 'White', False), text_stroke_settings=('Black', 2),
                        text_alingment=(9999, 5), colorkey=(255, 0,0), zindex=999)
core.frame_counter = 0
cycle_timer = Timer(0.1, core_object.global_timer.get_time)
async def main():
    while 1:
        core.update_dt(60)
        for event in pygame.event.get():
            core.event_manager.process_event(event)
        #if core.check_window_focus() == False:
        #    core.stop_things()
        
        if core.game.active == False:

            window.fill(core.menu.bg_color)
            core.menu.update(core.dt)
            core.menu.render(window)
        else:
            #if core.check_window_focus() == False:
            #    core.stop_things()
            if core.game.state != core.game.STATES.paused:
                Sprite.update_all_sprites(core.dt)
                Sprite.update_all_registered_classes(core.dt)
                core.game.main_logic(core.dt)

            window.fill((94,129,162))    
            Sprite.draw_all_sprites(window)
            core.main_ui.update()
            core.main_ui.render(window)

        core.update()
        if cycle_timer.isover(): 
            fps_sprite.text = f'FPS : {core.get_fps():0.0f}'
            cycle_timer.restart()
        if core.settings.info['Brightness'] != 0:
            window.blit(core.brightness_map, (0,0), special_flags=core.brightness_map_blend_mode)
            
        pygame.display.update()
        core.frame_counter += 1
        clock.tick(core.FPS)
        await asyncio.sleep(0)

asyncio.run(main())


