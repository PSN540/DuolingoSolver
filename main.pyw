import os.path
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image
import sys
import time
import threading
import json
import re
from functools import partial
import solve
from win32comext.shell import shell, shellcon
import shutil


def start_solving():
    global solver
    if settings['username']:
        # Starting solving the story in the other thread
        solver = solve.Solve(settings, label, text, listbox, path_appdata)
        thread_start_solving = threading.Thread(target=partial(solver.start_solving, x=window_width + 15, y=0,
                                                               width=root.winfo_screenwidth() - window_width - 15,
                                                               height=root.winfo_screenheight() -
                                                                      settings['title_height']),
                                                daemon=True)
        thread_start_solving.start()
    else:
        label.config(text='No active user found! Click "Settings" and add a new user.')


def button_ok_click():
    global solver
    if listbox.curselection():
        solver.story_index = listbox.curselection()[0]
        listbox.pack_forget()
        label.pack_forget()
        text.pack(side=TOP, fill=BOTH)
        text.config(yscrollcommand=scrollbar.set)
        text.bind('<Key>', lambda a: 'break')
        scrollbar.config(command=text.yview)
        button_ok.configure(state='disabled')


def button_exit_click():
    if solver is not None:
        solver.log_message('Please, wait. Exiting program...')
        time.sleep(2)
        solver.quit()
    sys.exit()


def button_settings_click(parent_window):
    def cb_change_user_changed(event):
        nonlocal username_new
        l_error.pack_forget()
        username_new = cb_change_user.get()

    def b_new_user_click():
        nonlocal username_new
        if e_login.get() != "" and e_pass.get() != "":
            l_error.pack_forget()
            username_new = e_login.get()
            users_new[username_new] = e_pass.get()
            cb_change_user.configure(values=list(users_new.keys()))
            e_login.delete(0, END)
            e_pass.delete(0, END)
            cb_change_user.set(username_new)
        else:
            l_error.pack()

    def b_delete_user_click():
        nonlocal username_new
        l_error.pack_forget()
        if cb_change_user.get():
            del (users_new[username_new])
            cb_change_user.configure(values=list(users_new.keys()))
            username_new = list(users_new.keys())[0] if users_new else ''
            cb_change_user.set(username_new)

    def chb_show_advanced_click():
        if show_advanced.get():
            f_advanced.pack(side='top', fill=X)
        else:
            f_advanced.pack_forget()

    def b_ok_click(window):
        global settings
        if e_login.get() != "" and e_pass.get() != "":
            b_new_user_click()
        settings['users'] = users_new
        settings['username'] = username_new
        settings['experience'] = int(e_experience.get())
        settings['story_count'] = int(e_story_count.get())
        settings['go_next_story'] = bool(go_next_story.get())
        settings['mute'] = bool(mute.get())
        settings['title_height'] = int(e_title_height.get())
        with open(path_settings, 'w') as ouf:
            json.dump(settings, ouf)
        window.destroy()
        if solver is None:
            label.config(text='Loading...')
            start_solving()

    go_next_story = BooleanVar()
    go_next_story.set(settings['go_next_story'])
    mute = BooleanVar()
    mute.set(settings['mute'])
    show_advanced = BooleanVar()
    show_advanced.set(False)

    parent_width, parent_height, parent_x, parent_y = map(int, re.split('[x+]', parent_window.geometry()))
    x = parent_x + parent_width // 2
    y = parent_y + parent_height // 2

    settings_window = Toplevel()  # вызываем главный метод библиотеки tkinter, создаём окно с настройками
    settings_window.resizable(False, False)
    settings_window.title('Settings')
    settings_window.geometry(f'+{x - 252 // 2}+{y - 270 // 2}')

    Label(settings_window, text='Текущий пользователь:').pack(side='top')

    users_new = settings['users'].copy()
    username_new = settings['username']
    cb_change_user = ttk.Combobox(settings_window, values=list(users_new.keys()), state="readonly")
    if username_new:
        cb_change_user.set(username_new)
    cb_change_user.pack(side='top')
    cb_change_user.bind("<<ComboboxSelected>>", cb_change_user_changed)

    f_user = Frame(settings_window)
    f_user.pack(side='top')
    f_user_buttons = Frame(f_user)
    f_user_buttons.pack(side='left')

    b_new_user = Button(f_user_buttons, text='Добавить\n или изменить\nпользователя', command=b_new_user_click)
    b_new_user.pack(side='top')
    b_delete_user = Button(f_user_buttons, text='Удалить\nпользователя', command=b_delete_user_click)
    b_delete_user.pack(side='top', fill=Y)
    f_user_data = Frame(f_user)
    f_user_data.pack(side='right')
    Label(f_user_data, text='Имя пользователя:').pack()
    e_login = Entry(f_user_data)
    e_login.pack()
    Label(f_user_data, text='Пароль:').pack()
    e_pass = Entry(f_user_data)
    e_pass.pack()

    f_experience = Frame(settings_window)
    f_experience.pack(side='top')
    Label(f_experience, text='Искать истории с опытом не менее', justify='left').pack(side='left')
    e_experience = Entry(f_experience, width=3)
    e_experience.pack(side='right')
    e_experience.insert(0, string=str(settings['experience']))

    f_story_count = Frame(settings_window)
    f_story_count.pack(side='top')
    Label(f_story_count, text='Количество историй для\nпрохождения (0 - без ограничений)',
          justify='left').pack(side='left')
    e_story_count = Entry(f_story_count, width=3)
    e_story_count.pack(side='right')
    e_story_count.insert(0, string=str(settings['story_count']))

    chb_go_next_story = Checkbutton(settings_window, text='После полного прохождения\n'
                                                          'переключаться на следующую историю',
                                    variable=go_next_story, onvalue=True, offvalue=False, justify='left')
    chb_go_next_story.pack(side='top')

    chb_mute = Checkbutton(settings_window, text='Отключить звук', variable=mute, onvalue=True, offvalue=False,
                           anchor='w')
    chb_mute.pack(side='top', fill=X)

    chb_show_advanced = Checkbutton(settings_window, text='Показать дополнительные настройки',
                                    variable=show_advanced, onvalue=True, offvalue=False, anchor='w',
                                    command=chb_show_advanced_click)
    chb_show_advanced.pack(side='top', fill=X)
    f_advanced = Frame(settings_window)
    Label(f_advanced, text='Высота заголовка окна').pack(side='left')
    e_title_height = Entry(f_advanced, width=3)
    e_title_height.insert(0, string=str(settings['title_height']))
    e_title_height.pack(side='right')

    f_buttons = Frame(settings_window)
    f_buttons.pack(side='bottom')
    b_ok = Button(f_buttons, text='OK', command=lambda: b_ok_click(settings_window))
    b_ok.pack(side='left')
    b_cancel = Button(f_buttons, text='Отмена', command=lambda: settings_window.destroy())
    b_cancel.pack(side='right')
    l_error = Label(settings_window, text='Введите имя пользователя и пароль!', fg='#ff0000')

    settings_window.mainloop()


