import sys
import pygame
import numpy as np

pygame.init()
#pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
FRAMERATE = 30
SIMSPEED = 5
size = width, height = 841, 431
speed = [2, 2]
BLACK = 0, 0, 0

background = pygame.image.load('jamboard.png')

screen = pygame.display.set_mode(size)
ball = pygame.image.load("intro_ball.gif")
ballrect = ball.get_rect()
screen.blit(background, (0,0))
clock = pygame.time.Clock()

POS = {
    "node1": (40,40),
    "node2": (170,130),
    "node3": (290,130),
    "node4": (410,130),
    "node5": (530,130),
    "node6": (650,130),
    "node7": (800,40),
    "node8": (40,400),
    "node9": (290,300),
    "node10": (530,300),
    "node11": (40,800),
}

class Packet:
    def __init__(self) -> None:
        self.events = [("node1", 1), ("node2", 5), ("node3", 10), ("node4", 12)
        ,("node5", 15),("node6", 25),("node7", 35),("node6", 40)]
        self.on = False
        self.curr_event = None
        self.next_event_time = self.events[0][1] 
        self.pos = None
        self.destination_pos = None
    
    def increment_event(self):
        if self.curr_event is None:
            self.curr_event = -1

        self.curr_event+= 1
        self.pos = POS[self.events[self.curr_event][0]]
        print(self.curr_event)
        self.destination_pos = POS[self.events[self.curr_event+1][0]]
        self.next_event_time = self.events[self.curr_event+1][1]
        time_to_next_event = self.next_event_time - self.events[self.curr_event][1]
        self.speed = self.get_speed(time_to_next_event, self.pos, self.destination_pos)
        assert time_to_next_event > 0
        
        self.rect = self._create_rect(self.pos)

        if self.curr_event + 2 == len(self.events):
            self.next_event_time = None


    def get_speed(self, prop_delay, pos, destination_pos):
        direction = np.subtract(destination_pos, pos)
        length = np.linalg.norm(direction)
        speed = length/(prop_delay*FRAMERATE/SIMSPEED)
        return speed
    
    def get_velocity(self, direction, speed):
        direction = np.array(direction)
        unit_direction = direction/np.linalg.norm(direction)
        vel = unit_direction*speed
        return tuple(vel)
    
    def _create_rect(self, pos):
        topleft_x, topleft_y = pos
        p_rect = pygame.Rect(topleft_x, topleft_y, 10, 10)
        return p_rect

    def _delta_pos(self, old_pos, velocity):
        pos = np.array(old_pos)
        new_pos = pos + velocity
        return new_pos
    
    def get_direction(self, pos, destination_pos):
        direction = np.subtract(destination_pos, pos)
        return direction

    def step(self, frame):
        self.setup_curr_event(frame)
        if self.curr_event != None:
            self.move_packet()
    
    def setup_curr_event(self, frame):
        if self.next_event_time is None:
            return
        time = frame/(FRAMERATE/SIMSPEED)
        if time > self.next_event_time:
            self.increment_event()

    def move_packet(self):
        direction = self.get_direction(self.pos, self.destination_pos)
        velocity = self.get_velocity(direction, self.speed)
        self.pos = self._delta_pos(self.pos, velocity)
        self.rect = self._create_rect(self.pos)
    
    def draw(self, screen):
        if self.curr_event != None:
            pygame.draw.rect(screen, BLACK, self.rect)
    

packet = Packet()
frame = 0
while True:

    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()


    screen.blit(background, (0,0))
    packet.draw(screen)
    pygame.display.flip()
    packet.step(frame)
    clock.tick_busy_loop(FRAMERATE)
    frame+=1