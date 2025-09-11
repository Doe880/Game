# -*- coding: utf-8 -*-
"""
Виселица (pygame) — мобильный дружелюбный UI (pygbag-ready).
- async-цикл (await asyncio.sleep(0) в WEB)
- респонсивный лейаут: портрет/альбом
- увеличенные тач-зоны и адаптивные размеры
"""

import sys
import random
import traceback
import pygame

# --------- НАСТРОЙКИ ----------
BASE_W, BASE_H = 960, 540      # базовая «макетка» для скейлинга
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

# базовые максимальные размеры шрифтов — умножаются на ui_scale
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
        "КОМПЬЮТЕР","АЛГОРИТМ","ИНТЕРФЕЙС","ПРОГРАММИСТ","СЕРВЕР","БИБЛИОТЕКА",
        "ПРИЛОЖЕНИЕ","ПАРАМЕТР","ФУНКЦИЯ","ДАННЫЕ","ЛОГИКА","ПИТОН","НЕЙРОСЕТЬ"
    ],
    "КОСМОС": ["РАКЕТА","КОСМОС","ЗВЕЗДА","ГРАВИТАЦИЯ","ПУЛЬСАР","КВАНТ","СИНТЕЗ","ВИХРЬ"],
    "ПРИРОДА": ["СНЕЖИНКА","ОКЕАН","МОЛЕКУЛА","ЖИРАФ","КАРТИНА","РЕАЛЬНОСТЬ","ТЕТРАДЬ","ЭНЕРГИЯ"],
    "С Ё-БУКВАМИ": ["ЁЛКА","ЁМКОСТЬ","ШЁПОТ"]
}
CATEGORIES = list(WORDS_BY_CATEGORY.keys())

# --------- ХЕЛПЕРЫ ----------
def ui_scale_for(w, h):
    s = min(w / BASE_W, h / BASE_H)
    return max(0.6, min(1.5, s))

def choose_word(cat): return random.choice(WORDS_BY_CATEGORY[cat])

def load_font(size):
    try:
        return pygame.font.Font(FONT_PATH, size)
    except Exception:
        try:
            return pygame.font.Font(None, size)
        except Exception:
            return pygame.font.SysFont(None, size)

def fit_font(text, max_width, max_size, min_size=14):
    size = max_size
    while size > min_size:
        f = load_font(size)
        if f.size(text)[0] <= max_width:
            return f
        size -= 1
    return load_font(min_size)

def ellipsize(text, font, max_width):
    if font.size(text)[0] <= max_width:
        return text
    ell = "…"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi) // 2
        if font.size(text[:mid] + ell)[0] <= max_width: lo = mid + 1
        else: hi = mid
    return text[:max(1, lo-1)] + ell

def draw_text(surface, text, font, color, pos, center=False):
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center: rect.center = pos
    else: rect.topleft = pos
    surface.blit(img, rect)
    return rect

