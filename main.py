import pygame
import sys
import math
import random

# Инициализация Pygame
pygame.init()

# Параметры окна (совпадают с tkinter версией)
WIDTH_KM = 16.0   # ширина карты в км
HEIGHT_KM = 12.0  # высота карты в км
SCALE = 45        # пикселей на 1 км
WIDTH = int(WIDTH_KM * SCALE)    # 720 px
HEIGHT = int(HEIGHT_KM * SCALE)  # 540 px

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🚁 Квадрокоптер vs Ракета — Симуляция перехвата")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (59, 130, 246)  # Более яркий синий
RED = (239, 68, 68)    # Более яркий красный
GREEN = (34, 197, 94)
YELLOW = (255, 204, 0)
GRAY = (150, 150, 150)
DARK_GRAY = (100, 100, 100)
LIGHT_BLUE = (230, 247, 255)
LIGHT_GRAY = (160, 196, 255)

font_small = pygame.font.SysFont(None, 18)
font_medium = pygame.font.SysFont(None, 22)
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

        if self.active:
            color = LIGHT_BLUE
        elif self.error:
            color = (255, 100, 100)
        else:
            color = WHITE
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

        # Поля ввода (со значениями по умолчанию)
        input_y = 150
        self.drone_speed_input = InputField(
            100, input_y, 200, 35, "Скорость дрона (км/ч):", 80, 0.1, 200)
        self.missile_speed_input = InputField(
            100, input_y + 80, 200, 35, "Скорость ракеты (км/ч):", 120, 0.1, 500)
        self.zone_radius_input = InputField(
            100, input_y + 160, 200, 35, "Радиус зоны (км):", 3.0, 0.1, 20)

        # Кнопки
        self.start_button = Button(
            100, 350, 160, 50, "▶️ Старт", color=(100, 200, 100))
        self.pause_button = Button(
            600, 10, 100, 40, "⏸ Пауза", color=(200, 150, 50))
        self.reset_button = Button(
            720, 10, 100, 40, "🔄 Сброс", color=(200, 50, 50))

        # Переменные симуляции
        self.speed_drone_kmh = 80.0
        self.speed_missile_kmh = 120.0
        self.zone_radius_km = 3.0

        self.clock = pygame.time.Clock()
        self.reset_simulation()

    def km_to_px(self, x_km, y_km):
        """
        Преобразование из км в пиксели.
        Начало (0,0) км = левый НИЖНИЙ угол.
        Canvas (0,0) = левый верхний угол → инвертируем Y.
        """
        px_x = int(x_km * SCALE)
        px_y = int((HEIGHT_KM - y_km) * SCALE)
        return px_x, px_y

    def reset_simulation(self):
        """Сброс симуляции"""
        self.speed_drone = self.speed_drone_kmh / 3600.0  # км/сек
        self.speed_missile = self.speed_missile_kmh / 3600.0  # км/сек

        # Дрон в центре карты (8, 6) км
        self.drone_pos = [WIDTH_KM / 2, HEIGHT_KM / 2]

        # Ракета изначально неактивна
        self.missile_pos = [0.0, 0.0]
        self.missile_angle = 0.0
        self.missile_active = False
        self.missile_direction_change_timer = 0
        self.missile_direction_change_interval = random.uniform(2, 6)

        self.explosion = False
        self.explosion_time = 0.0
        self.explosion_duration = 1.0

        self.time_elapsed = 0.0
        self.drone_distance = 0.0
        self.missile_distance = 0.0
        self.intercepted = False
        self.simulation_finished = False
        self.simulation_paused = False

    def spawn_missile(self):
        """Генерация стартовой позиции ракеты на краю карты"""
        side = random.choice(['top', 'bottom', 'left', 'right'])
        margin_km = 0.3  # минимальный отступ за край

        if side == 'top':
            x = random.uniform(1, WIDTH_KM - 1)
            y = HEIGHT_KM + margin_km
        elif side == 'bottom':
            x = random.uniform(1, WIDTH_KM - 1)
            y = -margin_km
        elif side == 'left':
            x = -margin_km
            y = random.uniform(1, HEIGHT_KM - 1)
        else:  # right
            x = WIDTH_KM + margin_km
            y = random.uniform(1, HEIGHT_KM - 1)

        # Направление на дрон (в центре)
        angle = math.atan2(self.drone_pos[1] - y, self.drone_pos[0] - x)
        return [x, y], angle

    def draw_setup_screen(self):
        """Рисует экран настройки"""
        screen.fill(WHITE)

        title = font_large.render("🚁 Квадрокоптер vs Ракета", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        subtitle = font_medium.render("Симуляция перехвата", True, DARK_GRAY)
        screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 75))

        self.drone_speed_input.draw(screen)
        self.missile_speed_input.draw(screen)
        self.zone_radius_input.draw(screen)
        self.start_button.draw(screen)

        if any([self.drone_speed_input.error, self.missile_speed_input.error, self.zone_radius_input.error]):
            error_text = font_small.render("Ошибка: проверьте значения!", True, RED)
            screen.blit(error_text, (100, 420))

        pygame.display.flip()

    def draw_simulation_screen(self):
        """Рисует экран симуляции"""
        screen.fill(LIGHT_BLUE)

        # Кнопки управления
        self.pause_button.text = "▶️ Возобн." if self.simulation_paused else "⏸ Пауза"
        self.pause_button.draw(screen)
        self.reset_button.draw(screen)

        # Дрон в центре (8, 6) км
        drone_px = self.km_to_px(self.drone_pos[0], self.drone_pos[1])
        cx, cy = drone_px

        # Зона обнаружения (окружность вокруг дрона)
        zone_radius_px = int(self.zone_radius_km * SCALE)
        pygame.draw.circle(screen, GREEN, (cx, cy), zone_radius_px, 2)

        # Подпись зоны
        zone_text = font_small.render(f"Зона {self.zone_radius_km} км", True, GREEN)
        screen.blit(zone_text, (cx - zone_text.get_width() // 2, cy - zone_radius_px - 20))

        # Дрон (квадрат с цветом) в CENTER
        drone_size = 15
        pygame.draw.rect(screen, BLUE, (cx - drone_size, cy - drone_size,
                                        drone_size * 2, drone_size * 2))
        pygame.draw.rect(screen, (30, 60, 150), (cx - drone_size, cy - drone_size,
                                                   drone_size * 2, drone_size * 2), 2)

        # Ракета (треугольник)
        if self.missile_active and not self.explosion:
            mx, my = self.km_to_px(self.missile_pos[0], self.missile_pos[1])

            # Проверка видимости (с запасом)
            if (-50 <= mx <= WIDTH + 50) and (-50 <= my <= HEIGHT + 50):
                # Треугольник указывает в направлении полета
                tip_x = mx + 15 * math.cos(self.missile_angle)
                tip_y = my + 15 * math.sin(self.missile_angle)

                side_angle = math.pi / 2
                left_x = mx + 8 * math.cos(self.missile_angle + side_angle)
                left_y = my + 8 * math.sin(self.missile_angle + side_angle)
                right_x = mx + 8 * math.cos(self.missile_angle - side_angle)
                right_y = my + 8 * math.sin(self.missile_angle - side_angle)

                pygame.draw.polygon(screen, RED, [
                    (tip_x, tip_y), (left_x, left_y), (right_x, right_y)
                ])
                pygame.draw.polygon(screen, (180, 20, 20), [
                    (tip_x, tip_y), (left_x, left_y), (right_x, right_y)
                ], 2)

        # Взрыв
        if self.explosion:
            ex, ey = cx, cy  # взрыв в центре (где дрон)
            progress = min(1.0, self.explosion_time / self.explosion_duration)
            base_radius = 20

            colors = [YELLOW, (255, 165, 0), (255, 69, 0), (200, 0, 0)]
            for i, color in enumerate(colors):
                radius = int(base_radius * (0.6 + 0.4 * progress) * (1.0 - i * 0.2))
                if radius > 0:
                    pygame.draw.circle(screen, color, (ex, ey), radius)

        # Статистика слева
        info_texts = [
            f"⏱ Время: {self.time_elapsed:.2f} сек",
            f"🚁 Дрон пройден: {self.drone_distance:.3f} км",
            f"🚀 Ракета пройдена: {self.missile_distance:.3f} км",
        ]

        if self.missile_active:
            dist = math.hypot(
                self.missile_pos[0] - self.drone_pos[0],
                self.missile_pos[1] - self.drone_pos[1]
            )
            info_texts.append(f"📏 Расстояние: {dist:.3f} км")
        else:
            info_texts.append("📏 Расстояние: -- км")

        if self.simulation_paused:
            info_texts.append("⏸ ПАУЗА")
        if self.simulation_finished:
            if self.intercepted:
                info_texts.append("✅ Ракета перехвачена!")
            else:
                info_texts.append("❌ Ракета ушла")

        for i, text in enumerate(info_texts):
            surf = font_small.render(text, True, BLACK)
            screen.blit(surf, (10, 60 + i * 25))

        pygame.display.flip()

    def update_simulation(self):
        """Основной цикл обновления"""
        if not self.simulation_paused:
            dt = 0.05  # шаг симуляции в секундах

            # Взрыв
            if self.explosion:
                self.explosion_time += dt
                if self.explosion_time >= self.explosion_duration:
                    self.simulation_finished = True
                    self.simulation_paused = True

            # Если ракета еще летит
            if self.missile_active and not self.explosion:
                self.time_elapsed += dt

                # Изменение направления ракеты (случайные маневры)
                self.missile_direction_change_timer += dt
                if self.missile_direction_change_timer >= self.missile_direction_change_interval:
                    turn = random.uniform(-math.pi / 6, math.pi / 6)  # ±30 градусов
                    self.missile_angle += turn
                    self.missile_direction_change_timer = 0
                    self.missile_direction_change_interval = random.uniform(2, 6)

                # Движение ракеты
                dx_m = math.cos(self.missile_angle) * self.speed_missile * dt
                dy_m = math.sin(self.missile_angle) * self.speed_missile * dt
                self.missile_pos[0] += dx_m
                self.missile_pos[1] += dy_m
                self.missile_distance += math.hypot(dx_m, dy_m)

                # Расстояние до дрона
                dist_to_drone = math.hypot(
                    self.missile_pos[0] - self.drone_pos[0],
                    self.missile_pos[1] - self.drone_pos[1]
                )

                # Движение дрона (убегает от ракеты если она в зоне)
                if dist_to_drone <= self.zone_radius_km:
                    if dist_to_drone > 0.01:
                        # Направление ВЫХОДА из опасности (от ракеты)
                        dir_x = (self.drone_pos[0] - self.missile_pos[0]) / dist_to_drone
                        dir_y = (self.drone_pos[1] - self.missile_pos[1]) / dist_to_drone
                        dx_d = dir_x * self.speed_drone * dt
                        dy_d = dir_y * self.speed_drone * dt
                        self.drone_pos[0] += dx_d
                        self.drone_pos[1] += dy_d
                        self.drone_distance += math.hypot(dx_d, dy_d)

                    # Проверка перехвата
                    new_dist = math.hypot(
                        self.missile_pos[0] - self.drone_pos[0],
                        self.missile_pos[1] - self.drone_pos[1]
                    )
                    if new_dist < 0.1 and not self.explosion:  # 100 метров
                        self.explosion = True
                        self.explosion_time = 0
                        self.intercepted = True

                # Проверка: покинула ли ракета зону досягаемости
                if (self.missile_pos[0] < -5 or self.missile_pos[0] > WIDTH_KM + 5 or
                    self.missile_pos[1] < -5 or self.missile_pos[1] > HEIGHT_KM + 5):
                    self.simulation_finished = True
                    self.simulation_paused = True
                    self.missile_active = False

        self.draw_simulation_screen()

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

                        # Спавн ракеты и запуск симуляции
                        self.missile_pos, self.missile_angle = self.spawn_missile()
                        self.missile_active = True
                        self.simulation_paused = False
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
                    self.simulation_finished = False
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
                running = self.handle_simulation_events()

            self.clock.tick(30)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = SimulationApp()
    app.run()
