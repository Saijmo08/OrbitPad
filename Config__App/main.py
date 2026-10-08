import customtkinter as ctk
import os
import csv


#Settings

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orbitpad_config.csv")
CSV_FIELDS = ["profile", "layer", "key", "icon", "title", "shortcut"]
NUM_KEYS = 12


BOARD_STATUS = False
PORT = "COM4"
ICON_PATH = r"C:\Users\leolu\OneDrive\Dokumente\GitHub\OrbitPad\app.ico"

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

APP_PROFILES = [
    ("Default", True),
    ("KiCad",      False),
    ("Photoshop",  False),
    ("VS Code",    False),
    ("Fusion 360", False),
]
MAX_PROFILES = 12

EDIT_FIELDS = [
    ("Icon",     "z.B. ^, ★, ✂"),
    ("Title",    "z.B. Copy"),
    ("Shortcut", "z.B. Ctrl+Z, F6, Win+D"),
]

KEYS_DATA = [
    ("^Z", "Rückgängig"), ("^Y", "Wiederholen"), ("^C", "Kopieren"),   ("^V", "Einfügen"),
    ("E",  "Extrude"),    ("S",  "Sketch"),      ("P",  "Press/Pull"), ("F",  "Fillet"),
    ("F6", "Ansicht"),    ("L",  "Line"),        ("C",  "Circle"),     ("▲",  "Layer +"),
]

ENCODERS = [("ENC 1", "Volume"), ("ENC 2", "Zoom")]


ICON_LIST = ["★", "♪", "⏵", "⏸", "⏹", "⏭", "⏮", "✂", "✦",
             "⬆", "⬇", "⬅", "➡", "⟳", "⌘", "⎋", "⏎", "⌫",
             "⇥", "⇧", "⌃", "⌥", "E", "S", "F"]

MAX_LAYERS = 4


