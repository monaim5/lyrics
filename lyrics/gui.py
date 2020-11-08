import json
import time
import tkinter as tk
import pygame


def play_sound(path):
    pygame.mixer.init()
    pygame.mixer.music.load(path.__str__())
    pygame.mixer.music.play()


def stop_sound():
    pygame.mixer.music.stop()


def pause_sound():
    pygame.mixer.music.pause()


def unpause_sound():
    pygame.mixer.music.unpause()


def generate_separator(master, row=1, column=1, rowspan=1, colspan=1):
    tk.Frame(master, width=1, background='black', relief='sunken') \
        .grid(row=row, column=column, rowspan=rowspan, columnspan=colspan, sticky='nesw')


class Button(tk.Button):
    def __init__(self, master, text, command=None):
        super().__init__(master, text=text, command=command, width=12,  pady=4, padx=2)


class MappingConsole(tk.Frame):
    def __init__(self, parent, song):
        tk.Frame.__init__(self, parent)
        with open(song.lyrics_path, 'r', encoding='utf-8') as f:
            self.lyrics = json.load(f)
        self.lyrics_map_path = song.lyrics_map_path
        self.line_index = 0
        self.start_time = 0
        self.space_pressed = False
        self.backspace_pressed = False
        self.generate_lyrics = []
        self.text = tk.Text(self, width=100)
        self.text.tag_config('txt-center', justify='center')
        self.text.tag_config('next_line', foreground='purple')  # priorite 3
        self.text.tag_config('current_line', foreground='red')  # priorite 2
        self.text.tag_config('treated_line', foreground='blue')  # priorite 1
        self.text.config(state='normal')
        self.text.insert(tk.END, self.get_lyrics_text(), 'txt-center')
        self.text.config(state='disabled')
        self.text.pack()

        play_sound(song.path)
        time.perf_counter()
        self.text.tag_add('next_line', '%s.0' % (self.line_index + 1), '%s.0-1c' % (self.line_index + 2))
        pygame.mixer.music.get_pos() / 1000

    def get_lyrics_text(self):
        text = ''
        for line in self.lyrics:
            text += f'{line["text_en"]}  |  {line["text_ar"]}\n'
        return text

    def on_space_press(self, event):
        if not self.space_pressed:
            try:
                self.text.tag_add('current_line', '%s.0' % (self.line_index + 1), '%s.0-1c' % (self.line_index + 2))
                line = self.lyrics[self.line_index]
                line_inf = {'line': self.line_index,
                            'text_en': line['text_en'],
                            'text_ar': line['text_ar'],
                            'start': round(pygame.mixer.music.get_pos() / 1000, 2)}
                self.generate_lyrics.append(line_inf)
                self.line_index += 1
                self.space_pressed = True

            except IndexError:
                with open(self.lyrics_map_path, 'w+', encoding='utf-8') as f:
                    json.dump(self.generate_lyrics, f, ensure_ascii=False, sort_keys=True, indent=2)
                    print('writen')
                stop_sound()
                self.master.destroy()

    def on_space_release(self, event):
        if self.space_pressed:
            self.text.tag_remove('current_line', '%s.0' % self.line_index, '%s.0-1c' % (self.line_index + 1))
            self.text.tag_add('treated_line', '%s.0' % self.line_index, '%s.0-1c' % (self.line_index + 1))
            self.text.tag_add('next_line', '%s.0' % (self.line_index + 1), '%s.0-1c' % (self.line_index + 2))
            self.generate_lyrics[-1]['end'] = round(pygame.mixer.music.get_pos() / 1000, 2)
            self.space_pressed = False

    def on_backspace_press(self, event):
        if not self.backspace_pressed:
            try:
                del self.generate_lyrics[-1]
                self.text.tag_remove('treated_line', '%s.0' % self.line_index, '%s.0-1c' % (self.line_index + 1))
                self.text.tag_remove('next_line', '%s.0' % (self.line_index + 1), '%s.0-1c' % (self.line_index + 2))
                self.line_index -= 1
                self.backspace_pressed = True
            except IndexError:
                pass

    def on_backspace_release(self, event):
        if self.backspace_pressed:
            self.backspace_pressed = False


