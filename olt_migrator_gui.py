"""
CDATA OLT Config Migrator — Tkinter GUI (Upgraded for Advanced Parsing)
Double-clickable on Windows (after Python install).
Designed for ProSolve BD
"""

import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path


# ============================================================
# Advanced Conversion Engine
# ============================================================
DEFAULT_RULES = {
    "ont-lineprofile":   "ont-line-profile",
    "lineprofile-bind":  "line-profile-bind",
    "ont-srvprofile":    "ont-srv-profile",
    "servprofile-bind":  "srv-profile-bind",
}


def escape(s):
    return re.sub(r"[-/\\^$*+?.()|[\]{}]", r"\\\g<0>", s)


def compile_rules(rule_dict):
    return [
        (re.compile(r"\b" + escape(k) + r"\b"), v)
        for k, v in rule_dict.items()
    ]


def migrate_advanced(text, compiled_rules):
    """
    HTML ইঞ্জিনের মতোই নিখুঁতভাবে লাইন-বাই-লাইন অ্যানালাইসিস এবং 
    কমান্ড ইনজেকশন হ্যান্ডেল করার অ্যাডভান্সড ফাংশন।
    """
    lines = text.splitlines()
    output_lines = []
    replacement_count = 0

    for line in lines:
        trimmed = line.strip()
        
        # ১. ont-lineprofile -> ont-line-profile রূপান্তর
        if trimmed.startswith('ont-lineprofile '):
            line = line.replace('ont-lineprofile ', 'ont-line-profile ')
            replacement_count += 1
            output_lines.append(line)
            continue
            
        # ২. line-profile এর ভেতর tcont লাইনের আগে নতুন ২ টি কমান্ড ইনজেকশন
        if trimmed.startswith('tcont 1 dba-profile-id'):
            # আগের লাইনের স্পেস (Indentation) ঠিক রাখার জন্য
            indent_match = re.match(r"^\s*", line)
            indent = indent_match.group(0) if indent_match else ""
            
            output_lines.append(indent + "no gem mapping 1 1")
            output_lines.append(indent + "gem delete 1")
            output_lines.append(line)
            replacement_count += 2
            continue

        # ৩. ont-srvprofile -> ont-srv-profile রূপান্তর
        if trimmed.startswith('ont-srvprofile '):
            line = line.replace('ont-srvprofile ', 'ont-srv-profile ')
            replacement_count += 1
            output_lines.append(line)
            continue

        # ৪. service-port <number> -> service-port autoindex রূপান্তর
        if trimmed.startswith('service-port '):
            # Regex দিয়ে প্রথম সংখ্যার আইডিকে autoindex দিয়ে রিপ্লেস করা
            line = re.sub(r"^(\s*service-port\s+)\d+", r"\1autoindex", line)
            replacement_count += 1
            output_lines.append(line)
            continue

        # ৫. অন্যান্য ডিকশনারি ভিত্তিক জেনেরিক রুলস অ্যাপ্লাই করা
        if compiled_rules:
            modified = False
            for re_pat, replacement in compiled_rules:
                line, n = re_pat.subn(replacement, line)
                if n > 0:
                    replacement_count += n
                    modified = True
            output_lines.append(line)
        else:
            output_lines.append(line)

    return "\n".join(output_lines), replacement_count


