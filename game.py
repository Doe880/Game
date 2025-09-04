# -*- coding: utf-8 -*-
import random
import sys
import pygame

# -------------------- БАЗОВЫЕ НАСТРОЙКИ --------------------
WIDTH, HEIGHT = 980, 640
FPS = 60

BG_COLOR = (245, 247, 250)
INK = (30, 33, 36)
MUTED = (120, 130, 140)
ACCENT = (50, 120, 220)
GOOD = (30, 170, 90)
BAD = (220, 70, 70)
BTN_BG = (230, 235, 240)
BTN_USED = (205, 210, 215)
PANEL = (255, 255, 255)
BORDER = (230, 235, 240)

MAX_MISTAKES = 6
ROUND_TIME = 90  # секунд на раунд

# Максимальные размеры шрифтов (фактические будут подбираться динамически)
MAX_XL, MAX_L, MAX_M, MAX_S = 44, 32, 24, 18

# Русская «клавиатура»
KEYBOARD_ROWS = [
    list("ЙЦУКЕНГШЩЗХЪ"),
    list("ФЫВАПРОЛДЖЭ"),
    list("ЯЧСМИТЬБЮЁ"),
]

# Категории слов (в ВЕРХНЕМ регистре)
WORDS_BY_CATEGORY = {
    "ТЕХНИКА": [
        "КОМПЬЮТЕР","АЛГОРИТМ","ИНТЕРФЕЙС","ПРОГРАММИСТ","СЕРВЕР","БИБЛИОТЕКА",
        "ПРИЛОЖЕНИЕ","ПАРАМЕТР","ФУНКЦИЯ","ДАННЫЕ","ЛОГИКА","ПИТОН","НЕЙРОСЕТЬ"
    ],
    "КОСМОС": [
        "РАКЕТА","КОСМОС","ЗВЕЗДА","ГРАВИТАЦИЯ","ПУЛЬСАР","КВАНТ","СИНТЕЗ","ВИХРЬ"
    ],
    "ПРИРОДА": [
        "СНЕЖИНКА","ОКЕАН","МОЛЕКУЛА","ЖИРАФ","КАРТИНА","РЕАЛЬНОСТЬ","ТЕТРАДЬ","ЭНЕРГИЯ"
    ],
    "С Ё-БУКВАМИ": [
        "ЁЛКА","ЁМКОСТЬ","ШЁПОТ"
    ]
}
for k in list(WORDS_BY_CATEGORY.keys()):
    WORDS_BY_CATEGORY[k] = [w.upper() for w in WORDS_BY_CATEGORY[k]]
CATEGORIES = list(WORDS_BY_CATEGORY.keys())

# -------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ --------------------
def choose_word(category):
    return random.choice(WORDS_BY_CATEGORY[category])

def draw_text(surface, text, font, color, pos, center=False):
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(img, rect)
    return rect

def fit_font(base_font_name, text, max_width, max_size, min_size=14):
    """Подбор размера шрифта так, чтобы строка помещалась по ширине."""
    size = max_size
    while size > min_size:
        f = pygame.font.Font(base_font_name, size)
        if f.size(text)[0] <= max_width:
            return f
        size -= 1
    return pygame.font.Font(base_font_name, min_size)

def ellipsize(text, font, max_width):
    """Если не влезает, укорачивает текст и добавляет '…'."""
    if font.size(text)[0] <= max_width:
        return text
    ell = "…"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi) // 2
        if font.size(text[:mid] + ell)[0] <= max_width:
            lo = mid + 1
        else:
            hi = mid
    return text[:max(1, lo - 1)] + ell

