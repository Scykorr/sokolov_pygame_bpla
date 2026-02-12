"""Генерирует спрайты (изображения) для дрона и ракеты"""
from PIL import Image, ImageDraw

def create_rocket_sprite(filename, size=50):
    """Создает изображение ракеты"""
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Ракета - треугольник с острием вверх (красная)
    tip = (size // 2, 5)
    left = (10, size - 5)
    right = (size - 10, size - 5)
    
    # Основное тело ракеты (красное)
    draw.polygon([tip, left, right], fill=(255, 50, 50, 255))
    
    # Желтая окружность (двигатель)
    center = (size // 2, size // 2)
    radius = size // 5
    draw.ellipse(
        [center[0] - radius, center[1] - radius, 
         center[0] + radius, center[1] + radius],
        fill=(255, 255, 0, 255)
    )
    
    img.save(filename)
    print(f"✓ Ракета сохранена в {filename}")

def create_drone_sprite(filename, size=50):
    """Создает изображение дрона (квадрокоптера)"""
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    center = size // 2
    
    # Центральное тело (квадрат, синий)
    body_size = size // 5
    draw.rectangle(
        [center - body_size, center - body_size,
         center + body_size, center + body_size],
        fill=(0, 100, 255, 255)
    )
    
    # Четыре пропеллера (крест)
    arm_length = size // 3
    arm_width = 3
    
    # Вертикальная линия
    draw.rectangle(
        [center - arm_width, center - arm_length,
         center + arm_width, center + arm_length],
        fill=(0, 100, 255, 255)
    )
    
    # Горизонтальная линия
    draw.rectangle(
        [center - arm_length, center - arm_width,
         center + arm_length, center + arm_width],
        fill=(0, 100, 255, 255)
    )
    
    # Четыре окружности (винты)
    prop_radius = size // 8
    for x_offset, y_offset in [(arm_length, 0), (-arm_length, 0), (0, arm_length), (0, -arm_length)]:
        x = center + x_offset
        y = center + y_offset
        draw.ellipse(
            [x - prop_radius, y - prop_radius,
             x + prop_radius, y + prop_radius],
            fill=(0, 150, 255, 200)
        )
    
    # Центральная окружность
    draw.ellipse(
        [center - body_size - 2, center - body_size - 2,
         center + body_size + 2, center + body_size + 2],
        outline=(0, 100, 255, 255),
        width=2
    )
    
    img.save(filename)
    print(f"✓ Дрон сохранен в {filename}")

if __name__ == "__main__":
    create_rocket_sprite("rocket.png", size=60)
    create_drone_sprite("drone.png", size=60)
    print("\n Спрайты успешно созданы!")