class ConfigShop:
    def __init__(self, path=CONFIG_FILE):
        self.path = path
        self.data = {}
        self.load()
        if not self.data:
            self.create_defaults()

    @staticmethod
    def empty_keys():
        return [{"icon": "", "title": "", "shortcut": ""} for _ in range(NUM_KEYS)]

    def load(self):
        self.data = {}
        if not os.path.exists(self.path):
            return
        with open(self.path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                layers = self.data.setdefault(row["profile"], {})
                keys = layers.setdefault(row["layer"], self.empty_keys())
                idx = int(row["key"]) - 1
                if 0 <= idx < NUM_KEYS:
                    keys[idx] = {
                        "icon": row["icon"],
                        "title": row["title"],
                        "shortcut": row["shortcut"]
                    }

    def save(self):
        with open (self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for profile, layers in self.data.items():
                for layer, keys in layers.items():
                    for i, key in enumerate(keys):
                        writer.writerow({"profile": profile, "layer": layer, "key": i + 1, **key})

    def create_defaults(self):
        for name, active in APP_PROFILES:
            self.data[name] = {"Default": self.empty_keys()}
        default_profile = self.data["Default"]
        for i, (symbol, label) in enumerate(KEYS_DATA):
            default_profile["Default"][i] = {"icon": symbol, "title": label, "shortcut": ""}
        default_profile["Advanced"] = self.empty_keys()
        self.save()


    def profiles(self):
        return list(self.data)
    def layers(self, profile):
        return list(self.data[profile])
    def keys(self, profile, layer):
        return list(self.data[profile][layer])


    def set_key(self, profile, layer, idx, values):
        self.data[profile][layer][idx] = dict(values)
        self.save()

    def add_profile(self, name):
        self.data[name] = {"Default": self.empty_keys()}
        self.save()

    def remove_profile(self, name):
        self.data.pop(name)
        self.save()

    def add_layer(self, profile, name):
        self.data[profile][name] = self.empty_keys()
        self.save()

    def remove_layer(self, profile, name):
        self.data[profile].pop(name)
        self.save()

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, shop, active_profile, on_profile_change=None):
        super().__init__(parent, width=220, fg_color=BG_SIDEBAR, corner_radius=0)
        self.pack_propagate(False)

        self.shop = shop
        self.active_profile = active_profile
        self.on_profile_change = on_profile_change
        self.profile_widgets = []

        self.build_logo()
        self.build_profiles()
        self.build_status()

    def build_logo(self):
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(24, 8))

        ctk.CTkLabel(
            logo_frame,
            text="🚀 OrbitPad",
            font=ctk.CTkFont(family="Helvetica", size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="nw")

        ctk.CTkLabel(
            logo_frame,
            text="Configurator v1.0",
            font=ctk.CTkFont(family="Helvetica", size=11),
            text_color=TEXT_SEC,
        ).pack(anchor="w")

    def build_profiles(self):
        for widget in self.profile_widgets:
            widget.destroy()
        self.profile_widgets.clear()
   
        heading = ctk.CTkLabel(
            self,
            text="APP-PROFILES",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_SEC,
        )
        heading.pack(anchor="w", padx=20, pady=(0, 6))
        self.profile_widgets.append(heading)

        profiles = self.shop.profiles()
        for name in profiles:
            active = (name == self.active_profile)
            button = ctk.CTkButton(
                self,
                text=name,
                anchor="w",
                height=36,
                corner_radius=6,
                font=ctk.CTkFont(size=12),
                fg_color=ACCENT_DIM if active else "transparent",
                hover_color=BG_KEY_HOV,
                text_color=TEXT_PRIMARY if active else TEXT_SEC,
                border_width=0,
                command=lambda n=name: self.change_profile(n),
            )
            button.pack(anchor="w", padx=10, pady=1, fill="x")
            button.bind("<Button-3>", lambda event, n=name: self.remove_profile(n))
            self.profile_widgets.append(button)

        add_button = ctk.CTkButton(
            self,
            text="+ New profile",
            anchor="w",
            height=35,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=BG_KEY_HOV,
            text_color=ACCENT,
            border_width=0,
            command=self.add_profile,
            state="normal" if len(profiles) < MAX_PROFILES else "disabled",
        )
        add_button.pack(anchor="w", padx=10, pady=1, fill="x")
        self.profile_widgets.append(add_button)

    def add_profile(self):
        dialog = ctk.CTkInputDialog(text="Name of Profile:", title="New Profile")
        name = dialog.get_input()
        if not name or not name.strip():
            return

        name = name.strip().title()
        if name not in self.shop.profiles():
            if len(self.shop.profiles()) >= MAX_PROFILES:
                return
            self.shop.add_profile(name)
        self.active_profile = name
        self.notify()
            
    def remove_profile(self, name):
        if len(self.shop.profiles()) <= 1:
            return
        self.shop.remove_profile(name)
        if name == self.active_profile:
            self.active_profile = self.shop.profiles()[0]
        self.notify()

    def notify(self):
        self.build_profiles()
        if self.on_profile_change:
            self.on_profile_change(self.active_profile)

    def change_profile(self, name):
        self.active_profile = name
        self.notify()

    def build_status(self):
        status_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10)
        status_frame.pack(side="bottom", fill="x", padx=10, pady=15)

        ctk.CTkLabel(
            status_frame,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color=SUCCESS if BOARD_STATUS else WARNING,
        ).pack(side="left", padx=(12, 4), pady=10)

        ctk.CTkLabel(
            status_frame,
            text="OrbitPad connected" if BOARD_STATUS else "OrbitPad disconnected",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_PRIMARY,
        ).pack(side="left", pady=10)

        ctk.CTkLabel(
            status_frame,
            text=PORT if BOARD_STATUS else "",
            font=ctk.CTkFont(size=10),
            text_color=TEXT_SEC,
        ).pack(side="right", padx=12, pady=10)