def build_keyboard(area_rect, cols_row0):
    """Создаёт кнопки букв в указанной области с учётом текущего размера."""
    padding = 8
    rows = len(KEYBOARD_ROWS)
    # Распределяем высоту: три ряда + отступы
    btn_h = max(34, (area_rect.height - (rows + 1) * (padding + 2)) // rows)
    buttons = []
    y = area_rect.top + padding
    for row in KEYBOARD_ROWS:
        cols = len(row)
        btn_w = max(30, (area_rect.width - (cols + 1) * padding) // cols)
        x = area_rect.left + padding
        for ch in row:
            rect = pygame.Rect(x, y, btn_w, btn_h)
            buttons.append((ch, rect))
            x += btn_w + padding
        y += btn_h + padding
    return buttons

def normalize_letter(ch):
    if not ch:
        return None
    up = ch.upper()
    if 'А' <= up <= 'Я' or up == 'Ё':
        return up
    return None

def letters_equal(a, b, eyo_equiv):
    if a == b:
        return True
    if eyo_equiv and ((a == 'Е' and b == 'Ё') or (a == 'Ё' and b == 'Е')):
        return True
    return False

def all_letters_guessed(word, guessed, eyo_equiv):
    for ch in set(word):
        if ch in guessed:
            continue
        if eyo_equiv and ch in {'Е','Ё'} and (('Е' in guessed) or ('Ё' in guessed)):
            continue
        return False
    return True

def reveal_random_letter(state):
    """Открывает случайную скрытую букву; стоимость — +1 ошибка."""
    word = state["word"]
    hidden = []
    for ch in set(word):
        show = (ch in state["guessed"])
        if not show and state["eyo_equiv"] and ch in {'Е','Ё'} and (('Е' in state["guessed"]) or ('Ё' in state["guessed"])):
            show = True
        if not show:
            hidden.append(ch)
    if not hidden:
        return False
    to_reveal = random.choice(hidden)
    state["guessed"].add(to_reveal)
    state["mistakes"] = min(MAX_MISTAKES, state["mistakes"] + 1)
    return True

# -------------------- ОТРИСОВКА ВИСЕЛИЦЫ --------------------
def draw_gallows(surface, base_x, base_y, mistakes):
    pygame.draw.line(surface, MUTED, (base_x, base_y), (base_x + 220, base_y), 6)      # земля
    pygame.draw.line(surface, MUTED, (base_x + 50, base_y), (base_x + 50, base_y - 280), 6)  # столб
    pygame.draw.line(surface, MUTED, (base_x + 50, base_y - 280), (base_x + 170, base_y - 280), 6)  # балка
    pygame.draw.line(surface, MUTED, (base_x + 170, base_y - 280), (base_x + 170, base_y - 230), 4)  # верёвка
    cx, cy = base_x + 170, base_y - 210
    if mistakes > 0: pygame.draw.circle(surface, BAD, (cx, cy), 20, 3)                       # голова
    if mistakes > 1: pygame.draw.line(surface, BAD, (cx, cy + 20), (cx, cy + 95), 3)         # тело
    if mistakes > 2: pygame.draw.line(surface, BAD, (cx, cy + 45), (cx - 32, cy + 75), 3)    # левая рука
    if mistakes > 3: pygame.draw.line(surface, BAD, (cx, cy + 45), (cx + 32, cy + 75), 3)    # правая рука
    if mistakes > 4: pygame.draw.line(surface, BAD, (cx, cy + 95), (cx - 25, cy + 130), 3)   # левая нога
    if mistakes > 5: pygame.draw.line(surface, BAD, (cx, cy + 95), (cx + 25, cy + 130), 3)   # правая нога

# -------------------- АДАПТИВНАЯ РАЗМЕТКА --------------------
def compute_layout(w, h):
    """Считает прямоугольники панелей и кнопок под текущее окно."""
    left_panel  = pygame.Rect(20, 20, max(360, int(w * 0.4) - 40), h - 40)
    right_panel = pygame.Rect(left_panel.right + 20, 20, w - (left_panel.width + 60), h - 40)
    kb_area = pygame.Rect(right_panel.left, right_panel.top + int(h * 0.36), right_panel.width, int(h * 0.32))

    btn_h = 44
    yb = right_panel.bottom - (btn_h + 12)
    btn_hint  = pygame.Rect(right_panel.left + 16, yb, 210, btn_h)
    btn_again = pygame.Rect(btn_hint.right + 12, yb, 180, btn_h)
    btn_eyo   = pygame.Rect(btn_again.right + 12, yb, 150, btn_h)
    btn_cat   = pygame.Rect(right_panel.left + 16, right_panel.top + 170, 260, 40)
    return left_panel, right_panel, kb_area, btn_hint, btn_again, btn_eyo, btn_cat

def draw_btn(surface, base_font, rect, label, bg, max_size=22):
    f = fit_font(base_font, label, rect.width - 12, max_size, min_size=14)
    pygame.draw.rect(surface, bg, rect, border_radius=10)
    draw_text(surface, label, f, (255, 255, 255), rect.center, center=True)

# -------------------- ОСНОВНАЯ ИГРА --------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Виселица (pygame): категории, таймер, подсказки, Е=Ё")
    clock = pygame.time.Clock()

    # Шрифт с кириллицей (одно имя; размеры подбираем динамически)
    base_font = pygame.font.match_font("arial,dejavusans,noto sans,verdana,liberation sans")

    # Разметка и клавиатура
    left_panel, right_panel, kb_area, btn_hint, btn_again, btn_eyo, btn_cat = compute_layout(WIDTH, HEIGHT)
    buttons = build_keyboard(kb_area, cols_row0=len(KEYBOARD_ROWS[0]))

    cat_idx = 0

    def reset_game(category, keep_eyo=None):
        word = choose_word(category)
        return {
            "category": category,
            "word": word,
            "guessed": set(),
            "used": set(),
            "mistakes": 0,
            "won": False,
            "lost": False,
            "eyo_equiv": True if keep_eyo is None else keep_eyo,
            "time_left": ROUND_TIME,
            "started_ticks": pygame.time.get_ticks()
        }

    state = reset_game(CATEGORIES[cat_idx])

    running = True
    while running:
        dt_ms = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Ресайз окна — пересчитать раскладку
            if event.type == pygame.VIDEORESIZE:
                new_w, new_h = max(800, event.w), max(540, event.h)
                screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
                left_panel, right_panel, kb_area, btn_hint, btn_again, btn_eyo, btn_cat = compute_layout(new_w, new_h)
                buttons = build_keyboard(kb_area, cols_row0=len(KEYBOARD_ROWS[0]))

            # Клики мышью
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # Смена категории -> новая игра
                if btn_cat.collidepoint(mx, my) and not (state["won"] or state["lost"]):
                    cat_idx = (cat_idx + 1) % len(CATEGORIES)
                    state = reset_game(CATEGORIES[cat_idx], keep_eyo=state["eyo_equiv"])
                    continue

                # Подсказка
                if btn_hint.collidepoint(mx, my) and not (state["won"] or state["lost"]):
                    if state["mistakes"] < MAX_MISTAKES:
                        reveal_random_letter(state)

                # Сыграть ещё
                if btn_again.collidepoint(mx, my):
                    state = reset_game(state["category"], keep_eyo=state["eyo_equiv"])
                    continue

                # Переключатель Е=Ё
                if btn_eyo.collidepoint(mx, my):
                    state["eyo_equiv"] = not state["eyo_equiv"]
                    continue

                # Виртуальная клавиатура
                if not (state["won"] or state["lost"]):
                    for ch, rect in buttons:
                        if rect.collidepoint(mx, my):
                            if ch not in state["used"]:
                                state["used"].add(ch)
                                if any(letters_equal(ch, wch, state["eyo_equiv"]) for wch in state["word"]):
                                    for wch in set(state["word"]):
                                        if letters_equal(ch, wch, state["eyo_equiv"]):
                                            state["guessed"].add(wch)
                                else:
                                    state["mistakes"] += 1
                            break

            # Физическая клавиатура
            if event.type == pygame.KEYDOWN and not (state["won"] or state["lost"]):
                letter = normalize_letter(event.unicode)
                if letter and letter not in state["used"]:
                    state["used"].add(letter)
                    if any(letters_equal(letter, wch, state["eyo_equiv"]) for wch in state["word"]):
                        for wch in set(state["word"]):
                            if letters_equal(letter, wch, state["eyo_equiv"]):
                                state["guessed"].add(wch)
                    else:
                        state["mistakes"] += 1

        # Таймер
        if not (state["won"] or state["lost"]):
            passed = (pygame.time.get_ticks() - state["started_ticks"]) // 1000
            state["time_left"] = max(0, ROUND_TIME - passed)
            if state["time_left"] == 0:
                state["lost"] = True

        # Победа/поражение
        if not (state["won"] or state["lost"]):
            if all_letters_guessed(state["word"], state["guessed"], state["eyo_equiv"]):
                state["won"] = True
            elif state["mistakes"] >= MAX_MISTAKES:
                state["lost"] = True

        # -------------------- ОТРИСОВКА --------------------
        screen.fill(BG_COLOR)

        # Левая панель
        pygame.draw.rect(screen, PANEL, left_panel, border_radius=16)
        pygame.draw.rect(screen, BORDER, left_panel, 2, border_radius=16)
        title_font = fit_font(base_font, "Виселица", left_panel.width - 32, MAX_XL, 20)
        draw_text(screen, "Виселица", title_font, INK, (left_panel.left + 16, left_panel.top + 12))

        # Виселица
        gallows_base_y = left_panel.top + int(left_panel.height * 0.65)
        draw_gallows(screen, left_panel.left + 40, gallows_base_y, state["mistakes"])

        # Прогресс/таймер
        stat_font = fit_font(base_font, "Ошибок: 0/0", left_panel.width - 32, MAX_L, 16)
        draw_text(screen, f"Ошибок: {state['mistakes']} / {MAX_MISTAKES}", stat_font, MUTED, (left_panel.left + 16, gallows_base_y + 20))

        time_color = GOOD if state["time_left"] > 20 else (BAD if state["time_left"] <= 10 else ACCENT)
        time_font = fit_font(base_font, "Время: 00 сек", left_panel.width - 32, MAX_L, 16)
        draw_text(screen, f"Время: {state['time_left']:02d} сек", time_font, time_color, (left_panel.left + 16, gallows_base_y + 56))

        wrong_letters = [ch for ch in state["used"] if not any(letters_equal(ch, wch, state["eyo_equiv"]) for wch in set(state["word"]))]
        wrong_label_f = fit_font(base_font, "Неверные:", left_panel.width - 32, MAX_M, 14)
        wrong_text_f  = fit_font(base_font, "А Б В", left_panel.width - 32, MAX_M, 14)
        draw_text(screen, "Неверные:", wrong_label_f, MUTED, (left_panel.left + 16, gallows_base_y + 92))
        wrong_str = " ".join(sorted(wrong_letters)) if wrong_letters else "—"
        draw_text(screen, wrong_str, wrong_text_f, BAD, (left_panel.left + 16, gallows_base_y + 120))

        # Правая панель
        pygame.draw.rect(screen, PANEL, right_panel, border_radius=16)
        pygame.draw.rect(screen, BORDER, right_panel, 2, border_radius=16)

        # Категория (усекаем при необходимости)
        cat_area_w = right_panel.width - 32
        cat_full = f"Категория: {state['category']}"
        font_cat = fit_font(base_font, cat_full, cat_area_w, MAX_M, 14)
        cat_text = ellipsize(cat_full, font_cat, cat_area_w)
        draw_text(screen, cat_text, font_cat, MUTED, (right_panel.left + 16, right_panel.top + 16))

        # Кнопка смены категории
        pygame.draw.rect(screen, BTN_BG, btn_cat, border_radius=10)
        pygame.draw.rect(screen, BORDER, btn_cat, 1, border_radius=10)
        draw_btn(screen, base_font, btn_cat, "Сменить категорию", INK, max_size=18)

        # Слово
        display_word = []
        for ch in state["word"]:
            show = (ch in state["guessed"])
            if not show and state["eyo_equiv"] and ch in {'Е','Ё'} and (('Е' in state["guessed"]) or ('Ё' in state["guessed"])):
                show = True
            display_word.append(ch if show else "•")
        word_str = " ".join(display_word)

        label_str = "Угадайте слово:"
        label_font = fit_font(base_font, label_str, cat_area_w, MAX_M, 14)
        draw_text(screen, label_str, label_font, MUTED, (right_panel.left + 16, right_panel.top + 70))

        font_word = fit_font(base_font, word_str, cat_area_w, MAX_XL, 18)
        draw_text(screen, word_str, font_word, INK, (right_panel.left + 16, right_panel.top + 110))

        # Подсказка к управлению (усекаем)
        hint_line = "Кликайте по клавишам или печатайте с физической клавиатуры"
        hint_font = fit_font(base_font, hint_line, cat_area_w, MAX_S, 12)
        hint_line = ellipsize(hint_line, hint_font, cat_area_w)
        draw_text(screen, hint_line, hint_font, MUTED, (right_panel.left + 16, right_panel.top + 210))

        # Клавиатура
        for ch, rect in buttons:
            used = ch in state["used"]
            bg = BTN_USED if used else BTN_BG
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, BORDER, rect, 1, border_radius=8)
            key_font = fit_font(base_font, ch, rect.width - 8, MAX_M, 14)
            color = MUTED if used else INK
            draw_text(screen, ch, key_font, color, rect.center, center=True)

        # Нижние кнопки
        draw_btn(screen, base_font, btn_hint, "Подсказка (-1 жизнь)", ACCENT, max_size=22)
        draw_btn(screen, base_font, btn_again, "Сыграть ещё", ACCENT, max_size=22)
        draw_btn(screen, base_font, btn_eyo, f"Е=Ё: {'ВКЛ' if state['eyo_equiv'] else 'ВЫКЛ'}",
                 GOOD if state['eyo_equiv'] else MUTED, max_size=22)

        # Результат раунда (оверлей, также подбираем шрифт)
        if state["won"] or state["lost"]:
            overlay_w = right_panel.width - 32
            overlay_h = 120
            overlay_y = int(right_panel.top + right_panel.height * 0.68)
            overlay = pygame.Surface((overlay_w, overlay_h), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 235))
            screen.blit(overlay, (right_panel.left + 16, overlay_y))

            msg_text = "Победа! Слово:" if state["won"] else "Поражение. Слово:"
            msg_color = GOOD if state["won"] else BAD
            font_msg = fit_font(base_font, msg_text, overlay_w - 20, MAX_L, 16)
            font_ans = fit_font(base_font, state["word"], overlay_w - 20, MAX_XL, 18)
            draw_text(screen, msg_text, font_msg, msg_color, (right_panel.left + 30, overlay_y + 10))
            draw_text(screen, state["word"], font_ans, INK, (right_panel.left + 30, overlay_y + 48))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
