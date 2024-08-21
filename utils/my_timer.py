from time import perf_counter

class Timer:
    def __init__(self, treshold) -> None:
        self.duration = treshold
        self.start_time = perf_counter()
        self.init_time = perf_counter()
        
        
        self.paused = False
        self.pause_start = None
        self.pause_duration = 0
    
    @classmethod
    def new(cls, duration = -1):
        return cls(duration)


    def restart(self):
        self.start_time = perf_counter()
        
        self.paused = False
        self.pause_start = None
        self.pause_duration = 0
    
    def set_duration(self, duration, restart = True):
        self.duration = duration
        if restart: self.restart()
    
    def pause(self):
        if self.paused: return
        self.pause_start = perf_counter()
        self.paused = True
    
    def unpause(self):
        if not self.paused: return
        self.pause_duration += perf_counter() - self.pause_start
        self.paused = False
        self.pause_start = None
    
    def toogle(self):
        if self.paused: self.unpause()
        else: self.pause()
    
    def get_time(self):
        return perf_counter() - self.start_time - self.get_pause_time()
    
    def get_real_time(self):
        return perf_counter() - self.start_time
    
    def get_pause_time(self):
        if self.paused == False: return self.pause_duration
        else: return self.pause_duration + perf_counter() - self.pause_start
    
    def get_time_left(self):
        return self.duration - self.get_time()
    
    def isover(self):
        """
        Determines if the timer is over. 
        Returns False if the timer's duration is below 0.
        """
        if self.duration < 0: return False
        if self.get_time() > self.duration:
            return True
        return False


