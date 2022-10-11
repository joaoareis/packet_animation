import argparse
import sys
import pygame
import numpy as np
import pandas as pd
pygame.init()
#pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
FRAMERATE = 60
SIMSPEED = 5
SIZE = WIDTH, HEIGHT = 841*2, 431
speed = [2, 2]
BLACK = 0, 0, 0
RED = 255, 0, 0
BLUE = 0, 0, 255
FONT = pygame.font.SysFont('Arial', 15)
FLOW_COLORS = {
    0: RED,
    1: BLUE
}


POS = {
    "1": (40,40),
    "2": (170,130),
    "3": (290,130),
    "4": (410,130),
    "5": (530,130),
    "6": (650,130),
    "7": (800,40),
    "8": (40,400),
    "9": (290,300),
    "10": (530,300),
    "11": (800,400),
}

class Packet:
    def __init__(self, events, flowid, seqnumber, kind) -> None:
        self.events = events
        self.on = False
        self.curr_event = None
        self.next_event_time = self.events[0][1] 
        self.pos = None
        self.destination_pos = None
        self.flowid = flowid
        self.seqnumber = seqnumber
        self.kind = kind

    
    def increment_event(self):
        if self.curr_event is None:
            self.curr_event = -1

        self.curr_event+= 1
        if self.curr_event == len(self.events) - 1:
            self.curr_event = None
            self.next_event_time = None
            return
        self.pos = POS[self.events[self.curr_event][0]]
        self.destination_pos = POS[self.events[self.curr_event+1][0]]
        self.next_event_time = self.events[self.curr_event+1][1]
        time_to_next_event = self.next_event_time - self.events[self.curr_event][1]
        self.speed = self.get_speed(time_to_next_event, self.pos, self.destination_pos)
        assert time_to_next_event > 0
        
        self.rect = self._create_rect(self.pos)




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
        p_rect = pygame.Rect(topleft_x, topleft_y, 20, 20)
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
            if self.kind=="data":
                rect = pygame.draw.rect(screen, FLOW_COLORS[self.flowid], self.rect, 2)
            elif self.kind=="retransmission":
                rect = pygame.draw.rect(screen, FLOW_COLORS[self.flowid], self.rect)
            elif self.kind=="ack":
                rect = pygame.draw.circle(screen, FLOW_COLORS[self.flowid], self.rect.topleft, 18, width=2)
            else:
                raise ValueError("Kind not valid.", self.kind)
            text_coord = tuple((np.subtract(rect.center, rect.topleft)/2 + np.array(rect.topleft)).astype(int))
            screen.blit(FONT.render(str(self.seqnumber), True, BLACK),text_coord)

def create_packets(filename):
    df = pd.read_csv(filename)
    df["Node_str"] = df["Node"].astype(str)
    groups = df.groupby(["flowid", "seq",  "retransmission", "ack"])[["Node_str", "time"]].apply(lambda x: x.values.tolist()).to_dict()
    packets = list()
    for (flowid, seq, retransmission, ack), events in groups.items():
        if ack:
            kind="ack"
        else:
            kind = "data" if retransmission == 0 else "retransmission"
        packet = Packet(events=events, flowid=flowid, seqnumber=seq,kind=kind)
        packets.append(packet)
    
    return packets

def draw_stats(screen, frame):
    time_str = f"{get_frame_time(frame):.2f}"
    surface = pygame.Surface((676,45))
    surface.fill((255,255,255))
    surface.blit(FONT.render(time_str, True, BLACK), surface.get_rect().center)
    screen.blit(surface, (82,20))
    return surface
    

def get_frame_time(frame):
    time = frame/(FRAMERATE/SIMSPEED)
    return time

def set_background(screen, background):
    screen.blit(background, (0,0))
    screen.blit(background, (WIDTH/2, 0))

def draw_packets(packets, screen, frame):
    for packet in packets:
        packet.draw(screen)
        packet.step(frame)

def main(packet_file):

    background = pygame.image.load('jamboard.png')
    screen = pygame.display.set_mode(SIZE)
    set_background(screen, background)
    clock = pygame.time.Clock()

    packets = dict()
    packets["M-R2L"] = create_packets(packet_file)
    packets["SP"] = create_packets(packet_file)

    frame = 0
    frames = list()
    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()

        packet_surface = background.copy()
        draw_packets(packets, packet_surface, frame)
        set_background(screen, packet_surface)

        draw_stats(screen, frame)

        frames.append(screen.copy())
        pygame.display.flip()
        clock.tick_busy_loop(FRAMERATE)
        frame+=1
        if get_frame_time(frame) > 602:
            break

    for i, frame in enumerate(frames):
        pygame.image.save(frame, f"frames/frame{i}.jpg")

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Packet animation')
    parser.add_argument('-f','--file', help='Description for foo argument', default="packet_journey.csv")
    args = parser.parse_args()
    main(args.file)
