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

# --- 全局状态 ---
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

# --- 功能：模拟疲劳状态 ---
def check_fatigue():
    global last_fatigue_time
    now = time.time()
    if now - last_fatigue_time > random.uniform(20, 50):
        delay = random.uniform(1, 3)
        log(f"模拟疲劳：身体暂歇，停顿 {delay:.2f} 秒...")
        time.sleep(delay)
        last_fatigue_time = time.time()

# --- 核心操作：驱动按键 ---
def drive_tap_key(key_str):
    if not target_hwnd or not win32gui.IsWindow(target_hwnd):
        log("错误：请先探测具体的子窗口区域！")
        return True
    pause_event.wait()
    try:
        # 激活最顶级父窗口，确保子窗口可接收输入
        parent_hwnd = win32gui.GetAncestor(target_hwnd, win32con.GA_ROOT)
        win32gui.SetForegroundWindow(parent_hwnd)
        time.sleep(0.1) 
        
        log(f"驱动执行：向 [{key_str}] 键施压")
        interception.press(key_str)
        time.sleep(random.uniform(0.2, 0.4))
    except Exception as e:
        log(f"按键失败: {e}")
    return False

# --- 功能：模拟人手乱晃 (按键 1) ---
def mouse_chaos_drag():
    if not target_hwnd or not win32gui.IsWindow(target_hwnd):
        log("错误：未锁定窗口！")
        return
    pause_event.wait()
    try:
        parent_hwnd = win32gui.GetAncestor(target_hwnd, win32con.GA_ROOT)
        win32gui.SetForegroundWindow(parent_hwnd)
        time.sleep(0.2)

        log("步骤 1：先移至中心 (500, 500)...")
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
        log(f"乱晃失败: {e}")

# --- 核心：子窗口探测逻辑 ---
class TargetFinder:
    def __init__(self, label_var):
        self.label_var = label_var
        self.is_tracking = False

    def on_button_down(self, event):
        self.is_tracking = True
        log("探测启动：按住左键拖动到【具体子区域】（如打字区）再松开...")
        root.config(cursor="cross")

    def on_button_up(self, event):
        if self.is_tracking:
            self.is_tracking = False
            root.config(cursor="")
            x, y = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint((x, y)) # 获取最底层子窗口
            
            if not hwnd: return
            global target_hwnd
            target_hwnd = hwnd
            
            cls_name = win32gui.GetClassName(hwnd)
            parent_hwnd = win32gui.GetAncestor(hwnd, win32con.GA_ROOT)
            parent_title = win32gui.GetWindowText(parent_hwnd)
            
            try:
                rect = win32gui.GetWindowRect(hwnd)
                w, h = rect[2] - rect[0], rect[3] - rect[1]
                self.label_var.set(f"子窗口: {hwnd} | 类: {cls_name} | 分辨率: {w}x{h}")
                log(f"绑定成功！类名: {cls_name} | 所属: {parent_title} | 区域大小: {w}x{h}")
            except:
                log("获取分辨率失败")

# --- 技能序列定义 ---
def skill_7():
    log("执行技能 7: 组合序列")
    if drive_tap_key('up'): return
    if drive_tap_key('alt'): return
    if drive_tap_key('alt'): return
    if drive_tap_key('s'): return
    check_fatigue()

def skill_8():
    """技能 8: 左闪避 (连按 A)"""
    log("执行技能 8: 向左闪避 (A)")
    with interception.hold_key(key="left"):
        if drive_tap_key('s'): return
        for _ in range(random.randint(1, 3)):
            if drive_tap_key('a'): return
        
    check_fatigue()

def skill_9():
    """技能 9: 右闪避 (连按 D)"""
    log("执行技能 9: 向右闪避 (D)")
    with interception.hold_key(key="right"):
        if drive_tap_key('s'): return
        for _ in range(random.randint(1, 3)):
            if drive_tap_key('a'): return
        
    check_fatigue()

def skill_0():
    log("执行技能 0: 连按 A 三次")
    for _ in range(3):
        if drive_tap_key('a'): return
    check_fatigue()

# --- 线程管理 ---
def worker():
    try:
        interception.auto_capture_devices(keyboard=True, mouse=True)
        curve_params = beziercurve.BezierCurveParams()
        beziercurve.set_default_params(curve_params)
        log("驱动引擎及贝塞尔平滑引擎初始化成功。")
    except Exception as e:
        log(f"驱动启动失败: {e}")

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
        elif k == '7': task_queue.put(skill_7)
        elif k == '8': task_queue.put(skill_8)
        elif k == '9': task_queue.put(skill_9)
        elif k == '0': task_queue.put(skill_0)
        elif k == Key.f8:
            if pause_event.is_set(): pause_event.clear(); log("暂停 (F8)")
            else: pause_event.set(); log("恢复 (F8)")
        elif k == Key.f9:
            with task_queue.mutex: task_queue.queue.clear()
            log("任务队列已清空 (F9)")

    with Listener(on_press=on_press) as l: l.join()

# --- UI 界面 ---
root = tk.Tk()
root.title("2025 驱动级 AI 拟人控制台 (全功能整合版)")
root.geometry("600x520")

hwnd_var = tk.StringVar(value="状态: 等待精准探测")
tk.Label(root, textvariable=hwnd_var, fg="#d9534f", font=("微软雅黑", 9, "bold")).pack(pady=10)

btn_find = tk.Button(root, text="● 拖拽准星到目标【子区域】(如记事本打字区)", bg="#5bc0de", fg="white", font=("微软雅黑", 10, "bold"), height=2, width=45)
btn_find.pack(pady=10)

finder = TargetFinder(hwnd_var)
btn_find.bind("<Button-1>", finder.on_button_down)
btn_find.bind("<ButtonRelease-1>", finder.on_button_up)

log_area = scrolledtext.ScrolledText(root, width=75, height=18, font=("Consolas", 9))
log_area.pack(padx=10, pady=10)

tk.Label(root, text="快捷键: 7,8,9,0 (技能) | 1 (乱晃) | F8 (暂停) | F9 (清空) | ESC (退出)", font=("微软雅黑", 8), fg="gray").pack()

# 线程启动
threading.Thread(target=worker, daemon=True).start()
threading.Thread(target=keyboard_listener, daemon=True).start()

log("系统初始化完成。请先使用蓝色按钮探测具体的子窗口区域。")
root.mainloop()

exit_event.set()
pause_event.set()
