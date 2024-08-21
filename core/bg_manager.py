import pygame

class BgManager:
    def __init__(self) -> None:
        self.current : list[tuple[pygame.mixer.Sound, float]] = []
        self.global_volume = 1

    def set_global_volume(self, new_volume):
        self.global_volume = new_volume
        for track, vol in self.current:
            track.set_volume(vol * self.global_volume)

       

    def play(self, track : pygame.mixer.Sound, volume, loops = -1, maxtime = 0, fade_ms = 0):
        channel = track.play(loops, maxtime, fade_ms)
        track.set_volume(volume * self.global_volume)
        self.current.append((track, volume))
        return channel
    
    def play_sfx(self, sfx : pygame.mixer.Sound, volume, loops = 0, maxtime = 0, fade_ms = 0):
        '''Used for playing short sound effects.'''

        channel = sfx.play(loops, maxtime, fade_ms)
        sfx.set_volume(volume * self.global_volume)
        return channel
        


    def stop(self, track : pygame.mixer.Sound):
        track.stop()
        for tup in self.current:
            if tup[0] is track:
                self.current.remove(tup)
                return

    def stop_all(self):
        """Stops all currently playing tracks."""
        for track, _ in self.current:
            track.stop()
        self.current.clear()
            

    def update(self):
        to_remove : list[tuple[pygame.mixer.Sound, float]] = []
        for tup in self.current:
            sound : pygame.mixer.Sound = tup[0]
            if sound.get_num_channels() <= 0:
                to_remove.append(tup)
        for tup in to_remove:
            self.current.remove(tup)   

