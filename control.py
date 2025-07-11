import pygame

class Control:
    def __init__(self):
        # detect joystick if connected
        self.joystick = None
        if pygame.joystick.get_count() != 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print("Joystick connected!")
        else:
            print("No joystick found, sticking to keyboard controls")

    def get_joystick_data(self):

        x, y = (
            round(self.joystick.get_axis(0), 2),
            round(self.joystick.get_axis(1) * -1, 2),
        )

        pov = round(self.joystick.get_axis(3) * -1, 2)
        gripper = self.joystick.get_button(0)

        joystick_data = {
            "x": x,  # rotation right (+ve)/ left (-ve)
            "y": y,  # forward (+ve)/ backward (-ve)
            "pov": pov,  # float down (+ve) or up (-ve)
            "gripper": gripper,  # gripper closed (0) or open (1)
        }

        return joystick_data

    def get_keyboard_data(self):
        keys = pygame.key.get_pressed()

        y = 0, x = 0, pov = 0, gripper = 0

        if keys[pygame.K_UP] and not keys[pygame.K_DOWN]:
            y = 1.0
        elif not keys[pygame.K_UP] and keys[pygame.K_DOWN]:
            y = -1.0

        if keys[pygame.K_RIGHT] and not keys[pygame.K_LEFT]:
            x = 1.0
        elif not keys[pygame.K_RIGHT] and keys[pygame.K_LEFT]:
            x = -1.0

        if keys[pygame.K_SPACE]:
            gripper = 1.0

        if keys[pygame.K_LSHIFT] and not keys[pygame.K_LCTRL]:
            pov = 1.0
        elif not keys[pygame.K_LSHIFT] and keys[pygame.K_LCTRL]:
            pov = -1.0

        keyboard_data = {
            "x": x,  # rotation right (+ve)/ left (-ve)
            "y": y,  # forward (+ve)/ backward (-ve)
            "pov": pov,  # float down (+ve) or up (-ve)
            "gripper": gripper,  # gripper closed (0) or open (1)
        }

        return keyboard_data
        

    def get_input(self):
        pygame.event.pump()
        if self.joystick != None:
            return self.get_joystick_data()
        else:
            return self.get_keyboard_data()

