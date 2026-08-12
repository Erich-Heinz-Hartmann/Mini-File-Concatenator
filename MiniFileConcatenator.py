import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

# 文本文件白名单扩展名
TEXT_EXTENSIONS = {
    '.txt', '.py', '.java', '.c', '.cpp', '.h', '.hpp',
    '.js', '.html', '.css', '.xml', '.json', '.yaml', '.yml',
    '.md', '.rst', '.log', '.csv', '.tsv', '.sql', '.sh', '.bat',
    '.gitignore', '.dockerignore', '.ini', '.cfg', '.conf'
}

def is_text_file(filepath):
    """判断文件是否为文本文件"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in TEXT_EXTENSIONS:
        return True
    # 如果后缀不在白名单，尝试用 utf-8 读取一小部分来判断
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except UnicodeDecodeError:
        return False
    except Exception:
        return False

def concat_files(src_dir, output_name, progress_callback=None):
    """
    递归遍历目录，拼接所有文本文件内容
    
    Args:
        src_dir: 源目录路径
        output_name: 输出文件名
        progress_callback: 进度回调函数，接收 (当前计数, 总数)
    
    Returns:
        (成功文件数, 失败文件数)
    """
    all_files = []
    # 收集所有文本文件
    for root, dirs, filenames in os.walk(src_dir):
        # 跳过隐藏目录（以 . 开头）
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in filenames:
            full_path = os.path.join(root, f)
            if is_text_file(full_path):
                all_files.append(full_path)
    
    if not all_files:
        return 0, 0

    all_files.sort()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, output_name)

    success_count = 0
    fail_count = 0

    with open(output_path, 'w', encoding='utf-8') as out:
        total = len(all_files)
        out.write(f"# 文件拼接结果\n# 来源目录: {src_dir}\n# 文件总数: {total}\n")
        out.write("# " + "=" * 60 + "\n\n")

        for idx, filepath in enumerate(all_files):
            relpath = os.path.relpath(filepath, src_dir)
            out.write(f"\n\n# -------- {relpath} --------\n\n")
            try:
                with open(filepath, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    out.write(content)
                success_count += 1
            except Exception as e:
                out.write(f"[读取错误: {e}]\n")
                fail_count += 1

            if progress_callback:
                progress_callback(idx + 1, total)

    return success_count, fail_count


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("文件拼接工具")
        self.root.geometry("580x240")
        self.root.resizable(False, False)

        # ===== 第一行：源目录 =====
        tk.Label(root, text="源目录:", font=("微软雅黑", 10)).grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.dir_var = tk.StringVar()
        tk.Entry(root, textvariable=self.dir_var, width=50, font=("Consolas", 9)).grid(row=0, column=1, padx=5, sticky='we')
        tk.Button(root, text="浏览...", command=self.select_dir, width=8).grid(row=0, column=2, padx=5)

        # ===== 第二行：输出文件名 =====
        tk.Label(root, text="输出文件名:", font=("微软雅黑", 10)).grid(row=1, column=0, padx=10, pady=5, sticky='e')
        self.output_var = tk.StringVar(value="output.txt")
        tk.Entry(root, textvariable=self.output_var, width=50, font=("Consolas", 9)).grid(row=1, column=1, padx=5, sticky='we')
        tk.Label(root, text=".txt 自动补全", fg="gray", font=("微软雅黑", 8)).grid(row=1, column=2, padx=5, sticky='w')

        # ===== 第三行：进度条 =====
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, length=400)
        self.progress_bar.grid(row=2, column=0, columnspan=3, padx=20, pady=5, sticky='we')

        # ===== 第四行：状态标签 =====
        self.status_var = tk.StringVar(value="就绪")
        tk.Label(root, textvariable=self.status_var, fg="blue", font=("微软雅黑", 9)).grid(row=3, column=0, columnspan=3, pady=2)

        # ===== 第五行：操作按钮 =====
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10)

        self.run_btn = tk.Button(btn_frame, text="开始拼接", command=self.run_concat,
                                 bg="#4CAF50", fg="white", font=("微软雅黑", 10), width=12, height=1)
        self.run_btn.pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame, text="清空路径", command=self.clear_fields,
                  bg="#f0f0f0", font=("微软雅黑", 10), width=10, height=1).pack(side=tk.LEFT, padx=10)

        # ===== 设置网格权重 =====
        root.grid_columnconfigure(1, weight=1)

    def select_dir(self):
        path = filedialog.askdirectory(title="选择包含文件的目录")
        if path:
            self.dir_var.set(path)
            self.status_var.set(f"已选: {os.path.basename(path)}")

    def clear_fields(self):
        self.dir_var.set("")
        self.output_var.set("output.txt")
        self.progress_var.set(0)
        self.status_var.set("已清空")

    def run_concat(self):
        src_dir = self.dir_var.get().strip()
        output_name = self.output_var.get().strip()

        if not src_dir:
            messagebox.showwarning("提示", "请先选择源目录")
            return
        if not os.path.exists(src_dir):
            messagebox.showwarning("提示", "源目录不存在")
            return
        if not output_name:
            messagebox.showwarning("提示", "请输入输出文件名")
            return
        if not output_name.endswith(".txt"):
            output_name += ".txt"
            self.output_var.set(output_name)

        # 禁用按钮，防止重复点击
        self.run_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_var.set("正在拼接...")

        # 在后台线程执行，防止界面卡死
        def thread_task():
            try:
                def update_progress(current, total):
                    self.root.after(0, lambda: self.progress_var.set(current / total * 100))
                    self.root.after(0, lambda: self.status_var.set(f"处理中: {current}/{total}"))

                success, fail = concat_files(src_dir, output_name, update_progress)

                self.root.after(0, lambda: self.run_btn.config(state=tk.NORMAL))
                script_dir = os.path.dirname(os.path.abspath(__file__))
                output_path = os.path.join(script_dir, output_name)

                if success == 0 and fail == 0:
                    self.root.after(0, lambda: self.status_var.set("未找到任何文本文件"))
                    self.root.after(0, lambda: messagebox.showinfo("结果", "未找到任何文本文件，请检查目录。"))
                else:
                    self.root.after(0, lambda: self.status_var.set(f"完成: {success} 个成功, {fail} 个失败"))
                    self.root.after(0, lambda: messagebox.showinfo(
                        "完成", f"拼接完成！\n成功: {success} 个文件\n失败: {fail} 个文件\n\n输出路径:\n{output_path}"
                    ))
                self.root.after(0, lambda: self.progress_var.set(0))
            except Exception as e:
                self.root.after(0, lambda: self.run_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.status_var.set("错误"))
                self.root.after(0, lambda: messagebox.showerror("错误", f"拼接失败：{e}"))

        threading.Thread(target=thread_task, daemon=True).start()


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()