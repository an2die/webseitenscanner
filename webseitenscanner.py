# -*- coding: utf-8 -*-
"""
Erstellt: 16.04.2025
Autor: renza
"""
import os
import json
import subprocess
import threading
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from datetime import datetime, date
import google.generativeai as genai
import shlex

CONFIG_FILE = "config.json"

# ---------------------------------------------------------------------------
# Klasse zum Laden und Speichern der Konfiguration
# ---------------------------------------------------------------------------
class ConfigManager:
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        default_config = {
            "python_path": r"C:\Users\renza\Anaconda3\python.exe",
            "encoding": "utf-8",
            "ki_analysis": False,
            "gemini_model": "gemini-2.0-flash",
            "tools": [],
            "api_key": "",
            "result_path": os.path.join(os.getcwd(), "results")
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        # fehlende Felder ergänzen (z. B. bei alten configs)
                        for key, value in default_config.items():
                            loaded.setdefault(key, value)
                        return loaded
                    else:
                        print("[WARN] config.json ist kein gültiges Dictionary.")
            except Exception as e:
                print(f"[WARN] Fehler beim Laden der config.json: {e}")

        # Fallback: Standard schreiben und zurückgeben
        self.save_config(default_config)
        return default_config

    def save_config(self, config=None):
        if config is None:
            config = self.config
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        self.config = config

    def update_setting(self, key, value):
        self.config[key] = value
        self.save_config()

# ---------------------------------------------------------------------------
# Klasse, die einen einzelnen Tool-Tab darstellt und verwaltet
# ---------------------------------------------------------------------------
class ToolTab:
    def __init__(self, master, tool, config_manager, refresh_callback, app_reference):
        """
        master: übergeordnetes Frame, in dem dieser Tab eingebettet wird
        config_manager: Instanz der ConfigManager-Klasse
        refresh_callback: Callback-Funktion, die z. B. zum Neuladen der Toolliste dient
        """
        self.master = master
        self.app = app_reference
        self.process = None
        self.is_running = False
        self.tool = tool      
        self.config_manager = config_manager
        self.refresh_callback = refresh_callback
        self.frame = ctk.CTkFrame(master,border_width=3, border_color="black")
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.create_widgets()
        self.abort_requested = False
        
        
    def get_results_folder(self):
        folder = self.config_manager.config.get("result_path",
                    os.path.join(os.getcwd(), "results"))
        os.makedirs(folder, exist_ok=True)
        return folder
    
    def refresh_view(self):
        # Name updaten
        self.name_label.configure(text=f"Tool: {self.tool['name']}")
    
        # Kommando updaten
        full_cmd = self._build_full_command()
        full_cmd_str = " ".join(full_cmd)
        self.path_label.configure(text=f"Ausführungsbefehl: {full_cmd_str}")
    
    def copy_result_path(self, event=None):
        path = self.result_entry.get()
        if path:
            self.app.clipboard_clear()
            self.app.clipboard_append(path)
            messagebox.showinfo("Zwischenablage", "Pfad wurde kopiert!")

    def get_result_filepath(self, tool_name, target):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_target = target.replace(":", "_").replace("/", "_")
        filename = f"{tool_name}_{safe_target}_{timestamp}.txt"
        return os.path.join(self.get_results_folder(), filename)

    def create_widgets(self):
        # Obere Zeile: Anzeige des Tool-Namens + Bearbeiten und Löschen
        top_frame = ctk.CTkFrame(self.frame, fg_color="#2A2A2A")
        top_frame.pack(fill=tk.X,padx=10, pady=5)

        self.name_label = ctk.CTkLabel(
            top_frame,
            text=f"Tool: {self.tool['name']}",
            font=ctk.CTkFont(size=16, weight="bold"),
            wraplength=600,
            justify="left",
            anchor="w"
        )
        self.name_label.grid(row=0, column=0, sticky="w", padx=(20, 10))
        
        edit_button = ctk.CTkButton(
            top_frame,
            text="Bearbeiten",
            command=self.edit_tool,
            corner_radius=8,
            fg_color="#1ABC9C",
            hover_color="#148F77",
            text_color="black"
        )
        edit_button.grid(row=0, column=2, padx=(10, 20))
        
        delete_button = ctk.CTkButton(
                top_frame,
                text="Löschen",
                command=self.delete_tool,
                corner_radius=8,
                fg_color="#C0392B",
                hover_color="#922B21",  # dunkler beim Hover
                text_color="white"
            )
        delete_button.grid(row=0, column=1, padx=(10, 0))
        
        top_frame.columnconfigure(0, weight=1)  # Name nimmt gesamte Breite
    
        
        # Anzeige des Pfads
        full_cmd = self._build_full_command()
        full_cmd_str = " ".join(full_cmd)
        self.path_label = ctk.CTkLabel(self.frame, text=f"Ausfürhungsbefehl: {full_cmd_str}")
        self.path_label.pack(pady=5)

        # Button zum Starten des Tools
        self.is_running = False
        
        # Zugang zum Run‑Button speichern:
        self.start_button = ctk.CTkButton(self.frame, text="Tool starten", command=self.run_tool)
        self.start_button.pack(pady=5)
        
        self.stop_button = ctk.CTkButton(self.frame, text="Tool stoppen", fg_color="#E57373",hover_color="#EF5350", command=self.stop_)
        self.stop_button.pack(pady=6)
        
        # Lade-Indikator
        self.progress = ctk.CTkProgressBar(
            self.frame,
            orientation="horizontal",
            mode="indeterminate",        # hier Spinner-Modus
            border_width=1,
            border_color="black"
        )
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        self.progress.configure(mode="indeterminate")
        self.progress.set(0)
        
        # Ergebnis-Pfad-Anzeige
        self.result_label = ctk.CTkLabel(self.frame, text="Ergebnisdatei:")
        self.result_label.pack(pady=(5,0))
        self.result_entry = ctk.CTkEntry(self.frame, state="readonly")
        self.result_entry.pack(fill=tk.X, padx=5, pady=(0,5))
        self.result_entry.bind("<Button-1>", self.copy_result_path)

        # KI-Analyse (ganze Breite)
        self.ki_frame = ctk.CTkFrame(self.frame, fg_color="#2F3E46", corner_radius=10)
        self.ki_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        ki_label = ctk.CTkLabel(self.ki_frame, text="KI-Analyse", font=ctk.CTkFont(size=16, weight="bold"))
        ki_label.pack(pady=5)
        self.ki_text = ctk.CTkTextbox(self.ki_frame, state="disabled", wrap="word")
        self.ki_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.ki_text.configure(state="normal")
        self.ki_text.insert(tk.END, "\n")
        self.ki_text.configure(state="disabled")
        
        btn_frame = ctk.CTkFrame(self.ki_frame, fg_color=self.ki_frame.cget("fg_color"))
        btn_frame.pack(fill=tk.X, padx=5, pady=(0,5))   
        copy_btn = ctk.CTkButton(
            btn_frame,
            text="📋",
            command=self.copy_ki_to_clipboard,
            font=("Arial", 25, "bold"), 
            fg_color="transparent",
            width=25,
            height=25,
            corner_radius=0,
        )
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        expand_btn = ctk.CTkButton(
            btn_frame,
            text="⛶",
            font=("Arial", 25, "bold"), 
            command=self.open_ki_fullscreen,
            fg_color="transparent",
            width=25,
            height=25,
            corner_radius=0,
        )
        expand_btn.pack(side=tk.LEFT, padx=5)
        
    def copy_ki_to_clipboard(self):
        content = self.ki_text.get("1.0", tk.END)
        self.app.clipboard_clear()
        self.app.clipboard_append(content)
        messagebox.showinfo("Erfolg", "Text in Zwischenablage kopiert!")
        
    def _build_full_command(self, target="TARGET", output="OUTPUT"):
        """
        Gibt eine Liste zurück, die direkt an subprocess.run übergeben werden kann.
        """
        exe = self.tool.get("executor", "").strip()
        scr = self.tool.get("script", "").strip()
        args_t = self.tool.get("arguments", "{target}")
        args   = args_t.format(target=target, output=output)

        cmd = []
        if exe:
            cmd.append(exe)      # kein f'"{exe}"'
        cmd.append(scr)          # kein f'"{scr}"'
        cmd += args.split()      # split auf spaces ist ok, solange deine args keine Leerzeichen-Paths enthalten

        return cmd

    def open_ki_fullscreen(self):
        fullscreen = tk.Toplevel(self.app)
        fullscreen.title("KI-Analyse")
        # Versuche, das Fenster zu maximieren:
        try:
            fullscreen.state('zoomed')   # das ist auf Windows der Standard-Maximieren-Befehl
        except Exception:
            # Fallback: manuell auf volle Bildschirmgröße setzen
            w = self.app.winfo_screenwidth()
            h = self.app.winfo_screenheight()
            fullscreen.geometry(f"{w}x{h}+0+0")
        # Inhalt
        text = ctk.CTkTextbox(fullscreen, wrap="word")
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert("0.0", self.ki_text.get("1.0", tk.END))
        close_btn = ctk.CTkButton(fullscreen, text="Schließen", command=fullscreen.destroy)
        close_btn.pack(pady=10)

    def stop_(self):
        if self.process and self.is_running:
            self.abort_requested = True  
            try:
                self.process.terminate()   # oder self.process.kill() falls nötig
            except Exception as e:
                messagebox.showwarning("Stop-Fehler", f"Konnte Prozess nicht stoppen: {e}")
            finally:
                # UI zurücksetzen
                self.is_running = False
                self.master.after(0, self._scan_finished)
        else:
            messagebox.showinfo("Info", "Kein laufender Scan zum Stoppen.")

    def run_tool(self, target=""):
        # Startet die Ausführung des Tools in einem separaten Thread.
        # Standardmäßig Python-Pfad laden (immer!)
        if self.is_running:
            messagebox.showinfo("Info", "Scan läuft bereits. Bitte warten.")
            return

        # URL auslesen, Validierung
        if not target:
            target = self.app.url_entry.get().strip()
        if not target:
            messagebox.showwarning("Fehler", "Bitte zuerst eine Ziel-URL eingeben!")
            return

        # Jetzt wirklich loslegen
        self.abort_requested = False
        self.is_running = True
        self.start_button.configure(state="disabled")
        self.progress.start()   # <-- NUR hier aufrufen
        threading.Thread(
            target=self._run_tool_thread,
            args=(target, self.config_manager.config.get("python_path","python")),
            daemon=True
        ).start()

    def _run_tool_thread(self, target, python_path):
        result_filepath = self.get_result_filepath(self.tool['name'], target)
        cmd_list = self._build_full_command(target, result_filepath)
        print(cmd_list)
        try:
            with open(result_filepath, 'w', encoding='utf-8') as out:
                self.process = subprocess.Popen(
                    cmd_list,
                    stdout=out,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=False
                    )
                _, stderr = self.process.communicate()
                returncode = self.process.returncode
                
            if self.abort_requested:
                bericht = "Scan abgebrochen."
                # Ergebnis-Pfad brauchst Du nicht mehr updaten, oder:
                self.master.after(0, self.ki_bericht_anzeigen, bericht)
                self.master.after(0, self._scan_finished)
                return
                
            if returncode != 0:
                fehlertext = f"Tool-Fehler (Code {returncode}):\n{stderr}"
                # Fehler direkt anzeigen
                self.master.after(0, lambda: messagebox.showerror("Scan-Fehler", fehlertext))
                print(fehlertext)
                bericht = None
            else:
                bericht = None
        except Exception as e:
            print("Ausnahme:", e); bericht = f"Ausführungsfehler: {e}"
        # Ergebnis & KI
        self.master.after(0, self.update_output, result_filepath)
        # Nur wenn kein Fehlertext gesetzt wurde, KI-Analyse starten
        if bericht is None and os.path.exists(result_filepath) and os.path.getsize(result_filepath) > 0 and self.config_manager.config.get('ki_analysis', False):
            try:
                daten = open(result_filepath, 'r', encoding='utf-8', errors='replace').read().strip()
                bericht = self.generiere_report(daten)
            except Exception as ke:
                bericht = f"KI-Fehler: {ke}"
        else:
            bericht = bericht or "Kein Ergebnis oder KI deaktiviert."
        self.master.after(0, self.ki_bericht_anzeigen, bericht)
        self.master.after(0, self._scan_finished)
        
    def generiere_report_export(self,daten):
        api_key = self.config_manager.config.get("api_key", "")
        client = genai.Client(api_key=api_key)
        
        prompt = """
**SYSTEMANWEISUNG:** Du bist ein API-Endpunkt zur Berichterstellung. Generiere *ausschließlich* den angeforderten Sicherheitsbericht im Markdown-Format basierend auf den bereitgestellten `DATEN`. Füge KEINE einleitenden Sätze, Begrüßungen, Erklärungen ("Hier ist der Bericht:") oder abschließenden Bemerkungen hinzu. Beginne die Antwort direkt mit der ersten Zeile des Berichts (z.B. "## Sicherheitsbericht").

**AUFGABE:** Es wurde von dir schon die folgenden Daten zu einem Report analysiert. JEtzt kommen mehrere von egnerierten Reports zusammen und du muss diese zu einem kobnieren, mit der gleichen Struktur.

**BERICHTSSTRUKTUR:**

**FALL 1: Schwachstellen gefunden**

Wenn relevante Schwachstellen in den `DATEN` identifiziert werden, MUSS der Bericht die folgenden Abschnitte enthalten:

## Sicherheitsbericht

**1. Übersicht**
* **Zielsystem:** [Name/IP des gescannten Ziels, falls in `DATEN` erkennbar, sonst 'Unbekannt']
* **Tool:** [Name und Version des Tools, falls in `DATEN` erkennbar, sonst 'Unbekannt']
* **Scan-Datum:**
* **Gefundene Schwachstellen:** [Anzahl der in Tabelle 2 gelisteten Schwachstellen]
* **Geprüfte Elemente:** [Anzahl Anfragen/Checks, falls in `DATEN` erkennbar, sonst 'N/A']

**2. Schwachstellenübersicht**
| Fundstelle/Pfad | Beschreibung | Empfehlung | Priorität |
|---|---|---|---|
| [Wo?] | [Was? Wenn CVE: `[CVE-XXXX-YYYY](https://nvd.nist.gov/vuln/detail/CVE-XXXX-YYYY)`] | [Wie beheben?] | [🔴 Hoch / 🟠 Mittel / 🟢 Niedrig] |
* (Weitere Zeilen für jede gefundene Schwachstelle) *

**3. Informationsübersicht**
Hier sollen gefunde Inforamtionen aufgelistet werden, die nicht direkt Schwachstellen sind sondern potezielle sein können, wie z.B. offene Ports

**4. Handlungsempfehlungen (Top 3-5)**
*Priorisiert nach Dringlichkeit:*
* **🔴 Hoch:** [Kurze Empfehlung 1], [Kurze Empfehlung 2]
* **🟠 Mittel:** [Kurze Empfehlung 3]
* **🟢 Niedrig:** [Kurze Empfehlung 4]
*(Nur Prioritäten auflisten, für die Empfehlungen existieren. Fasse die wichtigsten Empfehlungen aus Tabelle 2 zusammen.)*
    """
        full_prompt = prompt + "\n```\n" + daten + "\n```"
        print(full_prompt)
        model= self.config_manager.config.get("gemini_model")

        response = client.models.generate_content(
            model=model,
            contents=full_prompt
            
        )
    
        return response.text.strip()

    def generiere_report(self,daten):
        api_key = self.config_manager.config.get("api_key", "")
        
        client = genai.Client(api_key=api_key)
        
        prompt = """
**SYSTEMANWEISUNG:** Du bist ein API-Endpunkt zur Berichterstellung. Generiere *ausschließlich* den angeforderten Sicherheitsbericht im Markdown-Format basierend auf den bereitgestellten `DATEN`. Füge KEINE einleitenden Sätze, Begrüßungen, Erklärungen ("Hier ist der Bericht:") oder abschließenden Bemerkungen hinzu. Beginne die Antwort direkt mit der ersten Zeile des Berichts (z.B. "## Sicherheitsbericht").

**AUFGABE:** Analysiere die folgenden `DATEN` eines Sicherheitstools und erstelle daraus einen kompakten, klar strukturierten Sicherheitsbericht.

**BERICHTSSTRUKTUR:**

**FALL 1: Schwachstellen gefunden**

Wenn relevante Schwachstellen in den `DATEN` identifiziert werden, MUSS der Bericht die folgenden Abschnitte enthalten:

## Sicherheitsbericht

**1. Übersicht**
* **Zielsystem:** [Name/IP des gescannten Ziels, falls in `DATEN` erkennbar, sonst 'Unbekannt']
* **Tool:** [Name und Version des Tools, falls in `DATEN` erkennbar, sonst 'Unbekannt']
* **Scan-Datum:**
* **Gefundene Schwachstellen:** [Anzahl der in Tabelle 2 gelisteten Schwachstellen]
* **Geprüfte Elemente:** [Anzahl Anfragen/Checks, falls in `DATEN` erkennbar, sonst 'N/A']

**2. Schwachstellenübersicht**
| Fundstelle/Pfad | Beschreibung | Empfehlung | Priorität |
|---|---|---|---|
| [Wo?] | [Was? Wenn CVE: `[CVE-XXXX-YYYY](https://nvd.nist.gov/vuln/detail/CVE-XXXX-YYYY)`] | [Wie beheben?] | [🔴 Hoch / 🟠 Mittel / 🟢 Niedrig] |
* (Weitere Zeilen für jede gefundene Schwachstelle) *

**3. Informationsübersicht**
Hier sollen gefunde Inforamtionen aufgelistet werden, die nicht direkt Schwachstellen sind sondern potezielle sein können, wie z.B. offene Ports

**4. Handlungsempfehlungen (Top 3-5)**
*Priorisiert nach Dringlichkeit:*
* **🔴 Hoch:** [Kurze Empfehlung 1], [Kurze Empfehlung 2]
* **🟠 Mittel:** [Kurze Empfehlung 3]
* **🟢 Niedrig:** [Kurze Empfehlung 4]
*(Nur Prioritäten auflisten, für die Empfehlungen existieren. Fasse die wichtigsten Empfehlungen aus Tabelle 2 zusammen.)*
    """
        model= self.config_manager.config.get("gemini_model")
        full_prompt = prompt + "\n```\n" + daten + "\n```"
        print(full_prompt)

        response = client.models.generate_content(
            model=model,
            contents=full_prompt
            
        )
    
        return response.text.strip()
    
    def update_output(self, output_path):
        # Zeigt nur den Pfad zur Ergebnisdatei an
        self.result_entry.configure(state="normal")
        self.result_entry.delete(0, tk.END)
        self.result_entry.insert(0, output_path)
        self.result_entry.configure(state="disabled")
  
    def ki_bericht_anzeigen(self, bericht):
        self.ki_text.configure(state="normal")      # Textfeld editierbar machen
        self.ki_text.delete("1.0", tk.END)          # Lösche bisherigen Platzhalter
        self.ki_text.insert(tk.END, bericht)        # KI-Bericht einfügen
        self.ki_text.configure(state="disabled")    # Textfeld deaktivieren
        self.ki_text.see(tk.END) 

    def edit_tool(self):
        dlg = ctk.CTkToplevel(self.app); dlg.transient(self.app); dlg.grab_set(); dlg.title("Tool bearbeiten"); dlg.geometry("600x400")
        # Felder: Name, Executor, Script, Arguments
        for label, val in [("Tool-Name:", self.tool['name']), ("Executor:", self.tool.get('executor','')), ("Script/Datei:", self.tool['script']), ("Arguments:", self.tool.get('arguments','{target}'))]:
            ctk.CTkLabel(dlg, text=label).pack(pady=5)
            ent = ctk.CTkEntry(dlg); ent.pack(pady=5, fill=tk.X, padx=10); ent.insert(0,val)
            if label=="Tool-Name:": name_entry=ent
            elif label.startswith("Executor"): exec_entry=ent
            elif label.startswith("Script"): script_entry=ent
            else: args_entry=ent
    
        def browse():
            fp=filedialog.askopenfilename(title="Datei auswählen", filetypes=[("Alle Dateien","*.*")]);
            if fp: script_entry.delete(0,tk.END); script_entry.insert(0,fp)
    
        def save():
            n=name_entry.get().strip(); ex=exec_entry.get().strip(); sc=script_entry.get().strip(); ar=args_entry.get().strip()
            if not n or not sc: messagebox.showerror("Fehler","Name+Script erforderlich"); return
            self.tool.update({'name':n,'executor':ex,'script':sc,'arguments':ar})
            for t in self.config_manager.config['tools']:
                if t.get('name')==self.name_label.cget('text').replace("Tool: ",""):
                    t.update(self.tool); break
            self.config_manager.save_config(); dlg.destroy(); self.refresh_callback()
            self.name_label.after(0, self.refresh_view)
        ctk.CTkButton(dlg, text="Speichern", command=save).pack(pady=10)


    def delete_tool(self):
        # Bestätigung zum Löschen
        if messagebox.askyesno("Tool löschen", "Soll dieses Tool wirklich gelöscht werden?"):
            tools = self.config_manager.config.get("tools", [])
            # Entferne das Tool anhand des Namens
            updated_tools = [t for t in tools if t.get("name") != self.tool["name"]]
            self.config_manager.config["tools"] = updated_tools
            self.config_manager.save_config()
            self.frame.destroy() # Aktualisiere die Tool-Liste
            
            
    def _scan_finished(self):
        self.is_running = False
        self.start_button.configure(state="normal")
        self.progress.stop()
        self.progress.set(0)

# ---------------------------------------------------------------------------
# Hauptanwendungsklasse (GUI)
# ---------------------------------------------------------------------------
class Application(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Webseitenscanner")
        self.update_idletasks()           
        self.geometry("1200x800")  
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.configure(fg_color="#2A2A2A")
 
        self.config_manager = ConfigManager()
        
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 0), anchor="n")
        self.tabview.add("Einstellungen")
        self.tabview.add("Tools")
        self.tabview.set("Tools")



        self.create_settings_page()
        self.create_tools_page()
    def reload_tools_view(self):
        # 1) Alle alten Frames und Objekte entfernen
        for tab in self.tool_tabs:
            tab.frame.destroy()
        self.tool_tabs.clear()

        # 2) Tools aus der config neu holen und sortieren
        raw_tools   = self.config_manager.config.get("tools", [])
        sorted_tools= sorted(raw_tools, key=lambda t: t.get("name","").lower())

        # 3) Für jedes Tool ein neues ToolTab anlegen
        for tool in sorted_tools:
            tab_frame = ctk.CTkFrame(self.tools_container)
            tab_frame.pack(fill=tk.X, pady=5, padx=5)
            new_tab = ToolTab(tab_frame, tool, self.config_manager,
                              self._do_nothing, app_reference=self)
            self.tool_tabs.append(new_tab)

        # Falls schon ein Suchbegriff drinsteht, wende ihn an
            self.load_tool_tabs()

    # -----------------------------------------------------------
    # Seite "Einstellungen"
    # -----------------------------------------------------------
    def create_settings_page(self):
            frame = self.tabview.tab("Einstellungen")
            # Auf dunkel umstellen passend zu den anderen Seiten
            frame.configure(fg_color="#2A2A2A")
            frame.columnconfigure(1, weight=1)
    
            # Einstellung: Python-Exe-Pfad
            python_path_label = ctk.CTkLabel(frame, text="Pfad zu Python:")
            python_path_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            
            # Feldbreite erhöht
            self.python_path_entry = ctk.CTkEntry(frame, width=400)
            self.python_path_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
            self.python_path_entry.insert(0, self.config_manager.config.get("python_path", ""))
            browse_button = ctk.CTkButton(frame, text="Durchsuchen", command=self.browse_python_path)
            browse_button.grid(row=0, column=2, padx=10, pady=10)
    
            # Einstellung: Encoding
            encoding_label = ctk.CTkLabel(frame, text="Encoding:")
            encoding_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
            # Feldbreite erhöht
            self.encoding_entry = ctk.CTkEntry(frame, width=400)
            self.encoding_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
            self.encoding_entry.insert(0, self.config_manager.config.get("encoding", "utf-8"))
            

            #Result PAth
            result_path_label = ctk.CTkLabel(frame, text="Ergebnis-Pfad:")
            result_path_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
            self.result_path_entry = ctk.CTkEntry(frame, width=400)
            self.result_path_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
            self.result_path_entry.insert(0, 
                 self.config_manager.config.get("result_path","results"))
            
            browse_result_btn = ctk.CTkButton(frame, text="Durchsuchen", 
                command=self.browse_result_path)
            browse_result_btn.grid(row=2, column=2, padx=10, pady=10)
            
            # API-Key
            api_label = ctk.CTkLabel(frame, text="API-Key:")
            api_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
            self.api_entry = ctk.CTkEntry(frame, width=400, show="*")
            self.api_entry.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
            # Aktuellen Wert laden
            self.api_entry.insert(0, self.config_manager.config.get("api_key", ""))
            
            # Label
            gemini_label = ctk.CTkLabel(frame, text="Gemini-Modell:")
            gemini_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
            
            # OptionMenu (Liste beliebig erweitern)
            model_options = ["gemini-2.0-flash","gemini-2.5-pro-exp-03-25", "gemini-2.5-pro", "gemini-1.0"]
            self.gemini_menu = ctk.CTkOptionMenu(frame, values=model_options)
            self.gemini_menu.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
            # akt. Wert setzen
            current = self.config_manager.config.get("gemini_model", model_options[0])
            self.gemini_menu.set(current)
            
            # KI-Analyse-Switch
            self.ki_switch = ctk.CTkSwitch(frame, text="KI-Analyse aktivieren")
            # optional: aktuellen Wert setzen
            if self.config_manager.config.get("ki_analysis", False):
                self.ki_switch.select()
            else:
                self.ki_switch.deselect()
            # Hier in Spalte 0 über alle 3 Columns spannen, damit er sicher sichtbar ist
            self.ki_switch.grid(row=5, column=0, columnspan=3, sticky="w", padx=10, pady=10)
               
                        
            # Button zum Speichern der Einstellungen
            save_button = ctk.CTkButton(
                frame,
                text="Einstellungen speichern",
                command=self.save_settings,
                corner_radius=8,
                fg_color="#1ABC9C",
                hover_color="#148F77"
            )
            # Breiter ausrichten
            save_button.grid(row=7, column=0, columnspan=3, pady=20, padx=10, sticky="ew")
    
            self.tools_overview_frame = ctk.CTkFrame(frame, fg_color="#353535")
            self.tools_overview_frame.grid(row=8, column=0, columnspan=3, sticky="ew", padx=10, pady=(0,10))
    
            ctk.CTkLabel(
                self.tools_overview_frame,
                text="Aktuelle Tools:",
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(anchor="w", padx=5, pady=(5,2))
    
            # Container für die Namen
            self.tools_list_container = ctk.CTkFrame(self.tools_overview_frame, fg_color="#2A2A2A")
            self.tools_list_container.pack(fill="both", expand=False, padx=5, pady=(0,5))
    
            # Und zum ersten Mal füllen:
            self._update_tools_overview()
    def _update_tools_overview(self):
        # lösche alte Einträge
        for w in self.tools_list_container.winfo_children():
            w.destroy()
    
        tools = self.config_manager.config.get("tools", [])
        if not tools:
            ctk.CTkLabel(
                self.tools_list_container,
                text="(Keine Tools vorhanden)",
                text_color="#888888"
            ).pack(anchor="w", padx=5, pady=2)
            return
    
        # für jedes Tool nur den Namen anzeigen
        for t in tools:
            name = t.get("name", "<unbenannt>")
            path = t.get("script", "")
            ctk.CTkLabel(
                self.tools_list_container,
                text=f"• {name} → {os.path.basename(path)}",
                anchor="w",
                font=ctk.CTkFont(size=12)
            ).pack(fill="x", padx=5, pady=1)


    def _save_to_file(self, text):
        fp = filedialog.asksaveasfilename(
            parent=self,
            title="Export speichern",
            defaultextension=".md",
            filetypes=[("Markdown-Dateien","*.md"),("Text-Dateien","*.txt")]
        )
        if not fp:
            return
        try:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(text)
            messagebox.showinfo("Export", f"Erfolgreich gespeichert:\n{fp}", parent=self)
        except Exception as e:
            messagebox.showerror("Export-Error", f"Konnte nicht speichern:\n{e}", parent=self)

    def browse_result_path(self):
        folder = filedialog.askdirectory(title="Ergebnis-Ordner wählen")
        if folder:
            self.result_path_entry.delete(0, tk.END)
            self.result_path_entry.insert(0, folder)
            
    def browse_python_path(self):
        file_path = filedialog.askopenfilename(
            title="Python-Executable auswählen",
            filetypes=[("Python executables", "*.exe")]
        )
        if file_path:
            self.python_path_entry.delete(0, tk.END)
            self.python_path_entry.insert(0, file_path)

    def save_settings(self):
        python_path = self.python_path_entry.get().strip()
        encoding = self.encoding_entry.get().strip()
        result_path = self.result_path_entry.get().strip()
        api_key = self.api_entry.get().strip()
        ki_enabled = self.ki_switch.get() 
        gemini_model = self.gemini_menu.get()
        self.config_manager.update_setting("gemini_model", gemini_model)
        self.config_manager.update_setting("python_path", python_path)
        self.config_manager.update_setting("encoding", encoding)
        self.config_manager.update_setting("result_path", result_path)
        self.config_manager.update_setting("ki_analysis", ki_enabled)
        self.config_manager.update_setting("api_key", api_key)
        messagebox.showinfo("Einstellungen", "Einstellungen gespeichert!")
        self._update_tools_overview()

    # -----------------------------------------------------------
    # Seite "Tools" zur Verwaltung der Tools
    # -----------------------------------------------------------
    def create_tools_page(self):
        frame = self.tabview.tab("Tools")
        frame.configure(fg_color="#2A2A2A")
    
        toolbar = ctk.CTkFrame(frame, fg_color="#353535")
        toolbar.pack(fill=tk.X, pady=10, padx=10)
    
        # LINKS: URL-Feld + Buttons
        ctk.CTkLabel(toolbar, text="Ziel-URL:").pack(side=tk.LEFT, padx=5, pady=5)
        self.url_entry = ctk.CTkEntry(toolbar, width=200)
        self.url_entry.pack(side=tk.LEFT, padx=5, pady=5)
    
        ctk.CTkButton(toolbar, text="Tool hinzufügen", command=self.add_tool,
                      fg_color="#3498DB", hover_color="#2980B9").pack(side=tk.LEFT, padx=5, pady=5)
        ctk.CTkButton(toolbar, text="Alle Tools starten", command=self.start_all_tools,
                      fg_color="#3498DB", hover_color="#2980B9").pack(side=tk.LEFT, padx=5, pady=5)
    
            
        # RECHTS: Suchfeld + Export
        export_btn = ctk.CTkButton(toolbar, text="Export", command=self.open_export_dialog,
                                   fg_color="#1ABC9C", hover_color="#16A085")
        export_btn.pack(side=tk.RIGHT, padx=(0,10), pady=5)
    
        self.search_entry = ctk.CTkEntry(toolbar, width=200)
        self.search_entry.pack(side=tk.RIGHT, padx=5, pady=5)
        self.search_after_id = None
        self.search_entry.bind("<KeyRelease>", self.load_tool_tabs)
        ctk.CTkLabel(toolbar, text="Tool suchen:").pack(side=tk.RIGHT, padx=(5,0), pady=5)
    
    
        # ScrollableFrame für die Tools
        self.tools_container = ctk.CTkScrollableFrame(frame)
        self.tools_container.pack(fill=tk.BOTH, expand=True, padx=10)
    
        # 1) Hole unsortierte Liste
        raw_tools = self.config_manager.config.get("tools", [])
    
        # 2) Sortiere alphabetisch nach Name (case-insensitive)
        sorted_tools = sorted(raw_tools, key=lambda t: t.get("name","").lower())
    
        # 3) Baue die Tabs in der sortierten Reihenfolge
        self.tool_tabs = []
        for tool in sorted_tools:
            tab_frame = ctk.CTkFrame(self.tools_container)
            tab_frame.pack(fill=tk.X, pady=5, padx=5)
            tool_tab = ToolTab(tab_frame, tool, self.config_manager,
                               self._do_nothing, app_reference=self)
            self.tool_tabs.append(tool_tab)

    def _do_nothing(self): 
        return
    def load_tool_tabs(self, event=None):
        query = self.search_entry.get().lower().strip()
        first_match = None
    
        # 1) Ein-/Ausblenden & erstes Match merken
        for tool_tab in self.tool_tabs:
            name = tool_tab.tool.get("name", "").lower()
            if query in name:
                tool_tab.frame.pack(fill=tk.X, pady=5, padx=5)
                if first_match is None:
                    first_match = tool_tab
            else:
                tool_tab.frame.pack_forget()
    
        # 2) Scrollen, falls Treffer
        if first_match:
            # a) Layout-Updates sicherstellen
            self.update_idletasks()
    
            # b) internes Canvas finden
            canvas = None
            for child in self.tools_container.winfo_children():
                if isinstance(child, tk.Canvas):
                    canvas = child
                    break
            if canvas is None:
                return  # Canvas nicht gefunden, abbrechen
    
            canvas.update_idletasks()
    
            # c) Scrollregion auf gesamten Inhalt setzen
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(scrollregion=bbox)
    
                # d) Pixel-Offset des ersten Treffers
                y = first_match.frame.winfo_y()
    
                # e) View- und Content-Höhen berechnen
                view_h    = canvas.winfo_height()
                content_h = bbox[3] - bbox[1]
                max_scroll = content_h - view_h
                if max_scroll <= 0:
                    fraction = 0.0
                else:
                    fraction = min(max(y / max_scroll, 0.0), 1.0)
    
                # f) Scrollen
                canvas.yview_moveto(fraction)

    def start_all_tools(self):
        target = self.url_entry.get().strip()
    
        if not target:
            messagebox.showwarning("Fehlende Ziel-URL", "Bitte gib zuerst eine Ziel-URL an.")
            return
    
        # Warnung anzeigen
        warnung = (
            "⚠️ Du bist dabei, **alle konfigurierten Tools gleichzeitig zu starten**.\n\n"
            "Dies kann folgende Auswirkungen haben:\n"
            "- Hohe Last auf dem Zielserver\n"
            "- Mögliche Firewall-/IDS-Auslösung\n"
            "- Lange Wartezeiten oder Tool-Konflikte\n\n"
            "Möchtest du wirklich fortfahren?"
        )
        antwort = messagebox.askyesno("Warnung: Alle Tools starten?", warnung)
    
        if not antwort:
            messagebox.showinfo("Abgebrochen", "Der Vorgang wurde abgebrochen.")
            return

        # Wenn bestätigt: Tools starten
        for tool_tab in self.tool_tabs:
            tool_tab.run_tool(target=target)
            

    def add_tool(self):
        dlg=ctk.CTkToplevel(self); dlg.transient(self); dlg.grab_set();dlg.lift();dlg.attributes("-topmost", True) ; dlg.title("Neues Tool")
        dlg.geometry("800x600")
        
        fields = [
            ("Name:",       "",                  "Name des Tools ggf. Hinweis/Beschreibung"),
            ("Executor:",   "",                  "python3, perl, nmap usw..."),
            ("Script/Datei:","",                 "Datei zum Programm"),
            ("Arguments:",  "{target}",          "{target} dient als Platzhalter")
        ]
        
        for label_text, default_val, placeholder in fields:
            ctk.CTkLabel(dlg, text=label_text).pack(pady=5)
            ent = ctk.CTkEntry(
                dlg,
                placeholder_text=placeholder,
                placeholder_text_color="#888888"
            )
            ent.pack(fill=tk.X, padx=10)
        
            if default_val:  # Nur wenn wirklich ein Wert vorhanden ist
                ent.insert(0, default_val)
        
            # speichere Referenz, damit Du später an die richtige Variable kommst
            if label_text == "Name:":
                n_ent = ent
            elif label_text.startswith("Executor"):
                ex_ent = ent
            elif label_text.startswith("Script"):
                sc_ent = ent
            else:
                ar_ent = ent
                

            
        def browse():
            fp = filedialog.askopenfilename(
                title="Datei auswählen",
                filetypes=[("Alle Dateien", "*.*")]
            )
            if fp:
                sc_ent.delete(0, tk.END)
                sc_ent.insert(0, fp)
        
        ctk.CTkButton(dlg, text="Durchsuchen", command=browse).pack(pady=5)
        
        
        
        def save():
            name  = n_ent.get().strip()
            execu = ex_ent.get().strip()
            scr   = sc_ent.get().strip()
            arg   = ar_ent.get().strip()
            if not name or not scr:
                messagebox.showerror("Fehler","Name+Script benötigt")
                return
        
            # 1) Neuen Eintrag in Config
            new_tool = {"name":name, "executor":execu, "script":scr, "arguments":arg}
            self.config_manager.config.setdefault("tools", []).append(new_tool)
            self.config_manager.save_config()
        
            dlg.destroy()
        
            # 2) Nur dieses eine Tab anlegen – alle anderen bleiben erhalten!
            tab_frame = ctk.CTkFrame(self.tools_container)
            tab_frame.pack(fill=tk.X, pady=5, padx=5)
            tool_tab = ToolTab(tab_frame, new_tool, self.config_manager,
                               refresh_callback=self._do_nothing, app_reference=self)
            self.tool_tabs.append(tool_tab)
            messagebox.showinfo("Erfolg", f"Tool «{name}» hinzugefügt.")
            
        ctk.CTkButton(dlg,text="Hinzufügen",command=save).pack(pady=10)
        
        
    def open_export_dialog(self):
        # Sammle alle Tools, die eine KI-Analyse haben
        exportable = []
        for tab in self.tool_tabs:
            content = tab.ki_text.get("1.0", tk.END).strip()
            if content and content != "":
                exportable.append((tab.tool['name'], content))
    
        if not exportable:
            messagebox.showinfo("Export", "Keine KI-Analysen vorhanden zum Exportieren.")
            return
    
        # Dialog-Fenster
        dlg = ctk.CTkToplevel(self)
        dlg.title("Export auswählen")
        dlg.geometry("400x300")
        dlg.transient(self)     # macht es zum Kind-Fenster
        dlg.grab_set()          # modalisiert es
        dlg.lift()              # bringt's nach vorn
        dlg.focus_force()       # erzwingt Fokus
        vars = []
        for name, _ in exportable:
            var = tk.BooleanVar(value=False)
            chk = ctk.CTkCheckBox(dlg, text=name, variable=var)
            chk.pack(anchor="w", pady=2, padx=10)
            vars.append(var)
            

        # Select All
        def select_all():
            for v in vars: v.set(True)
        ctk.CTkButton(dlg, text="Alle auswählen", command=select_all).pack(pady=(5,0))
        
        # Export-Knopf
        def do_export():
            selected = [c for (_, c), v in zip(exportable, vars) if v.get()]
            if not selected:
                messagebox.showwarning("Export", "Bitte mindestens ein Tool auswählen.", parent=self)
                return
        
            dlg.destroy()
        
            # Loader-Fenster
            loader = ctk.CTkToplevel(self)
            loader.title("KI-Zusammenfassung")
            loader.transient(self); loader.grab_set(); loader.lift()
            ctk.CTkLabel(loader, text="Wird momentan von KI analysiert…").pack(padx=20, pady=10)
            bar = ctk.CTkProgressBar(loader, mode="indeterminate")
            bar.pack(fill="x", padx=20, pady=(0,20))
            bar.start()
        
            def worker():
                try:
                    if len(selected) == 1:
                        result = selected[0]
                    else:
                        joined = "\n\n".join(selected)
                        result = self.tool_tabs[0].generiere_report_export(joined)
                except Exception as e:
                    # Fehler auch im Haupt-Thread anzeigen
                    self.after(0, lambda err=e: (
                        loader.destroy(),
                        messagebox.showerror("Export-Error", f"Fehler bei Zusammenfassung: {err}", parent=self)
                    ))
                    return
        
                # Hier gehen wir zurück in den Haupt-Thread:
                def finish():
                    loader.destroy()
                    self._save_to_file(result)
                self.after(0, finish)

            threading.Thread(target=worker, daemon=True).start()
        ctk.CTkButton(dlg, text="Exportieren", command=do_export).pack(pady=10)
           
# ---------------------------------------------------------------------------
# Hauptprogrammstart
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = Application()
    app.mainloop()
