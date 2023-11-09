import os
import tomllib
from collections import OrderedDict
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import *

from PIL import ImageTk, UnidentifiedImageError, ImageOps

from lib import *

THUMBNAIL_SIZE = (576, 576)

global img_dis, wm_dis


class IlluToolbox(Tk):
    with open("config.toml", "rb") as f:
        cf = tomllib.load(f)

    def __init__(self):
        super().__init__()
        self.res = (self.winfo_screenwidth(), self.winfo_screenheight())

        self.str_mode = StringVar()
        self.str_mouse = StringVar()
        self.str_list = StringVar()
        self.str_status = StringVar()

        self.od_mosaics = OrderedDict()
        self.od_files = OrderedDict()
        self.od_watermarks = OrderedDict()

        self.wm = Image.open(self.cf['WM'])
        if self.wm.mode == 'RGBA':
            r, g, b, a = self.wm.split()
            r2, g2, b2 = ImageOps.invert(Image.merge('RGB', (r, g, b))).split()
            self.wm_i = Image.merge('RGBA', (r2, g2, b2, a))
        else:
            self.wm_i = ImageOps.invert(self.wm)

        self.button_open = Button(self, text='Open', command=lambda: self.open_imgs("Dirs"), width=8)
        self.button_save = Button(self, text='Save & Close', command=self.save_file, width=8)
        self.button_thumb = Button(self, text='Thumbnail', command=lambda: self.save_file(thumbnail=True), width=8)
        self.button_blur = Button(self, text='Blur', command=lambda: self.save_file(blur=True, thumbnail=True), width=8)
        self.canvas_editor = Canvas(self)
        self.mode_mosaicer = Radiobutton(self, text='Mosaicer', variable=self.str_mode, value='mosaicer')
        self.mode_watermarker = Radiobutton(self, text='Watermarker', variable=self.str_mode, value='watermarker')
        self.label_mouse = Label(self, textvariable=self.str_mouse)
        self.label_status = Label(self, textvariable=self.str_status, borderwidth=1, relief=SUNKEN, anchor=W)
        self.listbox_files = Listbox(self, listvariable=self.str_list, selectmode='single')
        self.combobox_res = Combobox(self)

        self.menu()

        self.scale_img, self.scale_wm, self.width_line = 1, 1, 0
        self.start_pt = (0, 0)
        self.draft, self.wms = [],  []
        self.invert = False
        self.display_size = (0, 0)

        # self.combobox_res['value'] = ('Original', '720P', '1080P', '4K', '8K')
        self.res_list = {'720P': 720, '1080P': 1080, '4K': 2160, '8K': 4320}

        self.win_size = (self.winfo_width(), self.winfo_height())

    def __call__(self, *args, **kwargs):
        self.str_mode.set('mosaicer')
        # self.combobox_res.current(0)
        self.str_status.set('Done')
        self.widget_place()
        self.widget_bind()
        self.set_win()
        self.mainloop()

    def open_imgs(self, mode):
        if mode == 'Dirs' and (dirs := filedialog.askdirectory()):
            for root, dirs, files in os.walk(dirs):
                for fn in files:
                    fp = os.path.join(root, fn)
                    try:
                        img = Image.open(fp)
                    except UnidentifiedImageError:
                        continue
                    self.od_files[fn] = img
        elif mode == 'Files' and (files := filedialog.askopenfilenames()):
            for fp in files:
                try:
                    img = Image.open(fp)
                except UnidentifiedImageError:
                    raise Warning(f'UnidentifiedImageError: {fp}')
                _, fn = os.path.split(fp)
                self.od_files[fn] = img
        else:
            return
        self.str_list.set(' '.join(self.od_files.keys()))
        self.str_status.set(f'Open {mode}: Open {len(self.od_files)} images success!')
        self.listbox_files.update()
        self.listbox_files.focus_set()
        self.listbox_files.select_set(0)
        self.listbox_files.event_generate('<<ListboxSelect>>')

    def canvas_show(self, *args):
        global img_dis
        if len(self.od_files) == 0:
            return

        self.od_mosaics, self.od_watermarks = OrderedDict(), OrderedDict()
        img = self.od_files[self.listbox_files.get(self.listbox_files.curselection())]

        self.display_size, self.scale_img, self.width_line = calc_scale(img, self.winfo_width(), self.winfo_height())

        img_dis = ImageTk.PhotoImage(img.resize(self.display_size))
        self.load_watermark(init=True)
        self.canvas_editor.delete('all')
        self.canvas_editor.config(height=self.display_size[1], width=self.display_size[0])
        self.canvas_editor.create_image(0, 0, image=img_dis, anchor=NW)
        self.str_status.set(f'Show File: {img.filename} success!')

    def mosaic_confirm(self, event):
        self.canvas_editor.delete(*self.draft)
        lid = self.canvas_editor.create_line(*self.start_pt, event.x, event.y, width=self.width_line)
        self.od_mosaics[lid] = (self.start_pt[0], self.start_pt[1], event.x, event.y)
        self.canvas_editor.update()

    def mosaic_preview(self, event):
        self.canvas_editor.delete(*self.draft)
        lid = self.canvas_editor.create_line(*self.start_pt, event.x, event.y,
                                             width=self.width_line, dash=[self.width_line])
        self.draft.append(lid)
        self.canvas_editor.update()

    def load_watermark(self, init=False):
        global wm_dis
        if init:
            wm_width = int(0.618 * min(self.display_size))
            self.scale_wm = wm_width / self.wm.width
            wm_di = self.wm.resize((wm_width, int(self.scale_wm * self.wm.height)))
        elif self.invert:
            wm_di = self.wm_i.resize((int(self.scale_wm * self.wm_i.width), int(self.scale_wm * self.wm_i.height)))
        else:
            wm_di = self.wm.resize((int(self.scale_wm * self.wm.width), int(self.scale_wm * self.wm.height)))
        wm_dis = ImageTk.PhotoImage(wm_di)

    def watermark_preview(self, event):
        self.canvas_editor.delete(*self.draft)
        if event.type == EventType.MouseWheel:
            self.scale_wm -= event.delta / 10
            self.scale_wm = max(0.01, self.scale_wm)
        elif event.type == EventType.Key:
            self.invert = not self.invert
        self.load_watermark()
        wmp = self.canvas_editor.create_image(event.x, event.y, image=wm_dis, anchor=CENTER)
        self.draft.append(wmp)
        self.canvas_editor.update()

    def watermark_confirm(self, event):
        self.wms.append(wm_dis)
        wmp = self.canvas_editor.create_image(event.x, event.y, image=self.wms[-1], anchor=CENTER)
        self.od_watermarks[wmp] = (int(event.x - wm_dis.width() / 2), int(event.y - wm_dis.height() / 2),
                                   self.scale_wm, self.invert)
        self.canvas_editor.update()

    def save_file(self, close=True, filename=None, thumbnail=False, blur=False):
        curr_sel = self.listbox_files.curselection()
        if close:
            img = self.od_files.pop(self.listbox_files.get(curr_sel))
        else:
            img = self.od_files[self.listbox_files.get(curr_sel)].copy()
        fp, fn = os.path.split(img.filename)
        fp = fp if filename is None else filename
        fn, ext = os.path.splitext(fn)

        img, fn = render(img, fn, mosaics=(self.width_line, self.scale_img, self.od_mosaics), blur=blur,
                         watermarks=(self.wm, self.wm_i, self.scale_img, self.od_watermarks), thumbnail=thumbnail)

        img.save(os.path.join(fp, fn + ext), optimize=True, progressive=True)

        self.str_status.set(f'Save File: {fn + ext} success!')
        if close:
            self.canvas_editor.delete('all')
            self.str_list.set(' '.join(self.od_files.keys()))
            self.listbox_files.update()
            self.listbox_files.select_set(curr_sel)
            self.listbox_files.event_generate('<<ListboxSelect>>')

    def save_as_file(self):
        fn = filedialog.asksaveasfilename()
        self.save_file(filename=fn)

    def undo(self):
        pass
        # TODO

    def menu(self):
        def about():
            messagebox.showinfo("About", "Version：" + self.cf['VERSION'])

        m_main = Menu(self)

        app_menu = Menu(m_main, name='apple')
        app_menu.add_command(label='About', command=about)
        m_main.add_cascade(menu=app_menu)

        file_menu = Menu(m_main, tearoff=0)
        file_menu.add_command(label="Open", command=lambda: self.open_imgs('Files'))
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save as...", command=self.save_as_file)
        m_main.add_cascade(label="File", menu=file_menu)

        editmenu = Menu(m_main, tearoff=0)
        editmenu.add_command(label="Undo", command=self.undo)
        m_main.add_cascade(label="Edit", menu=editmenu)

        self.config(menu=m_main)

    def mouse_press(self, event):
        self.start_pt = (event.x, event.y)
        if self.str_mode.get() == 'watermarker':
            self.watermark_confirm(event)

    def mouse_position(self, event):
        self.str_mouse.set(f'x: {event.x} y: {event.y}')
        if self.str_mode.get() == 'watermarker':
            self.watermark_preview(event)

    def set_win(self):
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)
        self.geometry(f'{self.res[0]}x{self.res[1]}+0+0')
        self.title("illuToolbox")
        self.resizable(True, True)

    def widget_place(self):
        self.button_open.place(relx=.1, rely=0.01, anchor=N)
        self.button_save.place(relx=.25, rely=0.01, anchor=N)
        self.button_thumb.place(relx=.4, rely=0.01, anchor=N)
        self.button_blur.place(relx=.55, rely=0.01, anchor=N)
        # self.combobox_res.place(relwidth=.1, relheight=.05, relx=.45, rely=0, anchor=N)
        self.mode_mosaicer.place(relwidth=.1, relheight=.05, relx=.7, rely=0, anchor=N)
        self.mode_watermarker.place(relwidth=.1, relheight=.05, relx=.8, rely=0, anchor=N)
        self.label_mouse.place(relwidth=.1, relheight=.05, relx=.9, rely=0, anchor=N)
        self.label_status.place(relwidth=1, relheight=.05, relx=0, rely=.95, anchor=NW)
        self.listbox_files.place(relwidth=.1, relheight=.9, relx=.9, rely=.05, anchor=NW)
        self.canvas_editor.place(relx=.45, rely=.5, anchor=CENTER)

    def widget_bind(self):
        self.canvas_editor.bind('<ButtonPress-1>', self.mouse_press)
        self.canvas_editor.bind('<ButtonRelease-1>',
                                lambda e: self.mosaic_confirm(e) if self.str_mode.get() == 'mosaicer' else None)
        self.canvas_editor.bind('<B1-Motion>',
                                lambda e: self.mosaic_preview(e) if self.str_mode.get() == 'mosaicer' else None)
        self.canvas_editor.bind('<Motion>', self.mouse_position)
        self.listbox_files.bind("<<ListboxSelect>>", self.canvas_show)
        self.canvas_editor.bind('<Configure>', self.canvas_show)
        self.canvas_editor.bind('<MouseWheel>', self.watermark_preview)
        self.bind('<Tab>', self.watermark_preview)


if __name__ == '__main__':
    window = IlluToolbox()
    window()
