# -*- coding: utf-8 -*-
"""
Виселица (pygame) — веб-версия совместима с pygbag.
Главные отличия от исходника:
- Игровой цикл сделан async (await asyncio.sleep(0) в WEB-режиме).
- Чуть упорядочены вспомогательные функции.
- Обработчик исключений и экран с трейсбеком вынесены в отдельные функции.
"""

import sys
import random
import traceback

import pygame

# --------- НАСТРОЙКИ ----------
WIDTH, HEIGHT = 960, 540
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
ROUND_TIME = 90

MAX_XL, MAX_L, MAX_M, MAX_S = 44, 32, 24, 18

# важное: относительный путь (pygbag упакует assets/)
FONT_PATH = "assets/fonts/NotoSans-Regular.ttf"

WEB = (sys.platform == "emscripten")

KEYBOARD_ROWS = [
    list("ЙЦУКЕНГШЩЗХЪ"),
    list("ФЫВАПРОЛДЖЭ"),
    list("ЯЧСМИТЬБЮЁ"),
]

WORDS_BY_CATEGORY = {
    "ТЕХНИКА": [
        "КОМПЬЮТЕР", "АЛГОРИТМ", "ИНТЕРФЕЙС", "ПРОГРАММИСТ", "СЕРВЕР", "БИБЛИОТЕКА",
        "ПРИЛОЖЕНИЕ", "ПАРАМЕТР", "ФУНКЦИЯ", "ДАННЫЕ", "ЛОГИКА", "ПИТОН", "НЕЙРОСЕТЬ"
    ],
    "КОСМОС": ["РАКЕТА", "КОСМОС", "ЗВЕЗДА", "ГРАВИТАЦИЯ", "ПУЛЬСАР", "КВАНТ", "СИНТЕЗ", "ВИХРЬ"],
    "ПРИРОДА": ["СНЕЖИНКА", "ОКЕАН", "МОЛЕКУЛА", "ЖИРАФ", "КАРТИНА", "РЕАЛЬНОСТЬ", "ТЕТРАДЬ", "ЭНЕРГИЯ"],
    "С Ё-БУКВАМИ": ["ЁЛКА", "ЁМКОСТЬ", "ШЁПОТ"]
}
CATEGORIES = list(WORDS_BY_CATEGORY.keys())

# --------- ХЕЛПЕРЫ ----------
def choose_word(cat: str) -> str:
    return random.choice(WORDS_BY_CATEGORY[cat])

def load_font(size: int) -> pygame.font.Font:
    try:
        return pygame.font.Font(FONT_PATH, size)
    except Exception:
        try:
            return pygame.font.Font(None, size)
        except Exception:
            return pygame.font.SysFont(None, size)

def fit_font(text: str, max_width: int, max_size: int, min_size: int = 14) -> pygame.font.Font:
    size = max_size
    while size > min_size:
        f = load_font(size)
        if f.size(text)[0] <= max_width:
            return f
        size -= 1
    return load_font(min_size)

def ellipsize(text: str, font: pygame.font.Font, max_width: int) -> str:
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

def draw_text(surface: pygame.Surface, text: str, font: pygame.font.Font,
              color, pos, center: bool = False) -> pygame.Rect:
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(img, rect)
    return rect

def build_keyboard(area_rect: pygame.Rect):
    padding = 8
    rows = len(KEYBOARD_ROWS)
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

def normalize_letter(ch: str | None) -> str | None:
    if not ch:
        return None
    up = ch.upper()
    return up if ('А' <= up <= 'Я' or up == 'Ё') else None

def letters_equal(a: str, b: str, eyo: bool) -> bool:
    return a == b or (eyo and ((a, b) in {('Е', 'Ё'), ('Ё', 'Е')}))

def all_letters_guessed(word: str, guessed: set[str], eyo: bool) -> bool:
    for ch in set(word):
        if ch in guessed:
            continue
        if eyo and ch in {'Е', 'Ё'} and (('Е' in guessed) or ('Ё' in guessed)):
            continue
        return False
    return True

def reveal_random_letter(state: dict) -> bool:
    hidden = []
    for ch in set(state["word"]):
        show = (ch in state["guessed"]) or (
            state["eyo_equiv"] and ch in {'Е', 'Ё'} and (('Е' in state["guessed"]) or ('Ё' in state["guessed"]))
        )
        if not show:
            hidden.append(ch)
    if not hidden:
        return False
    state["guessed"].add(random.choice(hidden))
    state["mistakes"] = min(MAX_MISTAKES, state["mistakes"] + 1)
    return True