class TopBar(ctk.CTkFrame):
    def __init__(self, parent, shop, profile, on_layer_change=None):
        super().__init__(parent, fg_color=BG_SIDEBAR, corner_radius=0, height=56)
        self.pack_propagate(False)

        self.shop = shop
        self.profile = profile
        self.active_layer = shop.layers(profile)[0]
        self.on_layer_change = on_layer_change
        self.layer_buttons = []

        self.build_title()
        self.build_layer_frame()
        self.build_save_button()
        self.draw_layers()

    def build_title(self):
        ctk.CTkLabel(
            self,
            text="Key assignment",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left", padx=(0, 20), pady=16)

    def build_layer_frame(self):
        self.layer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.layer_frame.pack(side="left", padx=10)

        ctk.CTkLabel(
            self.layer_frame,
            text="Layer:",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SEC,
        ).pack(side="left", padx=(0, 8))

    def build_save_button(self):
        ctk.CTkButton(
            self,
            text="Save on Pad",
            width=160,
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_DIM,
            text_color=TEXT_PRIMARY,
        ).pack(side="right", padx=20)

    def set_profile(self, profile):
        self.profile = profile
        self.active_layer = self.shop.layers(profile)[0]
        self.draw_layers()

    def draw_layers(self):
        for button in self.layer_buttons:
            button.destroy()
        self.layer_buttons.clear()

        layers = self.shop.layers(self.profile)
        for i, name in enumerate(layers):
            button = ctk.CTkButton(
                self.layer_frame,
                text=f"{i + 1} — {name}",
                width=110,
                height=30,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                fg_color=ACCENT if name == self.active_layer else BG_CARD,
                hover_color=ACCENT_DIM,
                command=lambda n=name: self.select_layer(n),
            )
            button.pack(side="left", padx=3)
            button.bind("<Button-3>", lambda event, n=name: self.remove_layer(n))
            self.layer_buttons.append(button)

        if len(layers) < MAX_LAYERS:
            button = ctk.CTkButton(
                self.layer_frame,
                text="+ Layer",
                width=110,
                height=30,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                text_color=ACCENT,
                border_width=1,
                border_color=BORDER,
                hover_color=BG_KEY_HOV,
                command=self.add_layer,
            )
            button.pack(side="left", padx=3)
            self.layer_buttons.append(button)

    def notify(self):
        self.draw_layers()
        if self.on_layer_change:
            self.on_layer_change(self.active_layer)
    
    def select_layer(self, name):
        self.active_layer = name
        self.notify()

    def add_layer(self):
        dialog = ctk.CTkInputDialog(text="Name of Layer:", title="New Layer")
        name = dialog.get_input()
        if not name or not name.strip():
            return

        name = name.strip().title()
        if name not in self.shop.layers(self.profile):
            self.shop.add_layer(self.profile, name)
        self.active_layer = name
        self.notify()

    def remove_layer(self, name):
        if len(self.shop.layers(self.profile)) <= 1:
            return
        self.shop.remove_layer(self.profile, name)
        if name == self.active_layer:
            self.active_layer = self.shop.layers(self.profile)[0]
        self.notify()
    


class DeviceCard(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=BG_CARD, corner_radius=14)

        self.key_widgets = []
        self.display_labels = []

        self.build_header()

        self.device_inner = ctk.CTkFrame(self, fg_color="transparent")
        self.device_inner.pack(side="left", padx=20, pady=(0, 20))

        self.build_display()
        self.build_key_grid()
        self.build_encoders()

    def build_header(self):
        self.header_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.header_label.pack(anchor="w", padx=20, pady=(16, 12))

    def set_header(self, profile, layer):
        self.header_label.configure(text=f"Active Profile: {profile} - Layer: {layer}")

    def update_keys(self, keys):
        for i, key in enumerate(keys):
            _frame, symbol_label, text_label = self.key_widgets[i]
            symbol_label.configure(text=key["icon"])
            text_label.configure(text=key["title"])
            self.display_labels[i].configure(text=key["icon"])


    def build_display(self):
        display_frame = ctk.CTkFrame(
            self.device_inner,
            width=128,
            height=128,
            fg_color="#090e14",
            corner_radius=8,
            border_width=2,
            border_color="#2a3a4a",
        )
        display_frame.pack(side="left", padx=(0, 20))
        display_frame.pack_propagate(False)

        display_grid = ctk.CTkFrame(display_frame, fg_color="transparent")
        display_grid.pack(side="left", padx=(20, 0))

        for i in range(NUM_KEYS):
            cell = ctk.CTkFrame(
                display_grid,
                width=25,
                height=25,
                fg_color="#042712",
                border_color="#3dba6f",
                corner_radius=8,
                border_width=1,
            )
            cell.grid(row=i % 4, column=i // 4, padx=2, pady=2)
            cell.pack_propagate(False)

            label = ctk.CTkLabel(
                cell,
                text="",
                font=ctk.CTkFont(size=10),
                text_color="#3dba6f",
            )
            label.place(relx=0.5, rely=0.5, anchor="center")
            self.display_labels.append(label)

    def build_key_grid(self):
        key_grid_frame = ctk.CTkFrame(self.device_inner, fg_color="transparent")
        key_grid_frame.pack(side="left")

        for i in range(NUM_KEYS):

            key_frame = ctk.CTkFrame(
                key_grid_frame,
                width=72,
                height=64,
                fg_color=BG_KEY,
                corner_radius=8,
                border_width=1,
                border_color=BORDER,
            )
            key_frame.grid(row=i % 4, column=i // 4, padx=4, pady=4)
            key_frame.pack_propagate(False)

            ctk.CTkLabel(
                key_frame,
                text=str(i + 1),
                font=ctk.CTkFont(size=9),
                text_color=TEXT_SEC,
            ).place(relx=0.0, x=5, y=-5, anchor="nw")

            symbol_label = ctk.CTkLabel(
                key_frame,
                text="",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=TEXT_PRIMARY,
            )
            symbol_label.place(relx=0.5, rely=0.38, anchor="center")

            text_label = ctk.CTkLabel(
                key_frame,
                text="",
                font=ctk.CTkFont(size=8),
                text_color=TEXT_SEC,
            )
            text_label.place(relx=0.5, rely=0.78, anchor="center")
            self.key_widgets.append((key_frame, symbol_label, text_label))


    def select_key(self, idx):
        for i, (frame, symbol_label, text_label) in enumerate(self.key_widgets):
            is_selected = (i == idx)
            frame.configure(
                fg_color=ACCENT_DIM if is_selected else BG_KEY,
                border_width=2 if is_selected else 1,
                border_color=ACCENT if is_selected else BORDER
            )
            symbol_label.configure(text_color="#ffffff" if is_selected else TEXT_PRIMARY)
            text_label.configure(text_color="#aabbff" if is_selected else TEXT_SEC)
    
    def build_encoders(self):
        encoder_row = ctk.CTkFrame(self, fg_color="transparent")
        encoder_row.pack(pady=(0, 20))

        for i, (name, func) in enumerate(ENCODERS):
            enc_frame = ctk.CTkFrame(
                encoder_row,
                width=72,
                height=72,
                fg_color=BG_KEY,
                corner_radius=36,
                border_width=1,
                border_color=BORDER,
            )
            enc_frame.grid(column=0, row=i, pady=8)
            enc_frame.pack_propagate(False)

            ctk.CTkLabel(
                enc_frame,
                text="↻",
                font=ctk.CTkFont(size=22),
                text_color=ACCENT,
            ).place(relx=0.5, rely=0.38, anchor="center")

            ctk.CTkLabel(
                enc_frame,
                text=func,
                font=ctk.CTkFont(size=8),
                text_color=TEXT_SEC,
            ).place(relx=0.5, rely=0.75, anchor="center")




class EditCard(ctk.CTkFrame):
    def __init__(self, parent, on_key_select=None, on_apply=None):
        super().__init__(parent, fg_color=BG_CARD, corner_radius=14)

        self.on_key_select = on_key_select
        self.on_apply = on_apply
        self.entries = {}
        

        self.build_header()
        self.build_fields()
        self.build_key_selector()
        self.build_apply_button()


    def build_header(self):
        self.title_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self.title_label.pack(anchor="w", padx=20, pady=(16, 4))

        self.subtitle_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SEC,
        )
        self.subtitle_label.pack(anchor="w", padx=20, pady=(0, 14))

    def build_fields(self):
        for label, placeholder in EDIT_FIELDS:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=4)

            ctk.CTkLabel(
                row,
                text=label,
                font=ctk.CTkFont(size=11),
                text_color=TEXT_SEC,
                anchor="w",
            ).pack(anchor="w", pady=(0, 2))

            entry = ctk.CTkEntry(
                row,
                height=32,
                font=ctk.CTkFont(size=12),
                fg_color=BG_KEY,
                border_color=BORDER,
                text_color=TEXT_PRIMARY,
                placeholder_text=placeholder,
            )
            entry.pack(fill="x")

            self.entries[label] = entry

    def build_key_selector(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=(8, 4))

        ctk.CTkLabel(
            frame,
            text="Key",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SEC,
            anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        self.type_menu = ctk.CTkOptionMenu(
            frame,
            values=[str(n) for n in range(1, 13)],
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color=BG_KEY,
            button_color=ACCENT_DIM,
            button_hover_color=ACCENT,
            text_color=TEXT_PRIMARY,
            dropdown_fg_color=BG_CARD,
            dropdown_text_color=TEXT_PRIMARY,
            dropdown_hover_color=BG_KEY_HOV,
            command=self.on_key_selected
        )
        self.type_menu.pack(fill="x")

    def on_key_selected(self, value):
        if self.on_key_select:
            self.on_key_select(int(value) - 1)

    def build_apply_button(self):
        self.apply_btn = ctk.CTkButton(
            self,
            text="Apply",
            height=36,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_DIM,
            text_color=TEXT_PRIMARY,
            command=self.on_apply_clicked
        )
        self.apply_btn.pack(fill="x", padx=20, pady=(12, 16))

    def on_apply_clicked(self):
        if self.on_apply:
            self.on_apply({
                "icon": self.entries["Icon"].get(),
                "title": self.entries["Title"].get(),
                "shortcut": self.entries["Shortcut"].get()
            })

    def load_key(self, idx, key, profile, layer):
        self.title_label.configure(text=f"Edit key {idx + 1}")
        self.subtitle_label.configure(text=f"{profile} - {layer}")
        self.type_menu.set(str(idx + 1))
        for field, text in (("Icon", key["icon"]), ("Title", key["title"]), ("Shortcut", key["shortcut"])):
            entry = self.entries[field]
            entry.delete(0, "end")
            entry.insert(0, text)

    def set_icon(self, icon):
        self.entries["Icon"].delete(0, "end")
        self.entries["Icon"].insert(0, icon)


class IconCard(ctk.CTkFrame):
    def __init__(self, parent, on_select=None):
        super().__init__(parent, fg_color=BG_CARD, corner_radius=14)

        self.on_select = on_select
        self.selected_icon_idx = None

        ctk.CTkLabel(
            self,
            text="Select icon",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(16, 10))

        self.build_icon_grid()

    def build_icon_grid(self):
        icons_grid = ctk.CTkFrame(self, fg_color="transparent")
        icons_grid.pack(padx=16, pady=(0, 14))
        
        self.icon_buttons = []
        for i, icon in enumerate(ICON_LIST):
            button = ctk.CTkButton(
                icons_grid,
                text=icon,
                width=36,
                height=36,
                corner_radius=6,
                font=ctk.CTkFont(size=15),
                fg_color=ACCENT_DIM if i == self.selected_icon_idx else BG_KEY,
                hover_color=BG_KEY_HOV,
                text_color=TEXT_PRIMARY,
                border_width=0,
                border_color=BG_KEY,
                command=lambda idx=i: self.select_icon(idx)
            )
            button.grid(row=i // 5, column=i % 5, padx=2, pady=2)
            self.icon_buttons.append(button)

    def select_icon(self, idx):
        self.selected_icon_idx = idx
        for i, button in enumerate(self.icon_buttons):
            button.configure(fg_color=ACCENT_DIM if i == idx else BG_KEY)
        if self.on_select:
            self.on_select(ICON_LIST[idx])



class OrbitPadApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OrbitPad Configurator")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.iconbitmap(ICON_PATH)

        self.shop = ConfigShop()
        self.profile = self.shop.profiles()[0]
        self.layer = self.shop.layers(self.profile)[0]
        self.key_idx = 0
        
        self.build_layout()
        self.refresh()

    def build_layout(self):
        
        self.sidebar = Sidebar(self, self.shop, self.profile, on_profile_change=self.on_profile_change)
        self.sidebar.pack(side="left", fill="y")

        
        main_area = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        main_area.pack(side="left", fill="both", expand=True)

        self.topbar = TopBar(main_area, self.shop, self.profile, on_layer_change=self.on_layer_change)
        self.topbar.pack(side="top", fill="x")

        mid = ctk.CTkScrollableFrame(main_area, fg_color=BG_MAIN, scrollbar_button_color=BORDER)
        mid.pack(fill="both", expand=True, padx=0, pady=0)

        inner = ctk.CTkFrame(mid, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)
        inner.columnconfigure(0, weight=3)
        inner.columnconfigure(1, weight=2)

        
        left_col = ctk.CTkFrame(inner, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self.device_card = DeviceCard(left_col)
        self.device_card.pack(fill="x", pady=(0, 16))

        
        right_col = ctk.CTkFrame(inner, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew")

        self.edit_card = EditCard(right_col, on_key_select=self.on_key_select, on_apply=self.on_apply)
        self.edit_card.pack(fill="x", pady=(0, 12))

        self.icon_card = IconCard(right_col, on_select=self.edit_card.set_icon)
        self.icon_card.pack(fill="x", pady=(0, 12))

    def on_profile_change(self, profile):
        self.profile = profile
        self.topbar.set_profile(profile)
        self.layer = self.topbar.active_layer
        self.refresh()

    def on_layer_change(self, layer):
        self.layer = layer
        self.refresh()

    def on_key_select(self, idx):
        self.key_idx = idx
        self.device_card.select_key(idx)
        self._load_edit_card()

    def on_apply(self, values):
        self.shop.set_key(self.profile, self.layer, self.key_idx, values) 
        self.device_card.update_keys(self.shop.keys(self.profile, self.layer))

    def refresh(self):
        self.device_card.set_header(self.profile, self.layer)
        self.device_card.update_keys(self.shop.keys(self.profile, self.layer))
        self.device_card.select_key(self.key_idx)
        self._load_edit_card()

    def _load_edit_card(self):
        key = self.shop.keys(self.profile, self.layer)[self.key_idx]
        self.edit_card.load_key(self.key_idx, key, self.profile, self.layer)




def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = OrbitPadApp()
    app.mainloop()


if __name__ == "__main__":
    main()