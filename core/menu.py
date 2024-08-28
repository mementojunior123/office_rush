import pygame
import random
from utils.ui_sprite import UiSprite
from utils.textsprite import TextSprite
from utils.base_ui_elements import BaseUiElements
import utils.tween_module as TweenModule
import utils.interpolation as interpolation
from utils.my_timer import Timer
from utils.brightness_overlay import BrightnessOverlay
from math import floor
class Menu:
    font_40 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 70)
    font_150 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 150)
    paper_template_image = pygame.image.load(r'assets/graphics/tasks/letters/mid_dense_paper.png').convert_alpha()#
    grade_frame_image = pygame.image.load(r'assets/graphics/menu/grade_frame.png').convert()
    #paper_template_image.set_colorkey('Purple')
    nothing = pygame.surface.Surface((100,300), pygame.SRCALPHA)
    pygame.draw.rect(nothing, 'White', (0,0, 100,300))
    def __init__(self) -> None:
        self.stage : int
        self.stages : list[list[UiSprite]]
        self.bg_color = (94, 129, 162)
    def init(self):

        window_size = core_object.main_display.get_size()
        centerx = window_size[0] // 2

        black_transparent_overlay = pygame.Surface(window_size, pygame.SRCALPHA)
        pygame.draw.rect(black_transparent_overlay, (0, 0, 0, 255), (0,0, window_size[0], window_size[1]))

        white_transparent_overlay = pygame.Surface(window_size, pygame.SRCALPHA)
        pygame.draw.rect(white_transparent_overlay, (0, 0, 0, 255), (0,0, window_size[0], window_size[1]))

        text_settings = (Menu.font_60, 'Black', False)
        text_settings_buttons = (Menu.font_40, 'Black', False)
        self.stage = 1
        
        self.stage_data : list[dict] = [None, {'Tween' : None}, {}, {}]
        self.stages = [None, 
        [BaseUiElements.new_text_sprite('Office Rush', text_settings, 0, 'midtop', (centerx, 50)),
        BaseUiElements.new_button('Blue', 'Play', 1, 'midbottom', (centerx, window_size[1] - 15), (0.5, 1.4), {'name' : 'play_button'}, text_settings_buttons),
        BrightnessOverlay(0, pygame.Rect(0,0, *core_object.main_display.get_size()), 0, 'overlay', zindex=99)],
        #stage 1 --> stage 2
        [BaseUiElements.new_button('Blue', 'Back', 1, 'bottomleft', (200, window_size[1] - 15), (0.5, 1), {'name' : 'back_button'}, text_settings_buttons),
         BaseUiElements.new_button('Blue', 'Continue', 2, 'bottomright', (760, window_size[1] - 15), (0.5, 1), {'name' : 'continue_button'}, text_settings_buttons),
         UiSprite(Menu.grade_frame_image, Menu.grade_frame_image.get_rect(topleft = (25, 25)), 0, 'grade_frame'),
         TextSprite(pygame.Vector2(50, 50), 'center', 0, 'A', 'grade', None, None, 2, (Menu.font_150, 'Blue', False), ('Black', 3), (1500, 2))],
         #stage 2 --> stage 3
         [BaseUiElements.new_button('Blue', 'Continue', 1, 'bottomright', (760, window_size[1] - 15), (0.5, 1), {'name' : 'continue_button'}, text_settings_buttons),
          BaseUiElements.new_button('Blue', 'Back', 2, 'bottomleft', (200, window_size[1] - 15), (0.5, 1), {'name' : 'back_button'}, text_settings_buttons)],
        ]
        (self.get_sprite_by_name(1, 'overlay')).brightness = 0
        (self.get_sprite_by_name(2, 'grade')).visible = False
        self.bg_color = (94, 129, 162)
    
    def add_connections(self):
        core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.bind(UiSprite.TAG_EVENT, self.handle_tag_event)
    
    def remove_connections(self):
        core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.unbind(UiSprite.TAG_EVENT, self.handle_tag_event)
    
    def __get_core_object(self):
        global core_object
        from core.core import core_object

    def render(self, display : pygame.Surface):
        sprite_list = [sprite for sprite in self.stages[self.stage] if sprite.visible == True]
        sprite_list.sort(key = lambda sprite : sprite.zindex)
        for sprite in sprite_list:
            sprite.draw(display)
        
    
    def update(self, delta : float):
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                tween : TweenModule.TweenTrack = stage_data.get('Tween', None)
                if not tween: return
                if tween.has_finished:
                    pass
                    self.on_stage1_tween_ended()
            case 2:
                pass
    
    def start_stage1_fadeout(self):
        overlay : BrightnessOverlay = self.get_sprite_by_name(1, 'overlay')
        overlay.brightness = 0
        self.stage_data[1]['Tween'] = TweenModule.new_tween(overlay, TweenModule.TweenInfo(interpolation.linear, 1.5), {'brightness' : -255})

    def on_stage1_tween_ended(self):
        self.launch_game()
        self.stage_data[1]['Tween'] = None
        #overlay = self.get_sprite_by_name(1, 'overlay') --handled by start_game() or end_game() in the main function
        #overlay.opacity = 0

    def prepare_entry(self):
        self.add_connections()
        (self.get_sprite_by_name(1, 'overlay')).brightness = 0
    
    def prepare_exit(self):
        self.stage = 0
        self.remove_connections()

    def enter_stage2_result_screen(self, game_result : dict, screenshot : pygame.Surface):
        self.stage_data[2]['result'] = game_result
        self.stage_data[2]['screenshot'] = UiSprite(screenshot, screenshot.get_rect(topleft = (0,0)), 0, 'screenshot')
        self.stage_data[2]['timer'] = Timer(6, core_object.global_timer.get_time)
        self.stage_data[2]['papers'] = []
        self.stage_data[2]['tasks'] = []
        self.stage_data[2]['angle_cache'] = {}

        self.stages[2].append(self.stage_data[2]['screenshot'])
        back_button = self.get_sprite_by_name(2, 'back_button')
        next_day_button = self.get_sprite_by_name(2, 'continue_button')
        grade_sprite : TextSprite = self.get_sprite_by_name(2, 'grade')
        back_button.visible = False
        next_day_button.visible= False
        grade_sprite.visible = False
        grade_sprite.visible=  False

        final_percent : float  = game_result['final_percentage']
        if final_percent > 0.999:
            grade_sprite.text_settings = (grade_sprite.text_settings[0], 'Purple', grade_sprite.text_settings[2])
            grade_sprite.text = 'SS'
        elif final_percent >= 0.95:
            grade_sprite.text_settings = (grade_sprite.text_settings[0], 'Gold', grade_sprite.text_settings[2])
            grade_sprite.text = 'S'
        elif final_percent >= 0.9:
            grade_sprite.text_settings = (grade_sprite.text_settings[0], 'Blue', grade_sprite.text_settings[2])
            grade_sprite.text = 'A'
        elif final_percent >= 0.8:
            grade_sprite.text_settings = (grade_sprite.text_settings[0], 'Green', grade_sprite.text_settings[2])
            grade_sprite.text = 'B'
        elif final_percent >= 0.6:
            grade_sprite.text_settings = (grade_sprite.text_settings[0], 'Yellow', grade_sprite.text_settings[2])
            grade_sprite.text = 'C'
        else:
            grade_sprite.text_settings = (grade_sprite.text_settings[0], 'Red', grade_sprite.text_settings[2])
            grade_sprite.text = 'D'
        grade_frame = self.get_sprite_by_name(2, 'grade_frame')
        grade_sprite.rect = grade_sprite.surf.get_rect(center = grade_frame.rect.center)
        grade_sprite.position = pygame.Vector2(grade_sprite.rect.center)

        y_pos = 100
        left = grade_frame.rect.right
        for task in game_result['tasks']:
            task : str
            result : float = game_result['tasks'][task]
            result = floor(result * 100)
            text = f'{task} : {result:0.0f}%'
            new_sprite = TextSprite(pygame.Vector2(500, 400), 'center', 0, text, 'task_result', None, None, 0, (Menu.font_70, 'Black', False))
            new_sprite.rect.topleft = (left + 50, y_pos)
            y_pos += 100
            self.stages[2].append(new_sprite)
            self.stage_data[2]['tasks'].append(new_sprite)
            new_sprite.visible = False
                                    
        delay = 0.05
        frequency = 0.05
        count = 50
        a = frequency * count + delay + 0.1
        b = frequency * count + delay + 0.7
        end = (frequency * count) * 2 + delay + 0.75
        for i in range(count):
            core_object.task_scheduler.schedule_task(i * frequency + delay, self.add_stage2_rand_paper, 100 + i)
        core_object.task_scheduler.schedule_task(a, self.remove_stage2_screenshot_and_show_buttons)
        for i in range(count + 1):
            core_object.task_scheduler.schedule_task(b + i * frequency, self.remove_last_stage2_paper)


    def add_stage2_rand_paper(self, zindex):
        paper_list : list[UiSprite] = self.stage_data[2]['papers']
        #paper_image = Menu.paper_template_image
        #angle = random.randint(0, 360)
        #scale = 0 * (random.random() * 0.7) + 1
        #new_image = pygame.transform.rotozoom(paper_image, angle, scale)
        angle = random.choice([i for i in range(0, 360, 15)])
        if angle in self.stage_data[2]['angle_cache']:
            new_image = self.stage_data[2]['angle_cache'][angle]
        else:
            new_image = pygame.transform.rotate(Menu.paper_template_image, angle)
            self.stage_data[2]['angle_cache'][angle] = new_image
        final_surf = pygame.surface.Surface((new_image.get_size()))
        colorkey = pygame.color.Color(200, 0, 100)
        final_surf.fill(colorkey)
        final_surf.set_colorkey(colorkey)
        final_surf.blit(new_image, (0,0))
        paper_sprite = UiSprite(final_surf, final_surf.get_rect(center = (0,0)), 0, keep_og_surf=False, zindex=zindex)
        x, y = random.randint(10, 950), random.randint(10, 530)
        paper_sprite.position = pygame.Vector2(x, y)
        paper_sprite.rect.center = (x, y)
        self.stages[2].append(paper_sprite)
        paper_list.append(paper_sprite)
    
    def remove_last_stage2_paper(self):
        paper_list : list[UiSprite] = self.stage_data[2]['papers']
        if len(paper_list) == 0 : return
        paper_sprite : UiSprite = paper_list[-1]
        paper_list.remove(paper_sprite)
        self.stages[2].remove(paper_sprite)
        
    
    def remove_random_stage2_paper(self):
        paper_list : list[UiSprite] = self.stage_data[2]['papers']
        if len(paper_list) == 0 : return
        paper_sprite : UiSprite = random.choice(paper_list)
        paper_list.remove(paper_sprite)
        self.stages[2].remove(paper_sprite)

    
    def remove_stage2_screenshot_and_show_buttons(self):
        screenshot = self.get_sprite_by_name(2, 'screenshot')
        self.stages[2].remove(screenshot)
        self.stage_data[2]['screenshot'] = None
        back_button = self.get_sprite_by_name(2, 'back_button')
        next_day_button = self.get_sprite_by_name(2, 'continue_button')
        grade_sprite = self.get_sprite_by_name(2, 'grade')
        back_button.visible = True
        next_day_button.visible= True
        grade_sprite.visible= True
        for sprite in self.stage_data[2]['tasks']:
            sprite.visible = True

    def exit_stage2_results(self):
        self.stage_data[2]['result'] = None
        self.stage_data[2]['screenshot'] = None
        self.stage_data[2]['timer'] = None
        self.stage_data[2]['papers'] = None
        sprite : TextSprite
        for sprite in self.stage_data[2]['tasks']:
            self.stages[2].remove(sprite)
        self.stage_data[2]['tasks'].clear()
        self.stage_data[2]['angle_cache'].clear()
    
    def enter_stage3_results(self, money_result : dict[str, int]):
        self.stage_data[3]['task_sprites'] = []
        self.stage_data[3]['money_result'] = money_result
        centerx = core_object.main_display.get_width() // 2
        y_pos : int = 50
        task : str
        for task in money_result:
            if task == 'Final' : y_pos += 50   
            result : int = money_result[task]
            text = f'{task} : {result}$'
            new_sprite = TextSprite(pygame.Vector2(500, 400), 'center', 0, text, 'task_result', None, None, 0, (Menu.font_70, 'Black', False))
            new_sprite.rect.midtop = (centerx, y_pos)
            y_pos += 50
            self.stages[3].append(new_sprite)
            self.stage_data[3]['task_sprites'].append(new_sprite)
    
    def exit_stage3_results(self):
        for sprite in self.stage_data[3]['task_sprites']:
            self.stages[3].remove(sprite)
        self.stage_data[3]['task_sprites'].clear()
        self.stage_data[3]['money_result'].clear()

    def launch_game(self):
        new_event = pygame.event.Event(core_object.START_GAME, {'day' : 1})
        pygame.event.post(new_event)

    def get_sprite(self, stage, tag):
        """Returns the 1st sprite with a corresponding tag.
        None is returned if it was not found in the stage."""
        if tag is None or stage is None: return None

        the_list = self.stages[stage]
        for sprite in the_list:
            if sprite.tag == tag:
                return sprite
        return None
    
    def get_sprite_by_name(self, stage, name):
        """Returns the 1st sprite with a corresponding name.
        None is returned if it was not found in the stage."""
        if name is None or stage is None: return None

        the_list = self.stages[stage]
        sprite : UiSprite
        for sprite in the_list:
            if sprite.name == name:
                return sprite
        return None

    def get_sprite_index(self, stage, name = None, tag = None):
        '''Returns the index of the 1st occurence of sprite with a corresponding name or tag.
        None is returned if the sprite is not found'''
        if name is None and tag is None: return None
        the_list = self.stages[stage]
        sprite : UiSprite
        for i, sprite in enumerate(the_list):
            if sprite.name == name and name is not None:
                return i
            if sprite.tag == tag and tag is not None:
                return i
        return None
    
    def handle_tag_event(self, event : pygame.Event):
        if event.type != UiSprite.TAG_EVENT:
            return
        tag : int = event.tag
        name : str = event.name
        trigger_type : str = event.trigger_type
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                tween : TweenModule.TweenTrack|None = stage_data.get('Tween', None)
                if tween: return
                if name == 'play_button':
                    self.start_stage1_fadeout()
            case 2:
                timer : Timer = self.stage_data[2]['timer']
                if not timer.isover(): return
                if name == 'back_button':
                    self.stage = 1
                    self.exit_stage2_results()
                elif name == 'continue_button':
                    self.stage = 3
                    money_result : dict[str, int] = self.stage_data[2]['result']['Money']
                    self.exit_stage2_results()
                    self.enter_stage3_results(money_result)
            
            case 3:
                if name == 'back_button':
                    self.stage = 1
                    self.exit_stage3_results()
                elif name == 'continue_button':
                    self.stage = 1
                    self.exit_stage3_results()

                   
    
    def handle_mouse_event(self, event : pygame.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos : tuple = event.pos
            sprite : UiSprite
            for sprite in self.stages[self.stage]:
                if type(sprite) != UiSprite: continue
                if sprite.rect.collidepoint(mouse_pos):
                    sprite.on_click()