def draw_gallows(surface: pygame.Surface, base_x: int, base_y: int, mistakes: int):
    pygame.draw.line(surface, MUTED, (base_x, base_y), (base_x + 220, base_y), 6)
    pygame.draw.line(surface, MUTED, (base_x + 50, base_y), (base_x + 50, base_y - 280), 6)
    pygame.draw.line(surface, MUTED, (base_x + 50, base_y - 280), (base_x + 170, base_y - 280), 6)
    pygame.draw.line(surface, MUTED, (base_x + 170, base_y - 280), (base_x + 170, base_y - 230), 4)
    cx, cy = base_x + 170, base_y - 210
    if mistakes > 0:
        pygame.draw.circle(surface, BAD, (cx, cy), 20, 3)
    if mistakes > 1:
        pygame.draw.line(surface, BAD, (cx, cy + 20), (cx, cy + 95), 3)
    if mistakes > 2:
        pygame.draw.line(surface, BAD, (cx, cy + 45), (cx - 32, cy + 75), 3)
    if mistakes > 3:
        pygame.draw.line(surface, BAD, (cx, cy + 45), (cx + 32, cy + 75), 3)
    if mistakes > 4:
        pygame.draw.line(surface, BAD, (cx, cy + 95), (cx - 25, cy + 130), 3)
    if mistakes > 5:
        pygame.draw.line(surface, BAD, (cx, cy + 95), (cx + 25, cy + 130), 3)

def compute_layout(w: int, h: int):
    left = pygame.Rect(20, 20, max(360, int(w * 0.4) - 40), h - 40)
    right = pygame.Rect(left.right + 20, 20, w - (left.width + 60), h - 40)
    kb_area = pygame.Rect(right.left, right.top + int(h * 0.36), right.width, int(h * 0.32))
    btn_h = 44
    yb = right.bottom - (btn_h + 12)
    btn_hint = pygame.Rect(right.left + 16, yb, 210, btn_h)
    btn_again = pygame.Rect(btn_hint.right + 12, yb, 180, btn_h)
    btn_eyo = pygame.Rect(btn_again.right + 12, yb, 150, btn_h)
    btn_cat = pygame.Rect(right.left + 16, right.top + 170, 260, 40)
    return left, right, kb_area, btn_hint, btn_again, btn_eyo, btn_cat

def draw_btn(surface: pygame.Surface, rect: pygame.Rect, label: str, bg, max_size: int = 22):
    f = fit_font(label, rect.width - 12, max_size, 14)
    pygame.draw.rect(surface, bg, rect, border_radius=10)
    draw_text(surface, label, f, (255, 255, 255), rect.center, center=True)

def new_state(cat: str, keep_eyo: bool | None = None) -> dict:
    return {
        "category": cat,
        "word": choose_word(cat),
        "guessed": set(),
        "used": set(),
        "mistakes": 0,
        "won": False,
        "lost": False,
        "eyo_equiv": True if keep_eyo is None else keep_eyo,
        "time_left": ROUND_TIME,
        "started_ticks": pygame.time.get_ticks(),
    }

# ---------- ВСПОМОГАТЕЛЬНЫЕ ЭКРАНЫ ----------
def show_traceback_screen(tb_text: str):
    """Показывает стек на экране (без краха «в никуда»)."""
    try:
        pygame.display.init()
        pygame.font.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT), 0)
        screen.fill((10, 10, 10))
        f = load_font(18)
        y = 10
        lines = ("Ошибка исполнения:",) + tuple(tb_text.splitlines())
        for line in lines:
            img = f.render(line[:120], True, (255, 80, 80))
            screen.blit(img, (10, y))
            y += 22
        pygame.display.flip()
        # держим 10 секунд, чтобы успеть увидеть
        import time
        t0 = time.time()
        while time.time() - t0 < 10:
            pygame.event.pump()
    except Exception as e2:
        print("FATAL (traceback screen):", e2)

