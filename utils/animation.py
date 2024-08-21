import json
import pygame
from utils.my_timer import Timer
import utils.interpolation as interpolation



class AnimationTrack:
    def __init__(self, owner, data : list[dict], name):
        self.target = owner
        
        new_data = [None for instruction in data]
        for i, value in enumerate(data):
            instruction = AnimationInstruction(value)
            new_data[i] = instruction

        self.data : list[AnimationInstruction] = new_data
        self.blocking_tasks = []
        self.tasks = []
        self.progress = 0
        self.count = len(self.data)

        self.has_started = False
        self.has_ended= False
        self.time_scale = 1
        self.name = name
    
    def reset(self):
        instruction : AnimationInstruction
        for instruction in self.data:
            instruction.reset()
        
        self.blocking_tasks = []
        self.tasks = []
        self.progress = 0
        self.count = len(self.data)

        self.has_started = False
        self.has_ended= False
    
    def set_time_scale(self, value):
        self.time_scale = value
        
    
    def __getitem__(self, index):
        return self.data[index]
    
    def __delitem__(self, index):
        del self.data[index]
    
    def do_instruction(self, instruction : 'AnimationInstruction', index : int = None):

        match instruction.type:

            case "wait":
                if not instruction.has_started:
                    instruction.has_started = True
                    instruction.timer = Timer(instruction.time / self.time_scale)
                    self.blocking_tasks.append(instruction)

                if instruction.timer.isover():

                    instruction.has_ended = True
                return
            
            case "delay":
                if not instruction.has_started:
                    instruction.has_started = True
                    self.blocking_tasks.append(instruction)
                
                indexes = instruction.index
                if type(indexes) is int:
                    indexes = [indexes]

                for index in indexes:
                    if not self.data[index].has_ended: return     
                instruction.has_ended = True


            case "move_by":
                instruction.has_started = True
                self.target.x += instruction.offset[0]
                self.target.y += instruction.offset[1]
                self.target.rect.center = (round(self.target.x), round(self.target.y))
                instruction.has_ended = True
                return

            case "move_to":
                instruction.has_started = True
                self.target.rect.__setattr__(instruction.anchor, instruction.target)
                self.target.x, self.target.y = self.target.rect.center
                instruction.has_ended = True
                return
            
            case "slide_to":
                if not instruction.has_started:
                    instruction.has_started = True
                    self.tasks.append(instruction)
                    instruction.timer = Timer(instruction.time / self.time_scale)
                    instruction.start_value = self.target.rect.__getattribute__(instruction.anchor)
                    if type(instruction.easing_style) is str:
                        instruction.easing_style = getattr(interpolation, instruction.easing_style)                 
                    return
                

                alpha = instruction.timer.get_time() / instruction.timer.duration
                if alpha > 1: 
                    alpha = 1
                    instruction.has_ended = True
                

                new_pos = interpolation.lerp(instruction.start_value, instruction.target, instruction.easing_style(alpha))

                self.target.rect.__setattr__(instruction.anchor, new_pos)
                self.target.x, self.target.y = self.target.rect.center
                return
            
            case "slide_by":
                if not instruction.has_started:
                    instruction.has_started = True
                    self.tasks.append(instruction)
                    instruction.timer = Timer(instruction.time / self.time_scale)
                    instruction.start_value = (self.target.x, self.target.y)
                    instruction.last_value = (0,0)
                    if type(instruction.easing_style) is str:
                        instruction.easing_style = getattr(interpolation, instruction.easing_style)             
                    return
                
                
                alpha = instruction.timer.get_time() / instruction.timer.duration
                if alpha > 1: 
                    alpha = 1
                    instruction.has_ended = True
                
                new_offset = interpolation.lerp((0, 0), instruction.offset, instruction.easing_style(alpha))
                prev_offset= instruction.last_value
                result = (new_offset[0] - prev_offset[0], new_offset[1] - prev_offset[1])

                
                self.target.x += result[0]
                self.target.y += result[1]

                self.target.rect.center = (round(self.target.x), round(self.target.y))
                instruction.last_value = new_offset

                return

            case "rotate":
                instruction.has_started = True
                self.target.image = pygame.transform.rotate(self.target.image, instruction.angle)
                instruction.has_ended = True
                return
            
            case "rotate_over_time":
                if not instruction.has_started:
                    instruction.has_started = True
                    self.tasks.append(instruction)
                    instruction.timer = Timer(instruction.time / self.time_scale)
                    instruction.start_value = self.target.image
                    if type(instruction.easing_style) is str:
                        instruction.easing_style = getattr(interpolation, instruction.easing_style)
                    return
                
                alpha = instruction.timer.get_time() / instruction.timer.duration
                if alpha > 1: 
                    alpha = 1
                    instruction.has_ended = True
                
                angle = interpolation.lerp(0, instruction.angle, instruction.easing_style(alpha))
                self.target.image = pygame.transform.rotozoom(instruction.start_value, angle, 1)
                old_center = self.target.rect.center
                self.target.rect = self.target.image.get_rect(center = old_center)
                self.target.x, self.target.y = self.target.rect.center

            
            case "switch_image":
                instruction.has_started = True
                source = self.target.__getattribute__(instruction.source)
                new_image = source[instruction.index]
                if instruction.dynamic_anchor:
                    old_pos = self.target.rect.__getattribute__(instruction.dynamic_anchor)
                    self.target.image = new_image
                    self.target.rect = self.target.image.get_rect()
                    self.target.rect.__setattr__(instruction.dynamic_anchor, old_pos)
                else:
                    self.target.image = new_image
                
                instruction.has_ended = True
                return
            
            case "set_alpha":
                instruction.has_started = True
                self.target.image.set_alpha(instruction.target)
                instruction.has_ended = True
                return
            
            case "image_gradient":
                if not instruction.has_started:
                    instruction.has_started = True
                    self.tasks.append(instruction)
                    instruction.timer = Timer(instruction.time / self.time_scale)
                    instruction.start_value = self.target.image
                    if type(instruction.easing_style) is str:
                        instruction.easing_style = getattr(interpolation, instruction.easing_style)
                    return
                
                alpha = instruction.timer.get_time() / instruction.timer.duration
                if alpha > 1: 
                    alpha = 1
                    instruction.has_ended = True

                index = int(interpolation.lerp(0, instruction.target_index, instruction.easing_style(alpha))  )  
                source = self.target.__getattribute__(instruction.source)
                new_image = source[index]

                if instruction.dynamic_anchor:
                    old_pos = self.target.rect.__getattribute__(instruction.dynamic_anchor)
                    self.target.image = new_image
                    self.target.rect = self.target.image.get_rect()
                    self.target.rect.__setattr__(instruction.dynamic_anchor, old_pos)
                else:
                    self.target.image = new_image
            
            case "alpha_gradient":
                if not instruction.has_started:
                    instruction.has_started = True
                    self.tasks.append(instruction)
                    instruction.timer = Timer(instruction.time / self.time_scale)
                    instruction.start_value = self.target.image.get_alpha()
                    if type(instruction.easing_style) is str:
                        instruction.easing_style = getattr(interpolation, instruction.easing_style)
                    return
                
                alpha = instruction.timer.get_time() / instruction.timer.duration
                if alpha > 1: 
                    alpha = 1
                    instruction.has_ended = True

                result = interpolation.lerp(instruction.start_value, instruction.target, instruction.easing_style(alpha))
                self.target.image.set_alpha(result)
                
    
    def play(self):
        self.has_started= True
        instruction: AnimationInstruction
        for i, instruction in enumerate(self.data):
            if self.blocking_tasks: break
            self.do_instruction(instruction, i)
            if instruction.has_ended: self.progress += 1
            

    def update(self):
        if self.has_ended: return
        to_delete = []
        instruction: AnimationInstruction
        for instruction in self.tasks:
            self.do_instruction(instruction)

            if instruction.has_ended: 
                to_delete.append(instruction)
                self.progress += 1
                
        
        for instruction in to_delete:
            self.tasks.remove(instruction)
        
        to_delete = []

        for instruction in self.blocking_tasks:
            self.do_instruction(instruction)
            if instruction.has_ended: 
                to_delete.append(instruction)
                self.progress += 1
                
        
        for instruction in to_delete:
            self.blocking_tasks.remove(instruction)
        

        for i, instruction in enumerate(self.data):
            if self.blocking_tasks: break
            if instruction.has_ended: continue
            self.do_instruction(instruction, i)
            if instruction.has_ended: self.progress += 1

        if self.progress >= self.count: self.has_ended = True
        



