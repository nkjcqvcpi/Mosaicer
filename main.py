from tkinter import *
from tkinter import messagebox, filedialog
from tkinter.ttk import *
from collections import OrderedDict

from PIL import ImageTk, ImageDraw, Image

from math import ceil


VERSION = '0.0.1'
GR = 0.618


class Mosaicer(Tk):
    def __init__(self):
        super().__init__()
        self.res = (self.winfo_screenwidth(), self.winfo_screenheight())
        self.o = self.res
        self.scale = 1
        self.linewidth = int(max(self.res) * 0.01)
        self.s_size = (int(self.winfo_screenwidth() * 0.8), int(self.winfo_screenheight() * 0.8))
        self.rt = []
        self.draft = []
        self.mosaics = OrderedDict()
        self.menu()
        self.set_win()
        self.mainloop()

    def open_file(self):
        self.filename = filedialog.askopenfilename()
        self.img = Image.open(self.filename)
        self.o = self.img.size
        if self.o[0] >= self.o[1]:
            s_width = min(self.s_size[0], self.o[0])
            self.scale = s_width / self.o[0]
            display_size = (s_width, int(self.scale * self.o[1]))
        else:
            s_height = min(self.s_size[1], self.o[1])
            self.scale = s_height / self.o[1]
            display_size = (int(self.scale * self.o[0]), s_height)

        self.linewidth = ceil(0.01 * max(display_size))

        img = self.img.resize(display_size)

        global photo
        photo = ImageTk.PhotoImage(img)
        self.button.pack_forget()
        self.save_button.pack(anchor='center')
        self.geometry(f'{display_size[0]}x{display_size[1] + 10}+{int((self.res[0] - display_size[0]) / 2)}+{int((self.res[1] - display_size[1]) / 2)}')
        self.c_picture.config(height=display_size[1], width=display_size[0])
        self.c_picture.pack(anchor='center')
        self.c_picture.delete('all')
        self.c_picture.create_image(0, 0, image=photo, anchor=NW)

    def render(self):
        draw = ImageDraw.Draw(self.img)
        for _, line in self.mosaics.items():
            line = [i / self.scale for i in line]
            draw.line(line, width=ceil(self.linewidth / self.scale), fill=0)

    def save_file(self):
        fn, pf = self.filename.split('.')
        self.render()
        self.img.save(fn + '_mosaic.' + pf)
        self.reset()

    def save_as_file(self):
        f = filedialog.asksaveasfilename()
        # TODO

    def undo():
        pass
        # TODO

    def reset(self):
        w = int(self.res[0] * GR)
        h = int(self.res[1] * GR)
        self.geometry(f'{w}x{h}+{int((self.res[0] - w) / 2)}+{int((self.res[1] - h) / 2)}')
        self.button.pack(anchor='center')
        self.save_button.pack_forget()
        self.c_picture.pack_forget()

    def menu(self):
        def about():
            messagebox.showinfo("About", "Version：" + VERSION)

        m_main = Menu(self)

        app_menu = Menu(m_main, name='apple')
        app_menu.add_command(label='About', command=about)
        m_main.add_cascade(menu=app_menu)
    
        filemenu = Menu(m_main, tearoff=0)
        filemenu.add_command(label="Open", command=self.open_file)
        filemenu.add_command(label="Save", command=self.save_file)
        filemenu.add_command(label="Save as...", command=self.save_as_file)
        m_main.add_cascade(label="File", menu=filemenu)

        editmenu = Menu(m_main, tearoff=0)
        editmenu.add_command(label="Undo", command=self.undo)
        m_main.add_cascade(label="Edit", menu=editmenu)

        self.config(menu=m_main)

    def MousePress(self, event):
        self.start_pt = (event.x, event.y)

    def MouseRelease(self, event):
        self.c_picture.delete(*self.draft)
        lid = self.c_picture.create_line(*self.start_pt, event.x, event.y, width=self.linewidth)
        self.mosaics[lid] = (self.start_pt[0], self.start_pt[1], event.x, event.y)
        self.c_picture.update()

    def MouseDrag(self, event):
        self.c_picture.delete(*self.draft)
        lid = self.c_picture.create_line(*self.start_pt, event.x, event.y, width=self.linewidth, dash=self.linewidth)
        self.draft.append(lid)
        self.c_picture.update()

    # def MouseClick(self, event):
    #     self.rt.append((event.x, event.y))
    #     self.c_picture.create_oval(event.x, event.y, width=self.w)
    #     if len(self.rt) == 4:
    #         self.c_picture.create_polygon(self.rt, fill='pink')
    #         self.rt = []
    #     self.c_picture.update()

    def set_win(self):
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)
        self.title("Mosaicer")
        self.resizable(True, True)
        self.button = Button(self, text='Open', command=self.open_file)
        self.save_button = Button(self, text='Save', command=self.save_file)
        self.c_picture = Canvas(self, borderwidth=0, relief="solid")
        # self.c_picture.bind('<Button-1>', self.MouseClick)
        self.c_picture.bind('<ButtonPress-1>', self.MousePress)
        self.c_picture.bind('<ButtonRelease-1>', self.MouseRelease)
        self.c_picture.bind('<B1-Motion>', self.MouseDrag)
        self.reset()

if __name__ == '__main__':
    Mosaicer()