# ============================================================
# GUI Layout & Interactions
# ============================================================
class MigratorApp:
    def __init__(self, root):
        self.root = root
        root.title("CDATA OLT Config Migrator (ProSolve BD Custom Engine)")
        root.geometry("1100x680")
        root.configure(bg="#1e1e1e")

        # Rules storage
        self.rules = dict(DEFAULT_RULES)
        self.current_file = None

        self._build_layout()

    def _build_layout(self):
        # ---- Toolbar ----
        bar = tk.Frame(self.root, bg="#252526", pady=8)
        bar.pack(fill="x")

        def btn(text, cmd, color="#0e639c"):
            b = tk.Button(bar, text=text, command=cmd, bg=color, fg="white",
                          activebackground="#1177bb", relief="flat",
                          padx=14, pady=6, cursor="hand2", font=("Segoe UI", 9, "bold"))
            b.pack(side="left", padx=4)

        btn("📂 Open .txt",          self.open_file)
        btn("⚡ Convert Config",     self.do_convert, "#f59e0b") # বাটনের কালার HTML টুলের মতো থিম ম্যাচ করা হয়েছে
        btn("💾 Save Output",        self.save_output, "#0e639c")
        btn("📋 Copy Output",        self.copy_output, "#10b981")
        btn("🗑  Clear All",          self.clear_all, "#a1260d")
        tk.Label(bar, text="    Rules: ", bg="#252526", fg="#9cdcfe",
                 font=("Segoe UI", 9)).pack(side="left", padx=(20, 0))
        btn("✏ Edit Rules",        self.edit_rules, "#6a9955")
        btn("↺ Reset Rules",       self.reset_rules, "#a1260d")

        # ---- Main paned area ----
        body = tk.PanedWindow(self.root, orient="horizontal", bg="#1e1e1e")
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # Left: input
        left = tk.Frame(body, bg="#1e1e1e")
        tk.Label(left, text="📥 [1] Paste Old Version OLT Config Here", fg="#38bdf8", bg="#1e1e1e",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self.txt_in = scrolledtext.ScrolledText(left, bg="#020617", fg="#ffffff",
                                                insertbackground="white",
                                                font=("Consolas", 11),
                                                undo=True, wrap="none")
        self.txt_in.pack(fill="both", expand=True)
        body.add(left, minsize=400)

        # Right: output
        right = tk.Frame(body, bg="#1e1e1e")
        tk.Label(right, text="📤 [2] Generated New Version OLT Config", fg="#10b981",
                 bg="#1e1e1e", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        self.txt_out = scrolledtext.ScrolledText(right, bg="#020617", fg="#10b981",
                                                 font=("Consolas", 11),
                                                 wrap="none", state="normal")
        self.txt_out.pack(fill="both", expand=True)
        body.add(right, minsize=400)

        # ---- Status bar ----
        self.status = tk.Label(self.root, text="Ready. Designed for Network Operations — ProSolve BD", anchor="w",
                               bg="#007acc", fg="white", padx=10, pady=4,
                               font=("Segoe UI", 9))
        self.status.pack(fill="x", side="bottom")

    # ---------------- Actions ----------------
    def open_file(self):
        p = filedialog.askopenfilename(
            title="Open old OLT config",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not p: return
        try:
            data = Path(p).read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        self.txt_in.delete("1.0", "end")
        self.txt_in.insert("1.0", data)
        self.current_file = p
        self.set_status(f"📂 Loaded: {p}")

    def do_convert(self):
        text = self.txt_in.get("1.0", "end-1c")
        if not text.strip():
            messagebox.showwarning("Empty Input", "Please paste or open the old configuration first.")
            return
        compiled = compile_rules(self.rules)
        
        # আপগ্রেডেড অ্যাডভান্সড মাইগ্রেশন ইঞ্জিন কল করা হলো
        out, n = migrate_advanced(text, compiled)
        
        self.txt_out.delete("1.0", "end")
        self.txt_out.insert("1.0", out)
        self.set_status(f"✅ Conversion successful! Processed/Optimized {n} configuration points.")

    def save_output(self):
        out = self.txt_out.get("1.0", "end-1c")
        if not out.strip():
            messagebox.showwarning("Empty", "Nothing to save. Generate the config first."); return
        default = "new_olt_config.txt"
        if self.current_file:
            default = str(Path(self.current_file).with_name(
                Path(self.current_file).stem + "_NEW.txt"))
        p = filedialog.asksaveasfilename(
            title="Save new config",
            defaultextension=".txt",
            initialfile=Path(default).name,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not p: return
        Path(p).write_text(out, encoding="utf-8")
        self.set_status(f"💾 Saved: {p}")

    def copy_output(self):
        out = self.txt_out.get("1.0", "end-1c")
        if not out.strip(): return
        self.root.clipboard_clear()
        self.root.clipboard_append(out)
        self.set_status("📋 New configuration copied to clipboard!")

    def clear_all(self):
        self.txt_in.delete("1.0", "end")
        self.txt_out.delete("1.0", "end")
        self.current_file = None
        self.set_status("Cleared.")

    # ---------------- Rules editor ----------------
    def edit_rules(self):
        win = tk.Toplevel(self.root)
        win.title("Edit conversion rules")
        win.geometry("640x500")
        win.configure(bg="#1e1e1e")

        tk.Label(win, text="Each line:  old_word  =  new_word",
                 fg="#9cdcfe", bg="#1e1e1e",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 4))

        tk.Label(win, text="Word-boundary match. Comments start with '#'.",
                 fg="#808080", bg="#1e1e1e", font=("Segoe UI", 9)).pack(anchor="w", padx=10)

        txt = scrolledtext.ScrolledText(win, bg="#0e0e0e", fg="#d4d4d4",
                                        insertbackground="white",
                                        font=("Consolas", 11), undo=True)
        txt.pack(fill="both", expand=True, padx=10, pady=8)

        body = "\n".join(f"{k} = {v}" for k, v in self.rules.items())
        txt.insert("1.0", body)

        def save_and_close():
            new_rules = {}
            for line in txt.get("1.0", "end-1c").splitlines():
                line = line.strip()
                if not line or line.startswith("#"): continue
                if "=" not in line:
                    messagebox.showwarning("Bad rule", f"Skipping: {line!r}")
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if k and v:
                    new_rules[k] = v
            if not new_rules:
                messagebox.showwarning("No rules", "At least one rule required.")
                return
            self.rules = new_rules
            win.destroy()
            self.set_status(f"✏ Rules updated: {len(new_rules)} rule(s) loaded.")

        bb = tk.Frame(win, bg="#1e1e1e")
        bb.pack(fill="x", pady=(0, 8))
        tk.Button(bb, text="💾 Save Rules", command=save_and_close,
                  bg="#0e639c", fg="white", relief="flat",
                  padx=14, pady=6, font=("Segoe UI", 9, "bold")).pack(side="left", padx=10)
        tk.Button(bb, text="Cancel", command=win.destroy,
                  bg="#6a9955", fg="white", relief="flat",
                  padx=14, pady=6, font=("Segoe UI", 9, "bold")).pack(side="left")

    def reset_rules(self):
        self.rules = dict(DEFAULT_RULES)
        self.set_status(f"↺ Rules reset to defaults ({len(self.rules)} rules).")

    def set_status(self, msg):
        self.status.config(text=msg)


def main():
    root = tk.Tk()
    app = MigratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()