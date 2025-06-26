import customtkinter as ctk
import json
import os
import subprocess
import time
import threading
from tkinter import messagebox

def load_config():
    config_file = "config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"streams": [], "dropdown_options": ["Option 1", "Option 2", "Option 3"]}
    else:
        default_config = {
            "streams": [],
            "dropdown_options": ["Option 1", "Option 2", "Option 3"]
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config
config_data = load_config()

programm = True
services = []
tasks = {}


def mediamtx():
    tasks["mediamtx"] = "mediamtx.exe"
    proc = subprocess.Popen(["mediamtx.exe"])
    threading.current_thread().proc = proc
    proc.wait()
    del tasks["mediamtx"]
    print("mediamtx.exe beendet")

def stream(http, rtsp, kategorie, name):
    time.sleep(3.5)

    tasks[name] = kategorie
    command = []

    for e in config_data["options"][kategorie]:
        add = ""
        match e:
            case "http_url":
                add = str(http)
            case "rtsp_url":
                add = "rtsp://localhost:8554/"+str(rtsp)
            case _:
                add = str(e)
        command.append(add)
    
    #print(command)

    proc = subprocess.Popen(command)
    threading.current_thread().proc = proc
    proc.wait()
    del tasks[name]
    print("HTTP Empfang beendet!")          

def start_server():
    print("Server start")

    service = threading.Thread(target=mediamtx, name="mediamtx")
    service.start()
    services.append(service)

    
    for s in config_data["streams"]:

        service = threading.Thread(target=stream, args=( s["http_url"], s["rtsp_name"], s["category"], s["name"]), name="http_empfangs_stream")
        service.start()
        services.append(service)
    
def stop_server():
    print("Server wird gestoppt...")
    for s in services:
        proc = getattr(s, "proc", None)
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"{s.name} beendet.")
            except Exception as e:
                print(f"Fehler beim Beenden von {s.name}: {e}")
    


class StreamManagerApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("Stream Manager")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        self.config_file = "config.json"
        self.task_labels = {}  # Dictionary um die Task-Labels zu verwalten
        self.current_tasks = {}  # Kopie der aktuellen Tasks um Changes zu erkennen
        
        self.create_widgets()
        self.load_streams()

        h1 = threading.Thread(target=self.show_tasks, name="show_tasks")
        h1.start()

    def show_tasks(self):
        while programm:
            time.sleep(2)
            # Verwende after() um GUI-Updates im Hauptthread auszuführen
            self.root.after(0, self.update_task_display)

    def update_task_display(self):
        """Aktualisiert die Task-Anzeige nur wenn sich etwas geändert hat"""
        try:
            # Prüfe ob sich die Tasks geändert haben
            if self.current_tasks != tasks:
                print("Aktive Tasks:")
                
                # Entferne Labels für Tasks die nicht mehr existieren
                tasks_to_remove = []
                for task_name in self.task_labels:
                    if task_name not in tasks:
                        self.task_labels[task_name].destroy()
                        tasks_to_remove.append(task_name)
                
                for task_name in tasks_to_remove:
                    del self.task_labels[task_name]
                
                # Füge neue Tasks hinzu oder aktualisiere existierende
                row = 0
                for name, task in tasks.items():
                    if name not in self.task_labels:
                        # Neues Label erstellen
                        self.task_labels[name] = ctk.CTkLabel(
                            self.right_content,
                            text=f"{name}: {task}",
                            font=ctk.CTkFont(size=14),
                            height=30,
                            fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"],
                            corner_radius=10
                        )
                    else:
                        # Existierendes Label aktualisieren
                        self.task_labels[name].configure(text=f"{name}: {task}")
                    
                    # Label positionieren
                    self.task_labels[name].grid(row=row, column=0, padx=10, pady=5, sticky="ew")
                    row += 1
                
                # Konfiguriere Grid-Gewichtung für bessere Darstellung
                self.right_content.grid_columnconfigure(0, weight=1)
                
                # Aktualisiere die Kopie der aktuellen Tasks
                self.current_tasks = tasks.copy()
                
        except Exception as e:
            print(f"Fehler beim Aktualisieren der Task-Anzeige: {e}")
        
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Konfiguration nicht speichern: {e}")
    
    def create_widgets(self):
        # Hauptframe
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Root Grid-Konfiguration
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Main Frame Grid-Konfiguration
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Topbar
        self.topbar = ctk.CTkFrame(self.main_frame, height=60)
        self.topbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.topbar.grid_propagate(False)
        self.topbar.grid_columnconfigure(1, weight=1)
        
        self.add_stream_btn = ctk.CTkButton(
            self.topbar,
            text="Add Stream",
            command=self.open_add_stream_dialog,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.add_stream_btn.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        self.title_label = ctk.CTkLabel(
            self.topbar,
            text="Stream Manager",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.grid(row=0, column=2, padx=20, pady=10, sticky="e")
        
        # Content Frame
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 10))
        
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Linker Frame (Stream Konfigurationen)
        self.left_frame = ctk.CTkFrame(self.content_frame)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(1, weight=1)
        
        self.left_title = ctk.CTkLabel(
            self.left_frame,
            text="Stream Konfigurationen",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.left_title.grid(row=0, column=0, pady=(20, 10))
        
        self.streams_scroll = ctk.CTkScrollableFrame(self.left_frame)
        self.streams_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Rechter Frame (Aktive Tasks)
        self.right_frame = ctk.CTkFrame(self.content_frame)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=1)
        
        self.right_title = ctk.CTkLabel(
            self.right_frame,
            text="Aktive Tasks",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.right_title.grid(row=0, column=0, pady=(20, 10))
        
        self.right_content = ctk.CTkFrame(self.right_frame)
        self.right_content.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.right_content.grid_columnconfigure(0, weight=1)
        
        # Entferne den Placeholder-Label da er durch die dynamischen Task-Labels ersetzt wird
    
    def open_add_stream_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Stream hinzufügen")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"500x500+{x}+{y}")
        
        # Dialog Grid-Konfiguration
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(0, weight=1)
        
        main_frame = ctk.CTkFrame(dialog)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            main_frame,
            text="Neuen Stream hinzufügen",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 30))
        
        # Name Input
        name_label = ctk.CTkLabel(main_frame, text="Stream Name:")
        name_label.grid(row=1, column=0, sticky="w", padx=20)
        name_entry = ctk.CTkEntry(main_frame, placeholder_text="Name eingeben...")
        name_entry.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 15))
        
        # HTTP URL Input
        http_label = ctk.CTkLabel(main_frame, text="HTTP Stream URL:")
        http_label.grid(row=3, column=0, sticky="w", padx=20)
        http_entry = ctk.CTkEntry(main_frame, placeholder_text="http://...")
        http_entry.grid(row=4, column=0, sticky="ew", padx=20, pady=(5, 15))
        
        # RTSP Name Input
        rtsp_label = ctk.CTkLabel(main_frame, text="RTSP Stream Name:")
        rtsp_label.grid(row=5, column=0, sticky="w", padx=20)
        rtsp_entry = ctk.CTkEntry(main_frame, placeholder_text="RTSP Name eingeben...")
        rtsp_entry.grid(row=6, column=0, sticky="ew", padx=20, pady=(5, 15))
        
        # Dropdown für Kategorien
        options = []
        for k,v  in config_data["options"].items():
            options.append(k)
        print(options)

        dropdown_label = ctk.CTkLabel(main_frame, text="Kategorie:")
        dropdown_label.grid(row=7, column=0, sticky="w", padx=20)
        dropdown = ctk.CTkComboBox(
            main_frame,
            values=options,
            state="readonly"
        )
        dropdown.grid(row=8, column=0, sticky="ew", padx=20, pady=(5, 30))
        dropdown.set(dropdown.cget("values")[0])
        
        # Button Frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=9, column=0, sticky="ew", padx=20, pady=(0, 20))
        button_frame.grid_columnconfigure(0, weight=1)
        
        def save_stream():
            name = name_entry.get().strip()
            http_url = http_entry.get().strip()
            rtsp_name = rtsp_entry.get().strip()
            category = dropdown.get()
            
            if not all([name, http_url, rtsp_name]):
                messagebox.showerror("Fehler", "Bitte füllen Sie alle Felder aus!")
                return
            
            new_stream = {
                "name": name,
                "http_url": http_url,
                "rtsp_name": rtsp_name,
                "category": category
            }
            
            config_data["streams"].append(new_stream)
            self.save_config()
            self.load_streams()
            dialog.destroy()
            messagebox.showinfo("Erfolg", f"Stream '{name}' wurde hinzugefügt!")
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Speichern",
            command=save_stream
        )
        save_btn.grid(row=0, column=0, sticky="e", padx=(0, 10))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Abbrechen",
            command=dialog.destroy,
            fg_color="gray",
            hover_color="dark gray"
        )
        cancel_btn.grid(row=0, column=1, sticky="e")
        
        name_entry.focus()
    
    def create_stream_item(self, stream_data, row):
        item_frame = ctk.CTkFrame(self.streams_scroll)
        item_frame.grid(row=row, column=0, sticky="ew", pady=5, padx=5)
        item_frame.grid_columnconfigure(0, weight=1)
        
        name_label = ctk.CTkLabel(
            item_frame,
            text=stream_data["name"],
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))
        
        info_text = f"HTTP: {stream_data['http_url']}\nRTSP: {stream_data['rtsp_name']}\nKategorie: {stream_data['category']}"
        info_label = ctk.CTkLabel(
            item_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        info_label.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 5))
        
        btn_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        btn_frame.grid_columnconfigure(0, weight=1)
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Löschen",
            command=lambda: self.delete_stream(stream_data),
            width=80,
            height=25,
            fg_color="red",
            hover_color="dark red",
            font=ctk.CTkFont(size=11)
        )
        delete_btn.grid(row=0, column=1, sticky="e", padx=5)
    
    def delete_stream(self, stream_data):
        config_data["streams"] = [s for s in config_data["streams"] if s != stream_data]
        self.save_config()
        self.load_streams()
    
    def load_streams(self):
        # Entferne alle existierenden Widgets
        for widget in self.streams_scroll.winfo_children():
            widget.destroy()
        
        # Konfiguriere Grid-Gewichtung
        self.streams_scroll.grid_columnconfigure(0, weight=1)
        
        if not config_data["streams"]:
            no_streams_label = ctk.CTkLabel(
                self.streams_scroll,
                text="Keine Streams konfiguriert\nVerwenden Sie 'Add Stream' um einen hinzuzufügen",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_streams_label.grid(row=0, column=0, pady=50)
        else:
            for row, stream in enumerate(config_data["streams"]):
                self.create_stream_item(stream, row)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    start_server()
    app = StreamManagerApp()
    app.run()
    programm = False
    stop_server()