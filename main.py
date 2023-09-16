import os
from collections import OrderedDict
import logging
from math import ceil
import tomllib
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import *

from PIL import ImageTk, ImageDraw, Image, UnidentifiedImageError


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

        self.button_open = Button(self, text='Open', command=self.open_dir, width=16)
        self.button_save = Button(self, text='Save & Close', command=self.save_file, width=16)
        self.button_thumb = Button(self, text='Thumbnail', command=self.save_thumbnail, width=16)
        self.canvas_editor = Canvas(self)
        self.mode_mosaicer = Radiobutton(self, text='Mosaicer', variable=self.str_mode, value='mosaicer')
        self.mode_watermarker = Radiobutton(self, text='Watermarker', variable=self.str_mode, value='watermarker')
        self.label_mouse = Label(self, textvariable=self.str_mouse)
        self.label_status = Label(self, textvariable=self.str_status, borderwidth=1, relief=SUNKEN, anchor=W)
        self.listbox_files = Listbox(self, listvariable=self.str_list)
        # self.combobox_res = Combobox(self)

        self.menu()

        self.scale_img = 1
        self.scale_wm = 1
        self.width_line = 0
        self.start_pt = (0, 0)
        self.draft = []

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

    def open_dir(self):
        if dirs := filedialog.askdirectory():
            for root, dirs, files in os.walk(dirs):
                for fn in files:
                    fp = os.path.join(root, fn)
                    try:
                        img = Image.open(fp)
                    except UnidentifiedImageError:
                        continue
                    self.od_files[fn] = img
            self.str_list.set(' '.join(self.od_files.keys()))
            self.str_status.set(f'Open Dir: Open {len(self.od_files)} images success!')
            self.listbox_files.update()
            self.listbox_files.focus_set()
            self.listbox_files.select_set(0)
            self.listbox_files.event_generate('<<ListboxSelect>>')

    def open_files(self):
        if files := filedialog.askopenfilenames():
            for fp in files:
                try:
                    img = Image.open(fp)
                except UnidentifiedImageError:
                    raise Warning(f'UnidentifiedImageError: {fp}')
                _, fn = os.path.split(fp)
                self.od_files[fn] = img
            self.str_list.set(' '.join(self.od_files.keys()))
            self.str_status.set(f'Open Files: {len(self.od_files)} images success!')
            self.listbox_files.update()
            self.listbox_files.focus_set()
            self.listbox_files.select_set(0)
            self.listbox_files.event_generate('<<ListboxSelect>>')

    def canvas_show(self, event):
        if len(self.od_files) == 0:
            return

        self.od_mosaics, self.od_watermarks = OrderedDict(), OrderedDict()
        img = self.od_files[self.listbox_files.get(self.listbox_files.curselection())]
        canvas_width, canvas_height = int(self.winfo_width() * 0.9), int(self.winfo_height() * 0.9)

        ratio_aspect_ori = img.width / img.height
        ratio_aspect_can = canvas_width / canvas_height

        scale_width = canvas_width / img.width
        scale_height = canvas_height / img.height

        if ratio_aspect_ori > ratio_aspect_can:
            display_size = (canvas_width, int(img.height * scale_width))
            self.scale_wm = int(img.height * scale_width) / 720
            self.scale_img = scale_width
        elif ratio_aspect_ori <= ratio_aspect_can:
            display_size = (int(img.width * scale_height), canvas_height)
            self.scale_wm = int(img.width * scale_height) / 720
            self.scale_img = scale_height
        else:
            display_size = (canvas_width, canvas_height)
            self.scale_wm = canvas_width / 1280
            self.scale_img = scale_width

        self.width_line = ceil(0.01 * max(display_size))

        wm = self.wm.resize((int(self.wm.width * self.scale_wm), int(self.wm.height * self.scale_wm)))
        global wm_dis, img_dis
        wm_dis = ImageTk.PhotoImage(wm)
        img_dis = ImageTk.PhotoImage(img.resize(display_size))

        self.canvas_editor.delete('all')
        self.canvas_editor.config(height=display_size[1], width=display_size[0])
        self.canvas_editor.create_image(0, 0, image=img_dis, anchor=NW)

    def draw_mosaic(self, img):
        draw = ImageDraw.Draw(img)
        for _, line in self.od_mosaics.items():
            line = [i / self.scale_img for i in line]
            draw.line(line, width=ceil(self.width_line / self.scale_img), fill=0)
        return img

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

    # def load_watermark(self):

    def watermark_preview(self, event):
        self.canvas_editor.delete(*self.draft)
        wmp = self.canvas_editor.create_image(event.x, event.y, image=wm_dis, anchor=CENTER)
        self.draft.append(wmp)
        self.canvas_editor.update()

    def watermark_confirm(self, event):
        self.canvas_editor.delete(*self.draft)
        wmp = self.canvas_editor.create_image(event.x, event.y, image=wm_dis, anchor=CENTER)
        self.od_watermarks[wmp] = (int(event.x - wm_dis.width() / 2), int(event.y - wm_dis.height() / 2))
        self.canvas_editor.update()

    def draw_watermark(self, img):
        for pos in self.od_watermarks.values():
            wm = self.wm.resize((int(self.wm.width * self.scale_wm / self.scale_img),
                                 int(self.wm.height * self.scale_wm / self.scale_img)))
            img.paste(wm, (int(pos[0] / self.scale_img), int(pos[1] / self.scale_img)), wm)
        return img

    # def resize(self):
    #     if self.img.width >= self.img.height:  # horizontal
    #         scale = self.res_list[self.combobox_res.get()] / self.img.height
    #         new_height = self.res_list[self.combobox_res.get()]
    #         new_width = int(scale * self.img.width)
    #     else:  # vertical
    #         scale = self.res_list[self.combobox_res.get()] / self.img.width
    #         new_height = int(scale * self.img.height)
    #         new_width = self.res_list[self.combobox_res.get()]
    #     self.img = self.img.resize((new_width, new_height))

    def save_file(self, filename=None):
        curr_sel = self.listbox_files.curselection()
        img = self.od_files.pop(self.listbox_files.get(curr_sel))
        fp, fn = os.path.split(img.filename)
        fp = fp if filename is None else filename
        fn, ext = os.path.splitext(fn)

        if len(self.od_mosaics) != 0:
            img = self.draw_mosaic(img)
            fn += '_m'

        if len(self.od_watermarks) != 0:
            img = self.draw_watermark(img)
            fn += '_w'

        # if self.combobox_res.get() != 'Original':
        #     self.resize()
        #     fn += '_r'

        img.save(os.path.join(fp, fn + ext), quality='keep', optimize=True, progressive=True)

        self.canvas_editor.delete('all')
        self.str_list.set(' '.join(self.od_files.keys()))
        self.listbox_files.update()
        self.listbox_files.select_set(curr_sel)
        self.listbox_files.event_generate('<<ListboxSelect>>')

    def save_thumbnail(self):
        img = self.od_files[self.listbox_files.get(self.listbox_files.curselection())]
        thumb = img.copy()
        fn, ext = os.path.splitext(img.filename)

        if len(self.od_mosaics) != 0:
            thumb = self.draw_mosaic(thumb)
            fn += '_m'

        if len(self.od_watermarks) != 0:
            thumb = self.draw_watermark(thumb)
            fn += '_w'

        fn += '.thumbnail'
        thumb.thumbnail((720, 720))
        thumb.save(fn + ext, optimize=True, progressive=True)

    def save_as_file(self):
        fn = filedialog.asksaveasfilename()
        self.save_file(fn)

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
        file_menu.add_command(label="Open", command=self.open_files)
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
        self.button_open.place(relx=.15, rely=0.01, anchor=N)
        self.button_save.place(relx=.3, rely=0.01, anchor=N)
        self.button_thumb.place(relx=.45, rely=0.01, anchor=N)
        # self.combobox_res.place(relwidth=.1, relheight=.05, relx=.45, rely=0, anchor=N)
        self.mode_mosaicer.place(relwidth=.1, relheight=.05, relx=.6, rely=0, anchor=N)
        self.mode_watermarker.place(relwidth=.1, relheight=.05, relx=.75, rely=0, anchor=N)
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


if __name__ == '__main__':
    window = IlluToolbox()
    window()
