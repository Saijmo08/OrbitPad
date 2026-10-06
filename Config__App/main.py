import customtkinter as ctk
from PIL import ImageTk, Image

board_status = False
port = "COM4"

BG_MAIN      = "#0f1117"   # Background
BG_SIDEBAR   = "#161b22"   
BG_CARD      = "#1c2230"   # Panels
BG_KEY       = "#1e2a3a"   # Buttons
BG_KEY_HOV   = "#243448"   # Button hover
ACCENT       = "#4f8ef7"   
ACCENT_DIM   = "#2a4a7f"  
TEXT_PRIMARY = "#e8eaf0"    
TEXT_SEC     = "#7a8599"   
TEXT_ACCENT  = "#4f8ef7"   
BORDER       = "#2a3347"   
SUCCESS      = "#3dba6f"  
WARNING      = "#e8a23a"   


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


root = ctk.CTk()
root.title("OrbitPad Configurator")
root.geometry("1100x700")
root.minsize(900, 600)
root.iconbitmap(r"C:\Users\leolu\OneDrive\Dokumente\Visual Studio Code\Stardance\app.ico")

sidebar = ctk.CTkFrame(root, width=220, fg_color=BG_SIDEBAR, corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
logo_frame.pack(fill="x", padx=20, pady=(24, 8))

logo_label = ctk.CTkLabel(
    logo_frame,
    text="🚀 OrbitPad",
    font=ctk.CTkFont(family="Helvetica", size=20, weight="bold"),
    text_color=TEXT_PRIMARY
)
logo_label.pack(anchor="nw")

version_label = ctk.CTkLabel(
    logo_frame,
    text="Configurator v1.0",
    font=ctk.CTkFont(family="Helvetica", size=11),
    text_color=TEXT_SEC
)
version_label.pack(anchor="w")


ctk.CTkLabel(
    sidebar,
    text="APP-PROFILES",
    font=ctk.CTkFont(size=10, weight="bold"),
    text_color=TEXT_SEC
).pack(anchor="w", padx=20, pady=(0, 6))


app_profiles = [
    ("Fusion 360",  True),
    ("KiCad",       False),
    ("Photoshop",   False),
    ("VS Code",     False),
    ("Default",    False),
]

profile_buttons = []

def change_profile(active_index):
    for index, button in enumerate(profile_buttons):
        is_active = index == active_index
        button.configure(
            fg_color=ACCENT_DIM if is_active else "transparent",
            text_color=TEXT_PRIMARY if is_active else TEXT_SEC,
        )
    active_profile_label.configure(
        text=f"Aktives Profil: {app_profiles[active_index][0]}"
    )

for label, active in app_profiles:
    btn_sidebar = ctk.CTkButton(
        sidebar,
        text=label,
        anchor="w",
        height=36,
        corner_radius=6,
        font=ctk.CTkFont(size=12),
        fg_color=ACCENT_DIM if active else "transparent",
        hover_color=BG_KEY_HOV,
        text_color=TEXT_PRIMARY if active else TEXT_SEC,
        border_width=0,
        command=lambda index=len(profile_buttons): change_profile(index),
    )
    btn_sidebar.pack(anchor="w", padx=10, pady=1, fill="x")
    profile_buttons.append(btn_sidebar)

new_profile_btn = ctk.CTkButton(
    sidebar,
    text="+ New profile",
    anchor="w",
    height=35,
    corner_radius=6,
    font=ctk.CTkFont(size=12),
    fg_color="transparent",
    hover_color=BG_KEY_HOV,
    text_color=ACCENT,
    border_width=0,
)
new_profile_btn.pack(anchor="w", padx=10, pady=1, fill="x")


status_frame = ctk.CTkFrame(sidebar, fg_color=BG_CARD, corner_radius=10)
status_frame.pack(side="bottom", fill="x", padx=10, pady=15)

status_dot = ctk.CTkLabel(
    status_frame,
    text="●",
    font=ctk.CTkFont(size=12),
    text_color=SUCCESS if board_status else WARNING
)
status_dot.pack(side="left", padx=(12, 4), pady=10)

status_text = ctk.CTkLabel(
    status_frame,
    text="OrbitPad connected" if board_status else "OrbitPad disconnected",
    font=ctk.CTkFont(size=11),
    text_color=TEXT_PRIMARY
)
status_text.pack(side="left", pady=10)

status_port = ctk.CTkLabel(
    status_frame,
    text=port if board_status else "",
    font=ctk.CTkFont(size=10),
    text_color=TEXT_SEC
)
status_port.pack(side="right", padx=12, pady=10)



main_area = ctk.CTkFrame(root, fg_color=BG_MAIN, corner_radius=0)
main_area.pack(side="left", fill="both", expand=True)


topbar = ctk.CTkFrame(main_area, fg_color=BG_SIDEBAR, corner_radius=0, height=56)
topbar.pack(side="top", fill="x")
topbar.pack_propagate(False)

page_title = ctk.CTkLabel(
    topbar,
    text="Key assignment",
    font=ctk.CTkFont(size=16, weight="bold"),
    text_color=TEXT_PRIMARY
)
page_title.pack(side="left", padx=(0, 20), pady=16)


layer_frame = ctk.CTkFrame(topbar, fg_color="transparent")
layer_frame.pack(side="left", padx=10)

ctk.CTkLabel(
    layer_frame,
    text="Layer:",
    font=ctk.CTkFont(size=12),
    text_color=TEXT_SEC
).pack(side="left", padx=(0, 8))


layer_names = ["Default", "Advanced"]
n = 0
layer_buttons = []


def normalize_active_layer_index():
    global n
    if not layer_names:
        n = 0
    elif n < 0:
        n = 0
    elif n >= len(layer_names):
        n = len(layer_names) - 1


def update_layer_button_colors():
    for index, button in enumerate(layer_buttons):
        if index >= len(layer_names):
            button.configure(fg_color=BG_CARD)
            continue
        button.configure(fg_color=ACCENT if index == n else BG_CARD)


def build_layer_buttons():
    global n
    for button in layer_buttons:
        button.destroy()
    layer_buttons.clear()

    normalize_active_layer_index()

    display_buttons = []
    for index, name in enumerate(layer_names):
        display_buttons.append((index, name, f"{index + 1} — {name}"))

    if len(layer_names) < 4:
        display_buttons.append((None, "+ Layer", "+ Layer"))

    for i_layer, layer_name, display_name in display_buttons:
        layer_btn = ctk.CTkButton(
            layer_frame,
            text=display_name,
            width=110,
            height=30,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color=ACCENT if i_layer is not None and i_layer == n else BG_CARD,
            hover_color=ACCENT_DIM,
            text_color=TEXT_PRIMARY,
            border_width=0,
            command=lambda layer=i_layer, name=layer_name: change_active(layer, name)
        )
        layer_btn.pack(side="left", padx=3)
        layer_buttons.append(layer_btn)

    update_layer_button_colors()


def add_layer_button():
    add_layer = ctk.CTkToplevel(root)
    add_layer.title("Layer")
    add_layer.geometry("300x150")
    add_layer._set_appearance_mode("dark")
    add_layer.transient(root)
    add_layer.grab_set()

    layer_add_frame = ctk.CTkFrame(add_layer, fg_color="transparent")
    layer_add_frame.pack(side="left", padx=10)

    box_layer = ctk.CTkTextbox(
        layer_add_frame,
        width=260,
        height=40,
        border_width=2,
        corner_radius=6,
        fg_color=BG_CARD,
        border_color=BORDER)
    box_layer.pack(pady=20, padx=10, fill="both")
    box_layer.focus_set()

    def save_layer_name():
        global n
        layer_name = box_layer.get("1.0", "end").strip()
        if not layer_name:
            return

        layer_name = layer_name.title()
        if layer_name == "+ Layer":
            return
        if layer_name in layer_names:
            n = layer_names.index(layer_name)
            add_layer.destroy()
            build_layer_buttons()
            return

        layer_names.append(layer_name)
        n = len(layer_names) - 1
        add_layer.destroy()
        build_layer_buttons()

    ctk.CTkButton(layer_add_frame, text="Add", command=save_layer_name).pack(pady=(0, 10))


def change_active(layer, name):
    global n
    if name == "+ Layer":
        add_layer_button()
        return

    if layer is None:
        layer = n
    if layer < 0:
        layer = 0
    elif layer >= len(layer_names):
        layer = len(layer_names) - 1

    n = layer
    update_layer_button_colors()


build_layer_buttons()




save_btn = ctk.CTkButton(
    topbar,
    text="Save on Pad",
    width=160,
    height=34,
    corner_radius=8,
    font=ctk.CTkFont(size=12, weight="bold"),
    fg_color=ACCENT,
    hover_color=ACCENT_DIM,
    text_color=TEXT_PRIMARY,
)
save_btn.pack(side="right", padx=20)



mid = ctk.CTkScrollableFrame(main_area, fg_color=BG_MAIN, scrollbar_button_color=BORDER)
mid.pack(fill="both", expand=True, padx=0, pady=0)

inner = ctk.CTkFrame(mid, fg_color="transparent")
inner.pack(fill="both", expand=True, padx=20, pady=20)
inner.columnconfigure(0, weight=3)
inner.columnconfigure(1, weight=2)

left_col = ctk.CTkFrame(inner, fg_color="transparent")
left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

device_card = ctk.CTkFrame(left_col, fg_color=BG_CARD, corner_radius=14)
device_card.pack(fill="x", pady=(0, 16))


active_profile = next((label for label, active in app_profiles if active), "Default")
active_profile_label = ctk.CTkLabel(
    device_card,
    text=f"Active Profile: {active_profile}",
    font=ctk.CTkFont(size=13, weight="bold"),
    text_color=TEXT_PRIMARY
)
active_profile_label.pack(anchor="w", padx=20, pady=(16, 12))

device_inner = ctk.CTkFrame(device_card, fg_color="transparent")
device_inner.pack(side="left", padx=20, pady=(0, 20))


display_frame = ctk.CTkFrame(
    device_inner,
    width=128,
    height=128,
    fg_color="#090e14",
    corner_radius=8,
    border_width=2,
    border_color="#2a3a4a"
)
display_frame.pack(side="left", padx=(0, 20))
display_frame.pack_propagate(False)


keys_data = [
    ("^Z", "Rückgängig"), ("^Y", "Wiederholen"), ("^C", "Kopieren"),  ("^V", "Einfügen"),
    ("E",   "Extrude"),    ("S",   "Sketch"),       ("P",   "Press/Pull"),("F",  "Fillet"),
    ("F6",  "Ansicht"),    ("L",   "Line"),          ("C",   "Circle"),    ("▲",  "Layer +"),
]

display_grid = ctk.CTkFrame(display_frame, fg_color="transparent")
display_grid.pack(side="left", padx=(20, 0))

for i_key_display, (symbol, label_text) in enumerate(keys_data):
    row = i_key_display % 4
    col = i_key_display // 4
    
    key_display_frame = ctk.CTkFrame(
        display_grid,
        width=25,
        height=25,
        fg_color="#042712",
        border_color="#3dba6f",
        corner_radius=8,
        border_width=1
    )
    key_display_frame.grid(row=row, column=col, padx=2, pady=2)
    key_display_frame.pack_propagate(False)

    ctk.CTkLabel(
        key_display_frame,
        text=symbol,
        font=ctk.CTkFont(size=10),
        text_color="#3dba6f"
    ).place(relx=0.5, rely=0.5, anchor="center")


key_grid_frame = ctk.CTkFrame(device_inner, fg_color="transparent")
key_grid_frame.pack(side="left")

selected_key_idx = 11

for i_key, (symbol, label_text) in enumerate(keys_data):
    row = i_key % 4
    col = i_key // 4

    is_selected = (i_key == selected_key_idx)

    key_frame = ctk.CTkFrame(
        key_grid_frame,
        width=72,
        height=64,
        fg_color=ACCENT_DIM if is_selected else BG_KEY,
        corner_radius=8,
        border_width=2 if is_selected else 1,
        border_color=ACCENT if is_selected else BORDER,
    )
    key_frame.grid(row=row, column=col, padx=4, pady=4)
    key_frame.pack_propagate(False)

    ctk.CTkLabel(
        key_frame,
        text=str(i_key + 1),
        font=ctk.CTkFont(size=9),
        text_color=TEXT_SEC
    ).place(relx=0.0, x=5, y=-5, anchor="nw")

    ctk.CTkLabel(
        key_frame,
        text=symbol,
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=TEXT_PRIMARY if not is_selected else "#ffffff"
    ).place(relx=0.5, rely=0.38, anchor="center")

    ctk.CTkLabel(
        key_frame,
        text=label_text,
        font=ctk.CTkFont(size=8),
        text_color=TEXT_SEC if not is_selected else "#aabbff"
    ).place(relx=0.5, rely=0.78, anchor="center")


encoder_row = ctk.CTkFrame(device_card, fg_color="transparent")
encoder_row.pack(pady=(0, 20))

for i_enc, (enc_name, enc_func) in enumerate([("ENC 1", "Volume"), ("ENC 2", "Zoom")]):
    enc_frame = ctk.CTkFrame(
        encoder_row,
        width=72,
        height=72,
        fg_color=BG_KEY,
        corner_radius=36,
        border_width=1,
        border_color=BORDER,
    )
    enc_frame.grid(column=0, row=i_enc, pady=8)
    enc_frame.pack_propagate(False)

    ctk.CTkLabel(
        enc_frame,
        text="↻",
        font=ctk.CTkFont(size=22),
        text_color=ACCENT
    ).place(relx=0.5, rely=0.38, anchor="center")

    ctk.CTkLabel(
        enc_frame,
        text=enc_func,
        font=ctk.CTkFont(size=8),
        text_color=TEXT_SEC
    ).place(relx=0.5, rely=0.75, anchor="center")



right_col = ctk.CTkFrame(inner, fg_color="transparent")
right_col.grid(row=0, column=1, sticky="nsew")

edit_card = ctk.CTkFrame(right_col, fg_color=BG_CARD, corner_radius=14)
edit_card.pack(fill="x", pady=(0, 12))

ctk.CTkLabel(
    edit_card,
    text="Edit key 3",
    font=ctk.CTkFont(size=13, weight="bold"),
    text_color=TEXT_PRIMARY
).pack(anchor="w", padx=20, pady=(16, 4))

ctk.CTkLabel(
    edit_card,
    text="Fusion 360 — Layer 1",
    font=ctk.CTkFont(size=11),
    text_color=TEXT_SEC
).pack(anchor="w", padx=20, pady=(0, 14))


fields = [
    ("Icon",   "^C",        "z.B. ^, ★, ✂"),
    ("Title",    "Copy",   "z.B Copy"),
    ("Shortcut", "Ctrl+C",   "z.B. Ctrl+Z, F6, Win+D")
]

for field_label, field_value, field_placeholder in fields:
    f_row = ctk.CTkFrame(edit_card, fg_color="transparent")
    f_row.pack(fill="x", padx=20, pady=4)

    ctk.CTkLabel(
        f_row,
        text=field_label,
        font=ctk.CTkFont(size=11),
        text_color=TEXT_SEC,
        anchor="w"
    ).pack(anchor="w", pady=(0, 2))

    entry = ctk.CTkEntry(
        f_row,
        height=32,
        font=ctk.CTkFont(size=12),
        fg_color=BG_KEY,
        border_color=BORDER,
        text_color=TEXT_PRIMARY,
        placeholder_text=field_placeholder,
    )
    if field_value:
        entry.insert(0, field_value)
    entry.pack(fill="x")

type_key_frame = ctk.CTkFrame(edit_card, fg_color="transparent")
type_key_frame.pack(fill="x", padx=20, pady=(8, 4))

ctk.CTkLabel(
    type_key_frame,
    text="Key",
    font=ctk.CTkFont(size=11),
    text_color=TEXT_SEC,
    anchor="w"
).pack(anchor="w", pady=(0, 4))

type_menu = ctk.CTkOptionMenu(
    type_key_frame,
    values=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
    height=32,
    font=ctk.CTkFont(size=12),
    fg_color=BG_KEY,
    button_color=ACCENT_DIM,
    button_hover_color=ACCENT,
    text_color=TEXT_PRIMARY,
    dropdown_fg_color=BG_CARD,
    dropdown_text_color=TEXT_PRIMARY,
    dropdown_hover_color=BG_KEY_HOV,
)
type_menu.pack(fill="x")
type_menu.set("1")


apply_btn = ctk.CTkButton(
    edit_card,
    text="Apply",
    height=36,
    corner_radius=8,
    font=ctk.CTkFont(size=13, weight="bold"),
    fg_color=ACCENT,
    hover_color=ACCENT_DIM,
    text_color=TEXT_PRIMARY,
)
apply_btn.pack(fill="x", padx=20, pady=(12, 16))





icon_card = ctk.CTkFrame(right_col, fg_color=BG_CARD, corner_radius=14)
icon_card.pack(fill="x", pady=(0, 12))

ctk.CTkLabel(
    icon_card,
    text="Select icon",
    font=ctk.CTkFont(size=13, weight="bold"),
    text_color=TEXT_PRIMARY
).pack(anchor="w", padx=20, pady=(16, 10))

icons_grid = ctk.CTkFrame(icon_card, fg_color="transparent")
icons_grid.pack(padx=16, pady=(0, 14))

icon_list = ["★", "♪", "⏵", "⏸", "⏹", "⏭", "⏮", "✂", "✦",
             "⬆", "⬇", "⬅", "➡", "⟳", "⌘", "⎋", "⏎", "⌫",
             "⇥", "⇧", "⌃", "⌥", "E", "S", "F"]

selected_icon_idx = 8

for i, icon in enumerate(icon_list):
    is_sel = (i == selected_icon_idx)
    icon_btn = ctk.CTkButton(
        icons_grid,
        text=icon,
        width=36,
        height=36,
        corner_radius=6,
        font=ctk.CTkFont(size=15),
        fg_color=ACCENT_DIM if is_sel else BG_KEY,
        hover_color=BG_KEY_HOV,
        text_color=TEXT_PRIMARY,
        border_width=1 if is_sel else 0,
        border_color=BG_KEY,
    )
    icon_btn.grid(row=i // 5, column=i % 5, padx=2, pady=2)






root.mainloop()
