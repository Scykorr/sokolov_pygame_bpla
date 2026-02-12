import pygame
import sys
import math
import random

# Инициализация Pygame
pygame.init()

# Параметры окна (в км, но масштабируем для отображения)
WIDTH, HEIGHT = 800, 600
SCALE = 50  # 1 км = 50 пикселей (можно менять)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Квадрокоптер vs Ракета")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)      # Квадрокоптер
RED = (255, 50, 50)       # Ракета
GREEN = (50, 200, 50)     # Зона
YELLOW = (255, 255, 0)    # Взрыв
GRAY = (100, 100, 100)

font = pygame.font.SysFont(None, 24)

# Ввод параметров пользователем
def get_input(prompt):
    while True:
        try:
            val = float(input(prompt))
            if val <= 0:
                print("Значение должно быть положительным.")
                continue
            return val
        except ValueError:
            print("Введите корректное число.")

print("=== Настройка симуляции ===")
speed_drone_kmh = get_input("Скорость квадрокоптера (км/ч): ")
speed_missile_kmh = get_input("Скорость ракеты (км/ч): ")
zone_radius_km = get_input("Радиус зоны вокруг квадрокоптера (км): ")

# Перевод скоростей в км/с
speed_drone = speed_drone_kmh / 3600.0
speed_missile = speed_missile_kmh / 3600.0

# Начальные координаты (в км)
center_x_km = WIDTH / (2 * SCALE)
center_y_km = HEIGHT / (2 * SCALE)

drone_pos = [center_x_km, center_y_km]
missile_active = False
missile_pos = [0.0, 0.0]
missile_angle = 0.0
missile_direction_change_timer = 0
missile_direction_change_interval = random.uniform(2, 6)

# Состояние взрыва
explosion = False
explosion_time = 0
explosion_duration = 1.0

# Счётчики
time_elapsed = 0.0
drone_distance = 0.0
missile_distance = 0.0
intercepted = False
simulation_finished = False

# Часы для управления временем
clock = pygame.time.Clock()
dt = 1.0

# Генерация начальной позиции ракеты
def spawn_missile():
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
    angle = math.atan2(center_y_km - y, center_x_km - x)
    return [x, y], angle

# Основной цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if simulation_finished:
        continue

    # Обновление времени
    time_elapsed += dt / 3600.0

    # Спавн ракеты, если ещё не активна
    if not missile_active:
        missile_pos, missile_angle = spawn_missile()
        missile_active = True

    # Движение ракеты
    if missile_active and not explosion:
        # Изменение направления каждые N секунд
        missile_direction_change_timer += dt
        if missile_direction_change_timer >= missile_direction_change_interval:
            turn = random.uniform(-math.pi/6, math.pi/6)
            missile_angle += turn
            missile_direction_change_timer = 0
            missile_direction_change_interval = random.uniform(2, 6)

        # Движение
        dx = math.cos(missile_angle) * speed_missile * dt
        dy = math.sin(missile_angle) * speed_missile * dt
        missile_pos[0] += dx
        missile_pos[1] += dy
        missile_distance += speed_missile * dt

        # Проверка: пересекла ли ракета зону?
        dist_to_drone = math.hypot(missile_pos[0] - drone_pos[0], missile_pos[1] - drone_pos[1])
        if dist_to_drone <= zone_radius_km and not intercepted:
            pass

    # Движение квадрокоптера (если ракета внутри зоны)
    if missile_active and not explosion:
        dist_to_missile = math.hypot(missile_pos[0] - drone_pos[0], missile_pos[1] - drone_pos[1])
        if dist_to_missile <= zone_radius_km:
            # Направление к ракете
            if dist_to_missile > 0:
                dir_x = (missile_pos[0] - drone_pos[0]) / dist_to_missile
                dir_y = (missile_pos[1] - drone_pos[1]) / dist_to_missile
                drone_pos[0] += dir_x * speed_drone * dt
                drone_pos[1] += dir_y * speed_drone * dt
                drone_distance += speed_drone * dt

            # Проверка перехвата
            new_dist = math.hypot(missile_pos[0] - drone_pos[0], missile_pos[1] - drone_pos[1])
            if new_dist < 0.1:
                explosion = True
                explosion_time = 0
                intercepted = True

    # Обновление взрыва
    if explosion:
        explosion_time += dt
        if explosion_time >= explosion_duration:
            simulation_finished = True

    # Отрисовка
    screen.fill(WHITE)

    # Преобразование координат км → пиксели
    def km_to_px(x_km, y_km):
        return int(x_km * SCALE), int(y_km * SCALE)

    # Зона (окружность)
    cx, cy = km_to_px(drone_pos[0], drone_pos[1])
    pygame.draw.circle(screen, GREEN, (cx, cy), int(zone_radius_km * SCALE), 2)

    # Квадрокоптер
    pygame.draw.rect(screen, BLUE, (cx - 5, cy - 5, 10, 10))

    # Ракета
    if missile_active and not explosion:
        mx, my = km_to_px(missile_pos[0], missile_pos[1])
        pygame.draw.polygon(screen, RED, [
            (mx, my),
            (mx - 8 * math.cos(missile_angle), my - 8 * math.sin(missile_angle)),
            (mx - 6 * math.cos(missile_angle) - 3 * math.sin(missile_angle),
             my - 6 * math.sin(missile_angle) + 3 * math.cos(missile_angle)),
            (mx - 6 * math.cos(missile_angle) + 3 * math.sin(missile_angle),
             my - 6 * math.sin(missile_angle) - 3 * math.cos(missile_angle))
        ])

    # Взрыв
    if explosion:
        ex, ey = km_to_px(missile_pos[0], missile_pos[1])
        radius = int(20 * (explosion_time / explosion_duration))
        pygame.draw.circle(screen, YELLOW, (ex, ey), radius)
        pygame.draw.circle(screen, RED, (ex, ey), radius // 2)

    # Информация
    info_lines = [
        f"Время: {time_elapsed:.3f} ч",
        f"Пройдено дроном: {drone_distance:.3f} км",
        f"Пройдено ракетой: {missile_distance:.3f} км",
        f"Скорость дрона: {speed_drone_kmh} км/ч",
        f"Скорость ракеты: {speed_missile_kmh} км/ч",
    ]
    if simulation_finished:
        if intercepted:
            info_lines.append("✅ Ракета перехвачена!")
        else:
            info_lines.append("❌ Ракета ушла!")

    for i, line in enumerate(info_lines):
        text = font.render(line, True, BLACK)
        screen.blit(text, (10, 10 + i * 25))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()