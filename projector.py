import os, sys, time
import cv2
import numpy as np
from pathlib import Path
import pygame


class Projector():
    def __init__(self, cfg):
        self._c = cfg
        # initial the pygame settings
        pygame.init()
        self.wait_proj = True

        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        # self.screen = pygame.display.set_mode((0,0))
        self.screen.fill((0,0,255))
        self.bg = pygame.image.load('./data/cover.png').convert()
        self.blank= pygame.image.load('./data/blank.png').convert()
        self._load_images()

        self.clock = pygame.time.Clock()              # 设置时钟
        self.clock.tick(24)

    def _load_images(self):
        self.images_h = []
        self.images_v = []

        self.counter_h, self.counter_v = 0, 0

        root = self._c.pattern_path
        for f, T in enumerate(self._c.Tp):
            for s in range(self._c.steps[f]):
                img_h = Path(root)/f"{f:0>2d}{s:0>2d}h.bmp" 
                print(img_h)
                self.images_h.append(pygame.image.load(img_h).convert())
                img_v = Path(root)/f"{f:0>2d}{s:0>2d}v.bmp" 
                self.images_v.append(pygame.image.load(str(img_v)).convert())
        img_bg = Path(root)/f"bg.bmp" 
        self.images_h.append(pygame.image.load(img_bg).convert())

    def wait_to_begin(self):
        self.screen.blit(self.bg,(0,0))
        pygame.display.flip()
        pygame.display.update()
        while True:
            self.clock.tick(24)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.wait_proj = False
                    self.exit()

            keys_pressed = pygame.key.get_pressed()
            if keys_pressed[pygame.K_SPACE]:
                print("Begin to project patterns...")
                break

            if keys_pressed[pygame.K_ESCAPE]:
                self.wait_proj = False
                print("Projection finished.\n")
                break
        return self.wait_proj

    def update(self, hv="h"):
        if hv == "h":
            self.screen.blit(self.images_h[self.counter_h],(0,0))
            pygame.display.flip()
            self.counter_h +=1
            self.counter_h = self.counter_h % len(self.images_h)
            not2end = False if self.counter_h ==0 else True
        else:
            self.screen.blit(self.images_v[self.counter_v],(0,0))
            pygame.display.flip()
            self.counter_v +=1
            self.counter_v = self.counter_v % len(self.images_v)
            not2end = False if self.counter_v ==0 else True
        return not2end

    def black(self):
        self.screen.blit(self.blank,(0,0))
        pygame.display.flip()

    def exit(self):
        pygame.quit()


def test():
    from config import config
    cfg = config()  
    prj = Projector(cfg)

    while prj.wait_to_begin():
        while prj.update():
            time.sleep(0.5)
    prj.exit()

if __name__ == "__main__":
    test()

