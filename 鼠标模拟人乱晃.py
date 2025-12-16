import time
import random
import threading
import queue
import tkinter as tk
from tkinter import scrolledtext
import win32gui
import win32con
import win32api
import interception
from interception import beziercurve
from pynput.keyboard import Key, Listener

# --- 全局配置 ---
task_queue = queue.Queue()
exit_event = threading.Event()
pause_event = threading.Event()
pause_event.set()

target_hwnd = None
last_fatigue_time = time.time()

def log(message):
    if 'log_area' in globals():
        log_area.after(0, lambda: log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n"))
        log_area.after(0, lambda: log_area.see(tk.END))

# --- 模拟疲劳状态 ---
def check_fatigue():
    global last_fatigue_time
    now = time.time()
    if now - last_fatigue_time > random.uniform(20, 50):
        delay = random.uniform(1, 3)
        log(f"模拟疲劳：停顿 {delay:.2f} 秒...")
        time.sleep(delay)
        last_fatigue_time = time.time()

# --- 驱动级操作函数 ---
def drive_tap_key(key_str):
    if not target_hwnd or not win32gui.IsWindow(target_hwnd):
        log("错误：请先探测窗口！")
        return True
    pause_event.wait()
    try:
        win32gui.SetForegroundWindow(target_hwnd)
        time.sleep(0.1) 
        interception.press(key_str)
        time.sleep(random.uniform(0.2, 0.4))
    except Exception as e:
        log(f"按键失败: {e}")
    return False

def mouse_chaos_drag():
    """先移至中心，再按住左键拟人乱晃"""
    if not target_hwnd or not win32gui.IsWindow(target_hwnd):
        log("错误：未锁定目标窗口！")
        return
    pause_event.wait()
    try:
        win32gui.SetForegroundWindow(target_hwnd)
        time.sleep(0.2)
        
        log("步骤 1：移至起始点 (500, 500)...")
        interception.move_to(500, 500)
        time.sleep(0.2)

        log("步骤 2：按住左键开始拟人乱晃...")
        with interception.hold_mouse(button="left"):
            for _ in range(random.randint(3, 5)):
                if exit_event.is_set() or not pause_event.is_set(): break
                rand_x = random.randint(300, 700)
                rand_y = random.randint(300, 700)
                log(f"-> 拟人拖拽至: ({rand_x}, {rand_y})")
                interception.move_to(rand_x, rand_y)
                time.sleep(random.uniform(0.1, 0.2))
        
        log("操作结束。")
        check_fatigue()
    except Exception as e:
        log(f"操作失败: {e}")

# --- 窗口探测逻辑 (带分辨率获取) ---
class TargetFinder:
    def __init__(self, label_var):
        self.label_var = label_var
        self.is_tracking = False

    def on_button_down(self, event):
        self.is_tracking = True
        log("探测启动：请按住左键拖动到目标窗口后松开...")
        root.config(cursor="cross")

    def on_button_up(self, event):
        if self.is_tracking:
            self.is_tracking = False
            root.config(cursor="")
            
            # 获取鼠标松开时的坐标和句柄
            x, y = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint((x, y))
            # 锁定最顶级窗口句柄
            hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
            
            global target_hwnd
            target_hwnd = hwnd
            
            # --- 获取并显示分辨率 ---
            try:
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
                title = win32gui.GetWindowText(hwnd)
                
                status_msg = f"目标: {hwnd} | 分辨率: {w}x{h}"
                self.label_var.set(status_msg)
                
                log(f"锁定成功: {title}")
                log(f"当前句柄: {hwnd}")
                log(f"窗口分辨率: {w} 像素(宽) x {h} 像素(高)")
            except Exception as e:
                log(f"获取窗口信息失败: {e}")

# --- 线程管理 ---
def worker():
    try:
        interception.auto_capture_devices(keyboard=True, mouse=True)
        curve_params = beziercurve.BezierCurveParams()
        beziercurve.set_default_params(curve_params)
        log("驱动引擎及贝塞尔平滑引擎初始化成功。")
    except Exception as e:
        log(f"驱动初始化失败: {e}")

    while not exit_event.is_set():
        pause_event.wait()
        try:
            task = task_queue.get(timeout=0.5)
            task()
            task_queue.task_done()
        except queue.Empty: continue

def keyboard_listener():
    def on_press(key):
        try: k = key.char
        except: k = key
        
        if k == Key.esc: exit_event.set(); return False
        elif k == '1': task_queue.put(mouse_chaos_drag)
        elif k == '7': task_queue.put(lambda: drive_tap_key('up'))
        elif k == Key.f8:
            if pause_event.is_set(): pause_event.clear(); log("暂停 (F8)")
            else: pause_event.set(); log("恢复 (F8)")
        elif k == Key.f9:
            with task_queue.mutex: task_queue.queue.clear()
            log("任务队列已清空 (F9)")

    with Listener(on_press=on_press) as l: l.join()

# --- UI 界面 ---
root = tk.Tk()
root.title("AI 拟人控制台 (2025 驱动增强版)")
root.geometry("550x500")

hwnd_var = tk.StringVar(value="状态: 等待探测目标")
tk.Label(root, textvariable=hwnd_var, fg="#0056b3", font=("微软雅黑", 10, "bold")).pack(pady=10)

btn_find = tk.Button(root, text="● 拖动定位目标 (自动获取分辨率)", bg="#ffc107", font=("微软雅黑", 10), height=2, width=30)
btn_find.pack(pady=10)

finder = TargetFinder(hwnd_var)
btn_find.bind("<Button-1>", finder.on_button_down)
btn_find.bind("<ButtonRelease-1>", finder.on_button_up)

log_area = scrolledtext.ScrolledText(root, width=65, height=18, font=("Consolas", 9))
log_area.pack(padx=10, pady=10)

tk.Label(root, text="快捷键: 7 (技能) | 1 (乱晃) | F8 (暂停) | F9 (清空) | ESC (退出)", font=("微软雅黑", 8), fg="gray").pack()

# 启动线程
threading.Thread(target=worker, daemon=True).start()
threading.Thread(target=keyboard_listener, daemon=True).start()

log("系统启动成功，请使用黄色按钮探测 RDP 或游戏窗口。")
root.mainloop()

exit_event.set()
pause_event.set()