class AdjustmentConsole(tk.Frame):
    def __init__(self, parent, song):
        tk.Frame.__init__(self, parent)
        self.lyrics_map_path = song.lyrics_map_path
        self.song_path = song.path
        self.lyrics_map = None
        self.set_lyrics_map()
        self.current_index = 0
        self.added_time = 0
        self.paused: bool = False
        self.main_frame = tk.Frame(self, width=1000, height=100, padx=10, pady=10)
        self.main_frame.grid_propagate(False)
        self.actions = tk.Frame(self, width=1000, height=50, padx=10, pady=10)
        self.actions.grid_propagate(False)
        self.summary = tk.Frame(self, width=200, padx=10, pady=10)
        self.summary.grid_propagate(False)

        self.main_frame.grid(row=0, column=0)
        generate_separator(self, row=1, column=0)
        self.actions.grid(row=2, column=0)
        generate_separator(self, row=0, column=1, rowspan=3)
        self.summary.grid(row=0, column=2, rowspan=3, sticky='ns')

        for i in range(3):
            self.main_frame.rowconfigure(i, weight=1)
        for i in range(18):
            self.main_frame.columnconfigure(i, weight=1)
        for i in range(7):
            self.actions.columnconfigure(i, weight=1)

        self.current_line = tk.StringVar()
        self.current_line_label = tk.Label(self.main_frame, textvariable=self.current_line)
        self.current_line_label.configure(font=('arial', 16, "normal"), fg='blue')

        self.next_line_btn = Button(self.main_frame, text='Next line', command=self.next_line)
        self.previous_line_btn = Button(self.main_frame, text='Previous line', command=self.previous_line)

        self.start_time = tk.DoubleVar()
        self.start_time.trace_add("write", self.update_start_time)

        self.end_time = tk.DoubleVar()
        self.end_time.trace_add("write", self.update_end_time)

        self.start_time_entry = tk.Entry(self.main_frame, textvariable=self.start_time, width=7)
        self.add_start_1 = tk.Button(self.main_frame, text='>', command=lambda: self.add_to_start_time(0.01))
        self.add_start_10 = tk.Button(self.main_frame, text='>>', command=lambda: self.add_to_start_time(0.1))
        self.sub_start_1 = tk.Button(self.main_frame, text='<', command=lambda: self.add_to_start_time(-0.01))
        self.sub_start_10 = tk.Button(self.main_frame, text='<<', command=lambda: self.add_to_start_time(-0.1))

        self.end_time_entry = tk.Entry(self.main_frame, textvariable=self.end_time, width=7)
        self.add_end_1 = tk.Button(self.main_frame, text='>', command=lambda: self.add_to_end_time(0.01))
        self.add_end_10 = tk.Button(self.main_frame, text='>>', command=lambda: self.add_to_end_time(0.1))
        self.sub_end_1 = tk.Button(self.main_frame, text='<', command=lambda: self.add_to_end_time(-0.01))
        self.sub_end_10 = tk.Button(self.main_frame, text='<<', command=lambda: self.add_to_end_time(-0.1))

        self.play_pause_btn = Button(self.actions, text='Play/Pause', command=self.play_pause)
        self.repeat = Button(self.actions, text='Repeat', command=self.repeat_line)
        self.save = Button(self.actions, text='Save', command=self.save)
        self.quit = Button(self.actions, text='Quit', command=self.quit)

        self.previous_line_btn.grid(row=0, column=1, columnspan=2)
        self.current_line_label.grid(row=0, column=4, columnspan=10, rowspan=2)
        self.next_line_btn.grid(row=0, column=15, columnspan=2)

        self.sub_start_1.grid(row=2, column=2)
        self.sub_start_10.grid(row=2, column=3)
        self.start_time_entry.grid(row=2, column=4, columnspan=2)
        self.add_start_1.grid(row=2, column=6)
        self.add_start_10.grid(row=2, column=7)

        self.sub_end_1.grid(row=2, column=10)
        self.sub_end_10.grid(row=2, column=11)
        self.end_time_entry.grid(row=2, column=12, columnspan=2)
        self.add_end_1.grid(row=2, column=14)
        self.add_end_10.grid(row=2, column=15)

        self.play_pause_btn.grid(row=0, column=1)
        self.repeat.grid(row=0, column=2)
        self.save.grid(row=0, column=3)
        self.quit.grid(row=0, column=4)

        self.bind('<Left>', self.on_left_arrow_press)
        self.bind('<Right>', self.on_right_arrow_press)
        self.bind('<space>', self.on_space_press)
        self.bind('<Control_L>', lambda event: self.repeat_line())
        self.start_time_entry.bind('<space>', self.on_space_press)
        self.start_time_entry.bind('<space>', self.on_space_press)

        play_sound(self.song_path)
        self.update_current_line()
        self.sync_bold_text()

    def set_lyrics_map(self):
        with open(self.lyrics_map_path, 'r', encoding='utf-8') as f:
            self.lyrics_map = json.load(f)

    def set_sound_pos(self, pos):
        pygame.mixer.music.play(start=pos)
        self.added_time = pos

    def get_sound_pos(self):
        return pygame.mixer.music.get_pos() / 1000 + self.added_time

    def update_start_time(self, a, b, c):
        self.lyrics_map[self.current_index]['start'] = self.start_time.get()

    def update_end_time(self, a, b, c):
        self.lyrics_map[self.current_index]['end'] = self.end_time.get()

    def update_current_line(self):
        self.current_line.set(self.lyrics_map[self.current_index]['text_en'])
        self.start_time.set(self.lyrics_map[self.current_index]['start'])
        self.end_time.set(self.lyrics_map[self.current_index]['end'])
        self.set_sound_pos(self.lyrics_map[self.current_index]['start'] - 1)
        self.focus()

    def sync_bold_text(self):
        if self.get_sound_pos() > self.end_time.get():
            self.next_line()
        if self.start_time.get() < self.get_sound_pos() < self.end_time.get():
            self.current_line_label.configure(font=('arial', 16, "bold"), fg='red')
        else:
            self.current_line_label.configure(font=('arial', 16, "normal"), fg='blue')
        self.after(1, self.sync_bold_text)

    def next_line(self):
        try:
            self.current_index += 1
            self.update_current_line()
        except IndexError as e:
            self.current_index -= 1
            print('you reached the last line')

    def previous_line(self):
        try:
            self.current_index -= 1
            self.update_current_line()
        except IndexError as e:
            self.current_index += 1
            print('no more lines under line 1')

    def add_to_start_time(self, t):
        self.start_time.set(self.start_time.get() + t)
        self.lyrics_map[self.current_index]['start'] = self.start_time.get()

    def add_to_end_time(self, t):
        self.end_time.set(self.end_time.get() + t)
        self.lyrics_map[self.current_index]['end'] = self.end_time.get()

    def play_pause(self):
        if self.paused:
            unpause_sound()
        else:
            pause_sound()
        self.paused = not self.paused

    def repeat_line(self):
        self.set_sound_pos(self.lyrics_map[self.current_index]['start'] - 1)

    def quit(self):
        self.master.destroy()

    def save(self):
        with open(self.lyrics_map_path, 'w', encoding='utf-8') as f:
            json.dump(self.lyrics_map, f, ensure_ascii=False, sort_keys=True, indent=2)

    def on_space_press(self, event):
        self.play_pause()

    def on_left_arrow_press(self, event):
        self.previous_line()

    def on_right_arrow_press(self, event):
        self.next_line()