# --------- ИГРА (ASYNC) ----------
async def run_game():
    import asyncio

    # инициализация без микшера, чтобы не споткнуться о звук
    pygame.display.init()
    pygame.font.init()

    flags = 0 if WEB else pygame.RESIZABLE
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    pygame.display.set_caption("Виселица (pygame): категории, таймер, подсказки, Е=Ё")
    clock = pygame.time.Clock()

    left, right, kb_area, btn_hint, btn_again, btn_eyo, btn_cat = compute_layout(WIDTH, HEIGHT)
    buttons = build_keyboard(kb_area)

    cat_idx = 0
    state = new_state(CATEGORIES[cat_idx])

    running = True
    while running:
        dt = clock.tick(FPS)

        # --- обработка событий ---
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if not WEB and e.type == pygame.VIDEORESIZE:
                w, h = max(800, e.w), max(540, e.h)
                screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                left, right, kb_area, btn_hint, btn_again, btn_eyo, btn_cat = compute_layout(w, h)
                buttons = build_keyboard(kb_area)

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos
                if btn_cat.collidepoint(mx, my) and not (state["won"] or state["lost"]):
                    cat_idx = (cat_idx + 1) % len(CATEGORIES)
                    state = new_state(CATEGORIES[cat_idx], keep_eyo=state["eyo_equiv"])
                    continue

                if btn_hint.collidepoint(mx, my) and not (state["won"] or state["lost"]):
                    if state["mistakes"] < MAX_MISTAKES:
                        reveal_random_letter(state)

                if btn_again.collidepoint(mx, my):
                    state = new_state(state["category"], keep_eyo=state["eyo_equiv"])
                    continue

                if btn_eyo.collidepoint(mx, my):
                    state["eyo_equiv"] = not state["eyo_equiv"]
                    continue

                if not (state["won"] or state["lost"]):
                    for ch, r in buttons:
                        if r.collidepoint(mx, my):
                            if ch not in state["used"]:
                                state["used"].add(ch)
                                if any(letters_equal(ch, wch, state["eyo_equiv"]) for wch in state["word"]):
                                    for wch in set(state["word"]):
                                        if letters_equal(ch, wch, state["eyo_equiv"]):
                                            state["guessed"].add(wch)
                                else:
                                    state["mistakes"] += 1
                            break

            if e.type == pygame.KEYDOWN and not (state["won"] or state["lost"]):
                letter = normalize_letter(e.unicode)
                if letter and letter not in state["used"]:
                    state["used"].add(letter)
                    if any(letters_equal(letter, wch, state["eyo_equiv"]) for wch in state["word"]):
                        for wch in set(state["word"]):
                            if letters_equal(letter, wch, state["eyo_equiv"]):
                                state["guessed"].add(wch)
                    else:
                        state["mistakes"] += 1

        # --- таймер и условия конца ---
        if not (state["won"] or state["lost"]):
            passed = (pygame.time.get_ticks() - state["started_ticks"]) // 1000
            state["time_left"] = max(0, ROUND_TIME - passed)
            if state["time_left"] == 0:
                state["lost"] = True
            elif all_letters_guessed(state["word"], state["guessed"], state["eyo_equiv"]):
                state["won"] = True
            elif state["mistakes"] >= MAX_MISTAKES:
                state["lost"] = True

        # --- РЕНДЕР ---
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, PANEL, left, border_radius=16)
        pygame.draw.rect(screen, BORDER, left, 2, border_radius=16)
        title_font = fit_font("Виселица", left.width - 32, MAX_XL, 20)
        draw_text(screen, "Виселица", title_font, INK, (left.left + 16, left.top + 12))

        gallows_base_y = left.top + int(left.height * 0.65)
        draw_gallows(screen, left.left + 40, gallows_base_y, state["mistakes"])

        stat_font = fit_font("Ошибок:", left.width - 32, MAX_L, 16)
        draw_text(screen, f"Ошибок: {state['mistakes']} / {MAX_MISTAKES}", stat_font, MUTED,
                  (left.left + 16, gallows_base_y + 20))

        time_color = GOOD if state["time_left"] > 20 else (BAD if state["time_left"] <= 10 else ACCENT)
        time_font = fit_font("Время:", left.width - 32, MAX_L, 16)
        draw_text(screen, f"Время: {state['time_left']:02d} сек", time_font, time_color,
                  (left.left + 16, gallows_base_y + 56))

        wrong = [ch for ch in state["used"]
                 if not any(letters_equal(ch, wch, state["eyo_equiv"]) for wch in set(state["word"]))]
        wrong_label_f = fit_font("Неверные:", left.width - 32, MAX_M, 14)
        wrong_text_f = fit_font("А Б В", left.width - 32, MAX_M, 14)
        draw_text(screen, "Неверные:", wrong_label_f, MUTED, (left.left + 16, gallows_base_y + 92))
        draw_text(screen, " ".join(sorted(wrong)) if wrong else "—", wrong_text_f, BAD,
                  (left.left + 16, gallows_base_y + 120))

        pygame.draw.rect(screen, PANEL, right, border_radius=16)
        pygame.draw.rect(screen, BORDER, right, 2, border_radius=16)

        cat_area_w = right.width - 32
        cat_full = f"Категория: {state['category']}"
        font_cat = fit_font(cat_full, cat_area_w, MAX_M, 14)
        cat_text = ellipsize(cat_full, font_cat, cat_area_w)
        draw_text(screen, cat_text, font_cat, MUTED, (right.left + 16, right.top + 16))

        # кнопка категории
        pygame.draw.rect(screen, BTN_BG, btn_cat, border_radius=10)
        pygame.draw.rect(screen, BORDER, btn_cat, 1, border_radius=10)
        draw_btn(screen, btn_cat, "Сменить категорию", INK, 18)

        # слово
        disp = []
        for ch in state["word"]:
            show = (ch in state["guessed"]) or (
                state["eyo_equiv"] and ch in {'Е', 'Ё'} and (('Е' in state["guessed"]) or ('Ё' in state["guessed"]))
            )
            disp.append(ch if show else "•")
        word_str = " ".join(disp)
        draw_text(screen, "Угадайте слово:", fit_font("Угадайте слово:", cat_area_w, MAX_M, 14),
                  MUTED, (right.left + 16, right.top + 70))
        draw_text(screen, word_str, fit_font(word_str, cat_area_w, MAX_XL, 18),
                  INK, (right.left + 16, right.top + 110))

        hint_line = "Кликайте по клавишам или печатайте с физической клавиатуры"
        hint_font = fit_font(hint_line, cat_area_w, MAX_S, 12)
        draw_text(screen, ellipsize(hint_line, hint_font, cat_area_w), hint_font,
                  MUTED, (right.left + 16, right.top + 210))

        # клавиатура
        for ch, rect in buttons:
            used = ch in state["used"]
            bg = BTN_USED if used else BTN_BG
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            pygame.draw.rect(screen, BORDER, rect, 1, border_radius=8)
            key_font = fit_font(ch, rect.width - 8, MAX_M, 14)
            draw_text(screen, ch, key_font, MUTED if used else INK, rect.center, center=True)

        # нижние кнопки
        draw_btn(screen, btn_hint, "Подсказка (-1 жизнь)", ACCENT, 22)
        draw_btn(screen, btn_again, "Сыграть ещё", ACCENT, 22)
        draw_btn(
            screen,
            btn_eyo,
            f"Е=Ё: {'ВКЛ' if state['eyo_equiv'] else 'ВЫКЛ'}",
            GOOD if state['eyo_equiv'] else MUTED,
            22,
        )

        if state["won"] or state["lost"]:
            overlay_w = right.width - 32
            overlay_h = 120
            overlay_y = int(right.top + right.height * 0.68)
            overlay = pygame.Surface((overlay_w, overlay_h), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 235))
            screen.blit(overlay, (right.left + 16, overlay_y))
            msg = "Победа! Слово:" if state["won"] else "Поражение. Слово:"
            draw_text(
                screen, msg, fit_font(msg, overlay_w - 20, MAX_L, 16),
                GOOD if state["won"] else BAD, (right.left + 30, overlay_y + 10)
            )
            draw_text(
                screen, state["word"], fit_font(state["word"], overlay_w - 20, MAX_XL, 18),
                INK, (right.left + 30, overlay_y + 48)
            )

        pygame.display.flip()

        # важный мини-патч для WEB: отдаём квант управления браузеру
        if WEB:
            await asyncio.sleep(0)

    # корректное завершение
    pygame.quit()
    if not WEB:
        sys.exit()

# --------- ТОЧКА ВХОДА ----------
if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(run_game())
    except Exception:
        tb = traceback.format_exc()
        print(tb)
        show_traceback_screen(tb)
        try:
            pygame.quit()
        except Exception:
            pass
        if not WEB:
            sys.exit(1)