class AnimationInstruction:
    def __init__(self, data):
        self.type = data["type"]
        for key in data:
            val = data[key]
            self.__setattr__(key, val)
        self.data = data

        self.has_started = False
        self.has_ended = False

        self.start_value = None
        self.last_update = None
        self.last_value = None
        self.timer : Timer = None
        
    def reset(self):
        data = self.data
        self.type = data["type"]
        for key in data:
            val = data[key]
            self.__setattr__(key, val)
        self.data = data

        self.has_started = False
        self.has_ended = False

        self.start_value = None
        self.last_update = None
        self.last_value = None
        self.timer : Timer = None

    def __getitem__(self, index):
        return self.data[index]
    
    def __setitem__(self, index, val):
        self.data[index] = val
        self.__setattr__(index, val)

TEMPLATES = [
    {"type" : "move_by", "offset" : (0,0)},
    {"type" : "move_to", "target" : (0,0), "anchor" : "center"},

    {"type" : "slide_to", "target" : (0,0), "anchor" : "center", "time" : 0, "easing_style" : interpolation.linear}, #target is tuple|int
    {"type" : "slide_by", "offset" : (0,0), "time" : 0, "easing_style" : interpolation.linear}, #offset is always a tuple

    {"type" : "wait", "time" : 0},
    {"type" : "delay" , "index" : 0},
    {"type" : "switch_image", "source" : "source_name", "index" : None, 'dynamic_anchor' : 'rect_attribute or none'},
    {"type" : "rotate", "angle" : 0},
    {"type" : "rotate_over_time", "angle" : 0, "time" : 0, "easing_style" : interpolation.linear},

    {"type" : "image_gradient", "source" : "source_name", "target_index" : 0, "time" : 0, "easing_style" : interpolation.linear, 'dynamic_anchor' : 'rect_attr/none'},
    {"type" : "set_alpha", "target" : 0},
    {"type" : "alpha_gradient", "target" : 0, "time" : 0, "easing_style" : interpolation.linear},
             ]


class Animation:
    ANIM_DATA = {}

    @classmethod
    def get_animation(cls, name):
        if name in cls.ANIM_DATA:
            return Animation(cls.ANIM_DATA[name], name)
        else:
            print("AnimationError: Animation not found")
            return None

    
    def __init__(self, data : list[dict], name : str) -> None:
        self.data = data
        self.name : str = name
    
    def load(self, owner):
        return AnimationTrack(owner, self.data, self.name)

    def load_file(self, path = "data/animations/animation_data.json"):
        with open(path, "r") as read_file:
            dictionary = json.load(read_file)
        
        self.ANIM_DATA += dictionary