def build_keyboard(area_rect, ui_s=1.0):
    # крупные клавиши и интервалы для тача
    padding = int(10 * ui_s)
    rows = len(KEYBOARD_ROWS)
    btn_h = max(int(40 * ui_s), (area_rect.height - (rows + 1) * (padding + 2)) // rows)
    buttons = []
    y = area_rect.top + padding
    for row in KEYBOARD_ROWS:
        cols = len(row)
        btn_w = max(int(34 * ui_s), (area_rect.width - (cols + 1) * padding) // cols)
        x = area_rect.left + padding
        for ch in row:
            rect = pygame.Rect(x, y, btn_w, btn_h)
            hit_rect = rect.inflate(int(6 * ui_s), int(6 * ui_s))  # расширенная тач-зона
            buttons.append((ch, rect, hit_rect))
            x += btn_w + padding
        y += btn_h + padding
    return buttons

def normalize_letter(ch):
    if not ch: return None
    up = ch.upper()
    return up if ('А' <= up <= 'Я' or up == 'Ё') else None

def letters_equal(a, b, eyo):
    return a == b or (eyo and ((a, b) in {('Е','Ё'),('Ё','Е')}))

def all_letters_guessed(word, guessed, eyo):
    for ch in set(word):
        if ch in guessed: continue
        if eyo and ch in {'Е','Ё'} and (('Е' in guessed) or ('Ё' in guessed)): continue
        return False
    return True

def reveal_random_letter(state):
    hidden = []
    for ch in set(state["word"]):
        show = (ch in state["guessed"]) or (state["eyo_equiv"] and ch in {'Е','Ё'} and (('Е' in state["guessed"]) or ('Ё' in state["guessed"])))
        if not show: hidden.append(ch)
    if not hidden: return False
    state["guessed"].add(random.choice(hidden))
    state["mistakes"] = min(MAX_MISTAKES, state["mistakes"] + 1)
    return True

def draw_gallows(surface, base_x, base_y, mistakes, ui_s=1.0):
    lw = max(2, int(6 * ui_s))
    lw_thin = max(1, int(4 * ui_s))
    pygame.draw.line(surface, MUTED, (base_x, base_y), (base_x + int(220*ui_s), base_y), lw)
    pygame.draw.line(surface, MUTED, (base_x + int(50*ui_s), base_y), (base_x + int(50*ui_s), base_y - int(280*ui_s)), lw)
    pygame.draw.line(surface, MUTED, (base_x + int(50*ui_s), base_y - int(280*ui_s)), (base_x + int(170*ui_s), base_y - int(280*ui_s)), lw)
    pygame.draw.line(surface, MUTED, (base_x + int(170*ui_s), base_y - int(280*ui_s)), (base_x + int(170*ui_s), base_y - int(230*ui_s)), lw_thin)
    cx, cy = base_x + int(170*ui_s), base_y - int(210*ui_s)
    if mistakes > 0: pygame.draw.circle(surface, BAD, (cx, cy), max(4, int(20*ui_s)), max(1, int(3*ui_s)))
    if mistakes > 1: pygame.draw.line(surface, BAD, (cx, cy + int(20*ui_s)), (cx, cy + int(95*ui_s)), max(1, int(3*ui_s)))
    if mistakes > 2: pygame.draw.line(surface, BAD, (cx, cy + int(45*ui_s)), (cx - int(32*ui_s), cy + int(75*ui_s)), max(1, int(3*ui_s)))
    if mistakes > 3: pygame.draw.line(surface, BAD, (cx, cy + int(45*ui_s)), (cx + int(32*ui_s), cy + int(75*ui_s)), max(1, int(3*ui_s)))
    if mistakes > 4: pygame.draw.line(surface, BAD, (cx, cy + int(95*ui_s)), (cx - int(25*ui_s), cy + int(130*ui_s)), max(1, int(3*ui_s)))
    if mistakes > 5: pygame.draw.line(surface, BAD, (cx, cy + int(95*ui_s)), (cx + int(25*ui_s), cy + int(130*ui_s)), max(1, int(3*ui_s)))

def compute_layout(w, h, ui_s=1.0):
    """Респонсивная раскладка:
       - альбом: левый (виселица) + правый (игра)
       - портрет: верх (виселица) + низ (игра)
       Нижние кнопки занимают всю ширину и делят её адаптивно.
    """
    margin = int(16 * ui_s)
    border = int(16 * ui_s)

    portrait = h >= w

    if not portrait:
        # альбом
        left_w = max(int(360 * ui_s), int(w * 0.42))
        left = pygame.Rect(margin, margin, left_w - margin, h - 2*margin)
        right = pygame.Rect(left.right + margin, margin, w - (left.width + 3*margin), h - 2*margin)
        kb_h_frac = 0.36 if h >= 560 else 0.42
        kb_area = pygame.Rect(right.left + border, right.top + int(h * 0.36),
                              right.width - 2*border, int(h * kb_h_frac))
    else:
        # портрет
        top_h = int(h * 0.46)
        left = pygame.Rect(margin, margin, w - 2*margin, top_h - margin)
        right = pygame.Rect(margin, left.bottom + margin, w - 2*margin, h - (left.height + 3*margin))
        kb_h = max(int(right.height * 0.48), int(220 * ui_s))
        kb_area = pygame.Rect(right.left + border,
                              right.bottom - kb_h - border,
                              right.width - 2*border,
                              kb_h)

    # --- нижние кнопки: адаптивно по ширине ---
    btn_h = max(int(44 * ui_s), 40)
    yb = kb_area.top - (btn_h + int(10 * ui_s))
    gap = int(10 * ui_s)
    side_pad = int(16 * ui_s)
    available_w = right.width - 2*side_pad - 2*gap

    # две большие + одна поменьше, но всё влезает
    btn_w_hint  = max(int(120 * ui_s), int(available_w * 0.34))
    btn_w_again = max(int(120 * ui_s), int(available_w * 0.34))
    btn_w_eyo   = max(int(100 * ui_s), available_w - btn_w_hint - btn_w_again)

    x = right.left + side_pad
    btn_hint  = pygame.Rect(x, yb, btn_w_hint, btn_h)
    x = btn_hint.right + gap
    btn_again = pygame.Rect(x, yb, btn_w_again, btn_h)
    x = btn_again.right + gap
    btn_eyo   = pygame.Rect(x, yb, btn_w_eyo, btn_h)

    # кнопка "Сменить категорию" — выше слова
    btn_cat = pygame.Rect(right.left + side_pad, right.top + int(170 * ui_s),
                          max(int(220 * ui_s), int(right.width * 0.4)),
                          max(int(40 * ui_s), 36))

    return left, right, kb_area, btn_hint, btn_again, btn_eyo, btn_cat

def draw_btn(surface, rect, label, bg, max_size=22, ui_s=1.0):
    f = fit_font(label, rect.width - int(12 * ui_s), int(max_size * ui_s), max(12, int(12 * ui_s)))
    pygame.draw.rect(surface, bg, rect, border_radius=max(10, int(10 * ui_s)))
    draw_text(surface, label, f, (255,255,255), rect.center, center=True)

def new_state(cat, keep_eyo=None):
    return {
        "category": cat,
        "word": choose_word(cat),
        "guessed": set(), "used": set(),
        "mistakes": 0, "won": False, "lost": False,
        "eyo_equiv": True if keep_eyo is None else keep_eyo,
        "time_left": ROUND_TIME, "started_ticks": pygame.time.get_ticks()
    }

# ---------- ВСПОМОГАТЕЛЬНОЕ ----------
def show_traceback_screen(tb_text):
    try:
        pygame.display.init(); pygame.font.init()
        screen = pygame.display.set_mode((BASE_W, BASE_H), 0)
        screen.fill((10,10,10))
        f = load_font(18)
        y = 10
        for line in ("Ошибка исполнения:",) + tuple(tb_text.splitlines()):
            img = f.render(line[:120], True, (255, 80, 80))
            screen.blit(img, (10, y)); y += 22
        pygame.display.flip()
        import time
        t0 = time.time()
        while time.time() - t0 < 10:
            pygame.event.pump()
    except Exception as e2:
        print("FATAL (traceback screen):", e2)

# --------- ИГРА (ASYNC) ----------
async def run_game():
    import asyncio

    pygame.display.init()
    pygame.font.init()

    flags = 0 if WEB else pygame.RESIZABLE
    screen = pygame.display.set_mode((BASE_W, BASE_H), flags)
    pygame.display.set_caption("Виселица (pygame): мобильный UI, категории, таймер, подсказки, Е=Ё")
    clock = pygame.time.Clock()

    w, h = screen.get_size()
    ui_s = ui_scale_for(w, h)
    left, right, kb_area, btn_hint, btn_again, btn_eyo, btn_cat = compute_layout(w, h, ui_s)
    buttons = build_keyboard(kb_area, ui_s)

    cat_idx = 0
    state = new_state(CATEGORIES[cat_idx])

    def refresh_layout_if_needed():
        nonlocal w, h, ui_s, left, right, kb_area, btn_hint, btn_again, btn_eyo, btn_cat, buttons
        cur_w, cur_h = pygame.display.get_surface().get_size()
        if (cur_w, cur_h) != (w, h):
            w, h = cur_w, cur_h
            ui_s = ui_scale_for(w, h)
            left, right, kb_area, btn_hint, btn_again, btn_eyo, btn_cat = compute_layout(w, h, ui_s)
            buttons = build_keyboard(kb_area, ui_s)

    running = True
    while running:
        dt = clock.tick(FPS)
        refresh_layout_if_needed()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if not WEB and e.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((max(640, e.w), max(480, e.h)), pygame.RESIZABLE)
                refresh_layout_if_needed()

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = e.pos

                if btn_cat.collidepoint(mx, my) and not (state["won"] or state["lost"]):
                    cat_idx = (cat_idx + 1) % len(CATEGORIES)
                    state = new_state(CATEGORIES[cat_idx], keep_eyo=state["eyo_equiv"]); continue

                if btn_hint.collidepoint(mx, my) and not (state["won"] or state["lost"]):
                    if state["mistakes"] < MAX_MISTAKES: reveal_random_letter(state)

                if btn_again.collidepoint(mx, my):
                    state = new_state(state["category"], keep_eyo=state["eyo_equiv"]); continue

                if btn_eyo.collidepoint(mx, my):
                    state["eyo_equiv"] = not state["eyo_equiv"]; continue

                if not (state["won"] or state["lost"]):
                    for ch, rect, hit_rect in buttons:
                        if hit_rect.collidepoint(mx, my):
                            if ch not in state["used"]:
                                state["used"].add(ch)
                                if any(letters_equal(ch, wch, state["eyo_equiv"]) for wch in state["word"]):
                                    for wch in set(state["word"]):
                                        if letters_equal(ch, wch, state["eyo_equiv"]): state["guessed"].add(wch)
                                else: state["mistakes"] += 1
                            break

            if e.type == pygame.KEYDOWN and not (state["won"] or state["lost"]):
                letter = normalize_letter(e.unicode)
                if letter and letter not in state["used"]:
                    state["used"].add(letter)
                    if any(letters_equal(letter, wch, state["eyo_equiv"]) for wch in state["word"]):
                        for wch in set(state["word"]):
                            if letters_equal(letter, wch, state["eyo_equiv"]): state["guessed"].add(wch)
                    else: state["mistakes"] += 1

        # таймер + условия конца
        if not (state["won"] or state["lost"]):
            passed = (pygame.time.get_ticks() - state["started_ticks"]) // 1000
            state["time_left"] = max(0, ROUND_TIME - passed)
            if state["time_left"] == 0: state["lost"] = True
            elif all_letters_guessed(state["word"], state["guessed"], state["eyo_equiv"]): state["won"] = True
            elif state["mistakes"] >= MAX_MISTAKES: state["lost"] = True

        # --- РЕНДЕР ---
        screen.fill(BG_COLOR)

        br = max(12, int(16 * ui_s))
        pygame.draw.rect(screen, PANEL, left, border_radius=br)
        pygame.draw.rect(screen, BORDER, left, max(1, int(2 * ui_s)), border_radius=br)
        pygame.draw.rect(screen, PANEL, right, border_radius=br)
        pygame.draw.rect(screen, BORDER, right, max(1, int(2 * ui_s)), border_radius=br)

        title_font = fit_font("Виселица", left.width - int(32 * ui_s), int(MAX_XL * ui_s), max(16, int(16 * ui_s)))
        draw_text(screen, "Виселица", title_font, INK, (left.left + int(16 * ui_s), left.top + int(12 * ui_s)))

        gallows_base_y = left.top + int(left.height * 0.66)
        draw_gallows(screen, left.left + int(40 * ui_s), gallows_base_y, state["mistakes"], ui_s)

        stat_font = fit_font("Ошибок:", left.width - int(32 * ui_s), int(MAX_L * ui_s), max(14, int(14 * ui_s)))
        draw_text(screen, f"Ошибок: {state['mistakes']} / {MAX_MISTAKES}", stat_font, MUTED,
                  (left.left + int(16 * ui_s), gallows_base_y + int(20 * ui_s)))

        time_color = GOOD if state["time_left"] > 20 else (BAD if state["time_left"] <= 10 else ACCENT)
        time_font = fit_font("Время:", left.width - int(32 * ui_s), int(MAX_L * ui_s), max(14, int(14 * ui_s)))
        draw_text(screen, f"Время: {state['time_left']:02d} сек", time_font, time_color,
                  (left.left + int(16 * ui_s), gallows_base_y + int(56 * ui_s)))

        wrong = [ch for ch in state["used"] if not any(letters_equal(ch, wch, state["eyo_equiv"]) for wch in set(state["word"]))]
        wrong_label_f = fit_font("Неверные:", left.width - int(32 * ui_s), int(MAX_M * ui_s), max(12, int(12 * ui_s)))
        wrong_text_f  = fit_font("А Б В", left.width - int(32 * ui_s), int(MAX_M * ui_s), max(12, int(12 * ui_s)))
        draw_text(screen, "Неверные:", wrong_label_f, MUTED, (left.left + int(16 * ui_s), gallows_base_y + int(92 * ui_s)))
        draw_text(screen, " ".join(sorted(wrong)) if wrong else "—", wrong_text_f, BAD,
                  (left.left + int(16 * ui_s), gallows_base_y + int(120 * ui_s)))

        # правая панель
        cat_area_w = right.width - int(32 * ui_s)
        cat_full = f"Категория: {state['category']}"
        font_cat = fit_font(cat_full, cat_area_w, int(MAX_M * ui_s), max(12, int(12 * ui_s)))
        cat_text = ellipsize(cat_full, font_cat, cat_area_w)
        draw_text(screen, cat_text, font_cat, MUTED, (right.left + int(16 * ui_s), right.top + int(16 * ui_s)))

        pygame.draw.rect(screen, BTN_BG, btn_cat, border_radius=max(8, int(10 * ui_s)))
        pygame.draw.rect(screen, BORDER, btn_cat, max(1, int(1 * ui_s)), border_radius=max(8, int(10 * ui_s)))
        draw_btn(screen, btn_cat, "Сменить категорию", INK, 18, ui_s)

        disp = []
        for ch in state["word"]:
            show = (ch in state["guessed"]) or (state["eyo_equiv"] and ch in {'Е','Ё'} and (('Е' in state["guessed"]) or ('Ё' in state["guessed"])))
            disp.append(ch if show else "•")
        word_str = " ".join(disp)
        draw_text(screen, "Угадайте слово:", fit_font("Угадайте слово:", cat_area_w, int(MAX_M * ui_s), max(12, int(12 * ui_s))),
                  MUTED, (right.left + int(16 * ui_s), right.top + int(70 * ui_s)))
        draw_text(screen, word_str, fit_font(word_str, cat_area_w, int(MAX_XL * ui_s), max(16, int(16 * ui_s))),
                  INK, (right.left + int(16 * ui_s), right.top + int(110 * ui_s)))

        hint_line = "Кликайте по клавишам или печатайте с физической клавиатуры"
        hint_font = fit_font(hint_line, cat_area_w, int(MAX_S * ui_s), max(10, int(12 * ui_s)))
        draw_text(screen, ellipsize(hint_line, hint_font, cat_area_w), hint_font, MUTED,
                  (right.left + int(16 * ui_s), right.top + int(210 * ui_s)))

        for ch, rect, _hit in buttons:
            used = ch in state["used"]
            bg = BTN_USED if used else BTN_BG
            rr = max(8, int(8 * ui_s))
            pygame.draw.rect(screen, bg, rect, border_radius=rr)
            pygame.draw.rect(screen, BORDER, rect, max(1, int(1 * ui_s)), border_radius=rr)
            key_font = fit_font(ch, rect.width - int(8 * ui_s), int(MAX_M * ui_s), max(14, int(14 * ui_s)))
            draw_text(screen, ch, key_font, MUTED if used else INK, rect.center, center=True)

        draw_btn(screen, btn_hint,  "Подсказка (-1 жизнь)", ACCENT, 22, ui_s)
        draw_btn(screen, btn_again, "Сыграть ещё",          ACCENT, 22, ui_s)
        draw_btn(screen, btn_eyo,   f"Е=Ё: {'ВКЛ' if state['eyo_equiv'] else 'ВЫКЛ'}",
                 GOOD if state['eyo_equiv'] else MUTED, 22, ui_s)

        if state["won"] or state["lost"]:
            overlay_w = right.width - int(32 * ui_s)
            overlay_h = max(int(120 * ui_s), 100)
            overlay_y = int(right.top + right.height * 0.68)
            overlay = pygame.Surface((overlay_w, overlay_h), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 235))
            screen.blit(overlay, (right.left + int(16 * ui_s), overlay_y))
            msg = "Победа! Слово:" if state["won"] else "Поражение. Слово:"
            draw_text(screen, msg, fit_font(msg, overlay_w - int(20 * ui_s), int(MAX_L * ui_s), max(14, int(14 * ui_s))),
                      GOOD if state["won"] else BAD, (right.left + int(30 * ui_s), overlay_y + int(10 * ui_s)))
            draw_text(screen, state["word"], fit_font(state["word"], overlay_w - int(20 * ui_s), int(MAX_XL * ui_s), max(16, int(16 * ui_s))),
                      INK, (right.left + int(30 * ui_s), overlay_y + int(48 * ui_s)))

        pygame.display.flip()
        if WEB:
            await asyncio.sleep(0)

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
        try: pygame.quit()
        except: pass
        if not WEB: sys.exit(1)