path_appdata = os.path.join(shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, None, 0), 'DuolingoSolver')
if not os.path.exists(path_appdata):
    os.mkdir(path_appdata)

path_settings = os.path.join(path_appdata, 'settings.json')
# moving files for compatibility with version 0.1 beta
if os.path.exists('settings.json') and not os.path.exists(path_settings):
    shutil.copy('settings.json', path_settings)
if os.path.exists('settings.json') and os.path.exists(path_settings):
    try:
        os.remove('settings.json')
    except PermissionError:
        pass
path_answers = os.path.join(path_appdata, 'answers.txt')
if os.path.exists('answers.txt') and not os.path.exists(path_answers):
    shutil.copy('answers.txt', path_answers)
if os.path.exists('answers.txt') and os.path.exists(path_answers):
    try:
        os.remove('answers.txt')
    except PermissionError:
        pass

version = '0.2 beta'
solver = None
if os.path.exists(path_settings):
    with open(path_settings, 'r') as inf:
        settings = json.load(inf)
    settings.setdefault('users', dict())
    settings.setdefault('username', '')
    settings.setdefault('experience', 0)
    settings.setdefault('story_count', 10)
    settings.setdefault('go_next_story', False)
    settings.setdefault('title_height', 38)
    settings.setdefault('mute', False)

else:
    settings = {'users': dict(),
                'username': '',
                'experience': 0,
                'story_count': 10,
                'go_next_story': False,
                'title_height': 38,
                'mute': False}

root = Tk()  # main tkinter method, creating main window
root.title('Duolingo solver')
root.geometry('+0+0')
root.resizable(width=False, height=False)
image = Image.open('splash.jpg')
image = ImageTk.PhotoImage(image)
canvas = Canvas(root, bg='white', width=image.width(), height=image.height())
canvas.create_image(0, 0, anchor='nw', image=image)
canvas.create_text(image.width() // 2, 50, text='Duolingo solver', font='Verdana 42', fill='yellow')
canvas.create_text(image.width() // 2, 170, text='Choose your story:', font='Verdana 22', fill='yellow')
canvas.create_text(10, image.height() - 2, text='Version: ' + version, font='Verdana 8', fill='yellow', anchor='sw')
canvas.pack(side=TOP)
frame_listbox = Frame(root)
frame_listbox.place(relx=0.5, rely=0.5, relwidth=0.5, relheight=0.3, anchor=CENTER)
label = Label(frame_listbox, text='Loading...')
label.pack(side=BOTTOM, fill=X)
text = Text(frame_listbox, font='Arial 8')
text.insert(END, 'Loading...' + '\n')
scrollbar = Scrollbar(frame_listbox)
scrollbar.pack(side=RIGHT, fill=Y)
listbox = Listbox(frame_listbox, yscrollcommand=scrollbar.set)
scrollbar.config(command=listbox.yview)
listbox.pack(side=TOP, fill=BOTH)
frame_buttons = Frame(root)
frame_buttons.place(relx=0.5, rely=0.66, relwidth=0.5, relheight=0.07, anchor=N)
button_ok = Button(frame_buttons, text='OK', command=button_ok_click)
button_settings = Button(frame_buttons, text='Settings')
button_exit = Button(frame_buttons, text='Quit', command=button_exit_click)
button_ok.pack(side=LEFT, expand=1, fill=BOTH)
button_settings.pack(side=LEFT, expand=1, fill=BOTH)
button_exit.pack(side=LEFT, expand=1, fill=BOTH)

root.update_idletasks()  # update main window geometry data
window_width, window_height = map(int, root.geometry().split('+', 1)[0].split('x'))
button_settings.configure(command=lambda: button_settings_click(root))
start_solving()

root.mainloop()  # starting main tkinter loop

# TODO Add "mute' option
# TODO Add Russian and English interface languages
# TODO Add Log in by cookie
