import pygame
import sys
import math
import random

# Инициализация Pygame
pygame.init()

# Параметры окна
WIDTH, HEIGHT = 900, 700
SCALE = 50  # 1 км = 50 пикселей

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Квадрокоптер vs Ракета")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (255, 50, 50)
GREEN = (50, 200, 50)
YELLOW = (255, 255, 0)
GRAY = (150, 150, 150)
DARK_GRAY = (100, 100, 100)
LIGHT_BLUE = (173, 216, 230)

font_small = pygame.font.SysFont(None, 20)
font_medium = pygame.font.SysFont(None, 24)
font_large = pygame.font.SysFont(None, 32)


class Button:
    def __init__(self, x, y, width, height, text, color=GRAY, text_color=BLACK):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hover = False

    def draw(self, surface):
        color = tuple(min(c + 30, 255)
                      for c in self.color) if self.hover else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        text_surf = font_medium.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def update(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)


class InputField:
    def __init__(self, x, y, width, height, label, default_value=0, min_val=0.1, max_val=1000):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.value = str(default_value)
        self.active = False
        self.min_val = min_val
        self.max_val = max_val
        self.error = False

    def draw(self, surface):
        label_surf = font_small.render(self.label, True, BLACK)
        surface.blit(label_surf, (self.rect.x, self.rect.y - 25))

        color = LIGHT_BLUE if self.active else (
            255, 100, 100 if self.error else 255)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)

        text_surf = font_medium.render(self.value, True, BLACK)
        surface.blit(text_surf, (self.rect.x + 5, self.rect.y + 5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.unicode.isdigit() or event.unicode == '.':
                self.value += event.unicode

    def get_value(self):
        try:
            val = float(self.value) if self.value else 0
            if val < self.min_val or val > self.max_val:
                self.error = True
                return None
            self.error = False
            return val
        except ValueError:
            self.error = True
            return None

    def set_value(self, value):
        self.value = str(value)
        self.error = False


STATE_SETUP = "setup"
STATE_RUNNING = "running"


class SimulationApp:
    def __init__(self):
        self.state = STATE_SETUP
        self.simulation_paused = False
        self.simulation_finished = False

        # Поля ввода
        input_y = 150
        self.drone_speed_input = InputField(
            100, input_y, 250, 35, "Скорость дрона атаки (км/ч):", 100)
        self.missile_speed_input = InputField(
            100, input_y + 80, 250, 35, "Скорость ракеты защиты (км/ч):", 200)
        self.zone_radius_input = InputField(
            100, input_y + 160, 250, 35, "Радиус зоны (км):", 3)

        # Кнопки
        self.start_button = Button(
            100, 350, 250, 50, "НАЧАТЬ СИМУЛЯЦИЮ", color=(100, 200, 100))
        self.pause_button = Button(
            650, 10, 120, 40, "ПАУЗА", color=(200, 150, 50))
        self.reset_button = Button(
            780, 10, 110, 40, "СБРОСИТЬ", color=(200, 50, 50))

        # Переменные симуляции
        self.speed_drone_kmh = 100
        self.speed_missile_kmh = 200
        self.zone_radius_km = 3.0

        self.clock = pygame.time.Clock()
        self.reset_simulation()

    def reset_simulation(self):
        """Сброс симуляции"""
        self.speed_drone = self.speed_drone_kmh / 3600.0
        self.speed_missile = self.speed_missile_kmh / 3600.0

        center_x_km = WIDTH / (2 * SCALE)
        center_y_km = HEIGHT / (2 * SCALE)

        # Ракета неподвижна в центре
        self.missile_pos = [center_x_km, center_y_km]
        # Дрон атакует с края
        self.drone_active = False
        self.drone_pos = [0.0, 0.0]
        self.drone_angle = 0.0
        self.drone_direction_change_timer = 0
        self.drone_direction_change_interval = random.uniform(2, 6)

        self.explosion = False
        self.explosion_time = 0
        self.explosion_duration = 1.0

        self.time_elapsed = 0.0
        self.drone_distance = 0.0
        self.missile_distance = 0.0
        self.drone_detected = False
        self.tracking_active = False
        self.intercepted = False
        self.simulation_finished = False
        self.simulation_paused = False

    def spawn_drone(self):
        """Спавн дрона на краю экрана"""
        side = random.choice(['top', 'bottom', 'left', 'right'])
        margin_km = 1.0
        if side == 'top':
            x = random.uniform(0, WIDTH / SCALE)
            y = -margin_km
        elif side == 'bottom':
            x = random.uniform(0, WIDTH / SCALE)
            y = HEIGHT / SCALE + margin_km
        elif side == 'left':
            x = -margin_km
            y = random.uniform(0, HEIGHT / SCALE)
        else:  # right
            x = WIDTH / SCALE + margin_km
            y = random.uniform(0, HEIGHT / SCALE)

        angle = random.uniform(0, 2 * math.pi)
        return [x, y], angle

    def draw_setup_screen(self):
        """Рисует экран настройки"""
        screen.fill(WHITE)

        title = font_large.render("КВАДРОКОПТЕР vs РАКЕТА", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        subtitle = font_medium.render("Настройка симуляции", True, DARK_GRAY)
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 80))

        self.drone_speed_input.draw(screen)
        self.missile_speed_input.draw(screen)
        self.zone_radius_input.draw(screen)
        self.start_button.draw(screen)

        if any([self.drone_speed_input.error, self.missile_speed_input.error, self.zone_radius_input.error]):
            error_text = font_small.render("Проверьте значения!", True, RED)
            screen.blit(error_text, (100, 420))

        pygame.display.flip()

    def draw_simulation_screen(self):
        """Рисует экран симуляции"""
        screen.fill(WHITE)

        self.pause_button.text = "ВОЗОБНОВИТЬ" if self.simulation_paused else "ПАУЗА"
        self.pause_button.draw(screen)
        self.reset_button.draw(screen)

        def km_to_px(x_km, y_km):
            return int(x_km * SCALE), int(y_km * SCALE)

        # Центр (ракета в центре)
        center_x_km = WIDTH / (2 * SCALE)
        center_y_km = HEIGHT / (2 * SCALE)
        cx, cy = km_to_px(center_x_km, center_y_km)

        # Зона вокруг ракеты
        pygame.draw.circle(screen, GREEN, (cx, cy),
                           int(self.zone_radius_km * SCALE), 2)

        # Ракета (неподвижная в центре) - увеличенный размер
        rocket_size = 15
        pygame.draw.polygon(screen, RED, [
            (cx, cy),
            (cx + rocket_size, cy + rocket_size),
            (cx, cy + rocket_size + 12),
            (cx - rocket_size, cy + rocket_size)
        ])
        pygame.draw.circle(screen, YELLOW, (cx, cy), rocket_size // 2)

        # Дрон (атакует с края) - увеличенный размер
        if self.drone_active and not self.explosion:
            dx, dy = km_to_px(self.drone_pos[0], self.drone_pos[1])
            drone_size = 12
            pygame.draw.polygon(screen, BLUE, [
                (dx, dy),
                (dx - drone_size * math.cos(self.drone_angle),
                 dy - drone_size * math.sin(self.drone_angle)),
                (dx - drone_size * 0.7 * math.cos(self.drone_angle) - drone_size * 0.5 * math.sin(self.drone_angle),
                 dy - drone_size * 0.7 * math.sin(self.drone_angle) + drone_size * 0.5 * math.cos(self.drone_angle)),
                (dx - drone_size * 0.7 * math.cos(self.drone_angle) + drone_size * 0.5 * math.sin(self.drone_angle),
                 dy - drone_size * 0.7 * math.sin(self.drone_angle) - drone_size * 0.5 * math.cos(self.drone_angle))
            ])
            pygame.draw.circle(screen, BLUE, (dx, dy), drone_size // 2)

        # Линия преследования (если обнаружен дрон)
        if self.drone_active and self.tracking_active and not self.explosion:
            dx, dy = km_to_px(self.drone_pos[0], self.drone_pos[1])
            pygame.draw.line(screen, YELLOW, (cx, cy), (dx, dy), 1)

        # Взрыв (в центре, у ракеты)
        if self.explosion:
            ex, ey = cx, cy
            radius = int(20 * (self.explosion_time / self.explosion_duration))
            pygame.draw.circle(screen, YELLOW, (ex, ey), radius)
            pygame.draw.circle(screen, RED, (ex, ey), radius // 2)

        # Информация
        dist_to_drone = math.hypot(
            self.missile_pos[0] - self.drone_pos[0],
            self.missile_pos[1] - self.drone_pos[1]) if self.drone_active else 0
        
        info_lines = [
            f"Время: {self.time_elapsed:.3f} ч",
            f"Дрон пройден: {self.drone_distance:.3f} км",
            f"Расстояние дрон→ракета: {dist_to_drone:.3f} км",
            f"Ракета преследует: {'ДА ✓' if self.tracking_active else 'НЕТ'}",
            f"Скорость дрона атаки: {self.speed_drone_kmh} км/ч",
            f"Скорость ракеты защиты: {self.speed_missile_kmh} км/ч",
        ]

        if self.simulation_paused:
            info_lines.append("⏸ СИМУЛЯЦИЯ ПРИОСТАНОВЛЕНА")

        if self.simulation_finished:
            if self.intercepted:
                info_lines.append("✅ ДРОН ПЕРЕХВАЧЕН РАКЕТОЙ!")
            else:
                info_lines.append("❌ ДРОН ИЗБЕЖАЛ ПЕРЕХВАТА!")

        for i, line in enumerate(info_lines):
            text = font_small.render(line, True, BLACK)
            screen.blit(text, (10, 60 + i * 22))

        pygame.display.flip()

    def update_simulation(self):
        """Обновляет состояние симуляции"""
        if self.simulation_paused or self.simulation_finished:
            return

        dt = 1.0
        self.time_elapsed += dt / 3600.0

        # Спавн дрона
        if not self.drone_active:
            self.drone_pos, self.drone_angle = self.spawn_drone()
            self.drone_active = True

        # Движение дрона (случайное)
        if self.drone_active and not self.explosion:
            self.drone_direction_change_timer += dt
            if self.drone_direction_change_timer >= self.drone_direction_change_interval:
                turn = random.uniform(-math.pi / 6, math.pi / 6)
                self.drone_angle += turn
                self.drone_direction_change_timer = 0
                self.drone_direction_change_interval = random.uniform(2, 6)

            dx = math.cos(self.drone_angle) * self.speed_drone * dt
            dy = math.sin(self.drone_angle) * self.speed_drone * dt
            self.drone_pos[0] += dx
            self.drone_pos[1] += dy
            self.drone_distance += self.speed_drone * dt

            # Проверка границ экрана
            margin = 0.5  # Отступ 0.5 км от края
            max_x = WIDTH / SCALE
            max_y = HEIGHT / SCALE
            self.drone_pos[0] = max(margin, min(
                self.drone_pos[0], max_x - margin))
            self.drone_pos[1] = max(margin, min(
                self.drone_pos[1], max_y - margin))

            # Проверка: дрон вошел в зону ракеты?
            dist_to_rocket = math.hypot(
                self.drone_pos[0] - self.missile_pos[0],
                self.drone_pos[1] - self.missile_pos[1])
            if dist_to_rocket <= self.zone_radius_km and not self.drone_detected:
                self.drone_detected = True
                self.tracking_active = True

        # Движение ракеты (преследование, если дрон обнаружен)
        if self.tracking_active and not self.explosion:
            dist_to_drone = math.hypot(
                self.missile_pos[0] - self.drone_pos[0],
                self.missile_pos[1] - self.drone_pos[1])

            if dist_to_drone > 0:
                # Направление к дрону
                dir_x = (self.drone_pos[0] -
                         self.missile_pos[0]) / dist_to_drone
                dir_y = (self.drone_pos[1] -
                         self.missile_pos[1]) / dist_to_drone
                self.missile_pos[0] += dir_x * self.speed_missile * dt
                self.missile_pos[1] += dir_y * self.speed_missile * dt
                self.missile_distance += self.speed_missile * dt

                # Проверка перехвата
                new_dist = math.hypot(
                    self.missile_pos[0] - self.drone_pos[0],
                    self.missile_pos[1] - self.drone_pos[1])
                if new_dist < 0.1:
                    self.explosion = True
                    self.explosion_time = 0
                    self.intercepted = True

        # Обновление взрыва
        if self.explosion:
            self.explosion_time += dt
            if self.explosion_time >= self.explosion_duration:
                self.simulation_finished = True

    def handle_setup_events(self):
        """Обработка событий на экране настройки"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            self.drone_speed_input.handle_event(event)
            self.missile_speed_input.handle_event(event)
            self.zone_radius_input.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.start_button.update(event.pos)
                if self.start_button.is_clicked(event.pos):
                    drone_val = self.drone_speed_input.get_value()
                    missile_val = self.missile_speed_input.get_value()
                    zone_val = self.zone_radius_input.get_value()

                    if drone_val and missile_val and zone_val:
                        self.speed_drone_kmh = drone_val
                        self.speed_missile_kmh = missile_val
                        self.zone_radius_km = zone_val
                        self.state = STATE_RUNNING
                        self.reset_simulation()
            else:
                self.start_button.update(pygame.mouse.get_pos())

        return True

    def handle_simulation_events(self):
        """Обработка событий на экране симуляции"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.pause_button.update(event.pos)
                self.reset_button.update(event.pos)

                if self.pause_button.is_clicked(event.pos):
                    self.simulation_paused = not self.simulation_paused

                if self.reset_button.is_clicked(event.pos):
                    self.state = STATE_SETUP
                    self.drone_speed_input.set_value(self.speed_drone_kmh)
                    self.missile_speed_input.set_value(self.speed_missile_kmh)
                    self.zone_radius_input.set_value(self.zone_radius_km)
            else:
                self.pause_button.update(pygame.mouse.get_pos())
                self.reset_button.update(pygame.mouse.get_pos())

        return True

    def run(self):
        """Главный цикл"""
        running = True
        while running:
            if self.state == STATE_SETUP:
                self.draw_setup_screen()
                running = self.handle_setup_events()
            else:
                self.update_simulation()
                self.draw_simulation_screen()
                running = self.handle_simulation_events()

            self.clock.tick(30)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = SimulationApp()
    app.run()
