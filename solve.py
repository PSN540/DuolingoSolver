import selenium.webdriver.chrome.service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import json
import sys
import time


class Solve:
    def __init__(self, settings, label, text, listbox, path_appdata):
        self.story_index = -1
        self.windows_chromedriver_path = 'chromedriver.exe'
        self.linux_chromedriver_path = r'/usr/local/bin/chromedriver104'
        self.label = label
        self.text = text
        self.listbox = listbox
        self.settings = settings
        self.path_answers = os.path.join(path_appdata, 'answers.txt')
        if not os.path.exists(self.windows_chromedriver_path):
            self.windows_chromedriver_path = '..\\Chromium\\' + self.windows_chromedriver_path
        pass

    def log_message(self, message):
        print(message)
        self.label.config(text=message)
        self.text.insert('end', message + '\n')

    def quit(self):
        self.driver.quit()

    def start_solving(self, x, y, width, height):

        def check_level(stories_elements_local):  # checking current level
            lvl = len(stories_elements_local) - 1
            while not stories_elements_local[lvl].is_displayed():
                lvl -= 1
            if lvl < len(stories_elements_local) - 1:
                self.driver.implicitly_wait(0)
                nxt = stories_elements_local[lvl + 1].find_elements(by='tag name', value='div')
                self.driver.implicitly_wait(10)
                if len(nxt) > 0 and nxt[0].is_displayed():
                    lvl += 1
            return lvl

        def save_answers(dic):
            self.log_message('Saving to file answers.txt')
            with open(self.path_answers, 'w') as ouf:
                json.dump(dic, ouf)

        def go_next(first_l):  # press "Next" button
            nonlocal stories_elements
            lvl = None
            stop_flag = False
            while True:
                for _ in range(20):
                    if btn_next.is_enabled():
                        btn_next.click()
                        break
                    # find button by text "Я сейчас не могу говорить" and click it if found
                    self.driver.implicitly_wait(0)
                    cant_speak = self.driver.find_elements(By.XPATH, value="//span[contains(text(), "
                                                                           "'Я сейчас не могу говорить')]")
                    self.driver.implicitly_wait(10)
                    if len(cant_speak) > 0:
                        cant_speak[0].click()
                        btn_next.click()
                        stories_elements = self.driver.find_elements(By.XPATH,
                                                                     value='//div[@data-test="stories-element"]')
                        break
                    lvl = check_level(stories_elements)
                    if str(lvl) in answers[story_name][first_l].keys():
                        stop_flag = True
                        break
                    time.sleep(0.3)
                else:
                    stop_flag = True
                if stop_flag:
                    break
            return lvl

        def go_buttons(level, first_l):
            # look for all checkboxes
            self.driver.implicitly_wait(0)
            buttons = stories_elements[level].find_elements(by='tag name', value='li')
            li = len(buttons) > 0
            # if checkboxes are not found, then we are looking for all buttons
            if not li:
                buttons = stories_elements[level].find_elements(by='tag name', value='button')
            # check if it's a dictionary translation of words
            self.driver.implicitly_wait(10)
            if len(buttons) == 10:
                go_dictionary(level)
                return False
            # if the answers are saved, then click on the desired buttons
            if str(level) in answers[story_name][first_l]:
                for word_id in sorted(list(answers[story_name][first_l][str(level)].keys())):
                    for button in buttons:
                        if button.text.strip() == answers[story_name][first_l][str(level)][word_id]:
                            if li:
                                button.find_element(by='tag name', value='button').click()
                            else:
                                button.click()
                            break
            # if the answers are not saved, then iterate through all the buttons
            else:
                answers[story_name][first_l][str(level)] = dict()
                need_save = False
                for word_id in range(len(buttons)):
                    if btn_next.is_enabled():
                        break
                    for button in buttons:
                        if li:
                            btn = button.find_element(by='tag name', value='button')
                        else:
                            btn = button
                        len1 = len(stories_elements[level - 1].find_element(By.TAG_NAME, value='div').find_elements(
                            By.TAG_NAME, value='div'))
                        atr = button.get_attribute('class') + btn.get_attribute('class')
                        btn.click()
                        time.sleep(1)
                        if atr != button.get_attribute('class') + btn.get_attribute('class'):
                            if btn_next.is_enabled() or len(
                                    stories_elements[level - 1].find_element(By.TAG_NAME, value='div').find_elements(
                                            By.TAG_NAME, value='div')) != len1:
                                answers[story_name][first_l][str(level)][str(word_id)] = button.text
                                need_save = True
                                break
                if need_save:
                    save_answers(answers)
            return True

        def go_dictionary(level):
            # translate words in a dictionary
            buttons = stories_elements[level].find_elements(by='tag name', value='button')
            objs_rus = buttons[:5]
            objs_eng = buttons[5:]
            # if the answers are not saved, then create an empty dictionary
            if not ('dict' in answers[story_name]):
                answers[story_name]['dict'] = dict()
            need_save = False
            atr = buttons[0].get_attribute('class')
            # if the word is saved in the dictionary, then click on the buttons
            for obj_rus in objs_rus:
                if obj_rus.text[2:] in answers[story_name]['dict']:
                    for obj_eng in objs_eng:
                        if obj_eng.text[2:] == answers[story_name]['dict'][obj_rus.text[2:]]:
                            obj_rus.click()
                            obj_eng.click()
                            break
                # if the word is not in the dictionary, then click on all the buttons in turn
                else:
                    need_save = True
                    for obj_eng in objs_eng:
                        if obj_eng.get_attribute('class') == atr:
                            obj_rus.click()
                            obj_eng.click()
                            time.sleep(2)
                            if obj_eng.get_attribute('class') != atr:
                                answers[story_name]['dict'][obj_rus.text[2:]] = obj_eng.text[2:]
                                break
            if need_save:
                save_answers(answers)

        if os.path.exists(self.path_answers):
            with open(self.path_answers, 'r') as inf:
                answers = json.load(inf)
        else:
            answers = dict()
        first = 'first'
        os_windows = (sys.platform == 'win32')
        chromedriver_path = self.windows_chromedriver_path if os_windows else self.linux_chromedriver_path
        chrome_service = selenium.webdriver.chrome.service.Service(executable_path=chromedriver_path)
        chrome_options = selenium.webdriver.ChromeOptions()
        chrome_options.add_argument('detach=true')
        if self.settings['mute']:
            chrome_options.add_argument('--mute-audio')
        if os_windows:
            from subprocess import CREATE_NO_WINDOW
            chrome_service.creationflags = CREATE_NO_WINDOW
        capabilities = DesiredCapabilities.CHROME
        capabilities["pageLoadStrategy"] = "eager"
        self.driver = webdriver.Chrome(service_log_path=os.devnull, options=chrome_options, service=chrome_service,
                                       desired_capabilities=capabilities)
        try:
            self.driver.set_window_rect(x, y, width, height)
            self.driver.implicitly_wait(10)
            # set the scale
            self.driver.get('chrome://settings/')
            if width > 1050:
                zoom = '1'
            elif width > 950:
                zoom = '0.9'
            elif width > 850:
                zoom = '0.8'
            elif width > 800:
                zoom = '0.75'
            elif width > 700:
                zoom = '0.67'
            else:
                zoom = '0.5'
            self.driver.execute_script(f'chrome.settingsPrivate.setDefaultZoom({zoom});')
            # open the login page
            self.driver.capabilities["pageLoadStrategy"] = 'none'
            self.driver.get('https://www.duolingo.com/stories?isLoggingIn=true')
            self.driver.capabilities["pageLoadStrategy"] = 'normal'
            while True:
                time.sleep(0.2)
                objs = self.driver.find_elements(by='id', value='sign-in-btn')
                if objs:
                    objs[0].click()
                    break

            # enter login and password
            obj = self.driver.find_elements(by='tag name', value='input')
            obj[0].send_keys(self.settings['username'])
            obj[1].send_keys(self.settings['users'][self.settings['username']])
            obj = self.driver.find_element(By.XPATH, value="//button[@data-test='register-button']")
            obj.click()
            objs = self.driver.find_elements(By.XPATH,
                                             "/html/body/div[1]/div[5]/div/div[2]/div[1]/div/div/div[3]/div/span")
            time.sleep(1)
            if objs:
                objs[0].click()

            is_first_time = True
            iteration = 0
            while (is_first_time or self.settings['go_next_story']) and\
                    (iteration < self.settings['story_count'] or self.settings['story_count'] == 0):
                is_first_time = False
                stories = []
                objs = self.driver.find_elements(By.XPATH, value=f"//div[contains(text(), 'Опыт: +')]")
                for obj in objs:
                    if self.story_index >= 0:
                        break
                    if int(obj.text[obj.text.find('+') + 1:]) >= self.settings['experience']:
                        self.listbox.insert('end', obj.find_element(By.XPATH,
                                                                    './../..').text.replace('\nОПЫТ', ' опыт'))
                        stories.append(obj)
                if self.story_index >= len(stories):
                    self.log_message('Reached the end of the story lst')
                    break
                self.label.config(text='Loading OK!')
                self.text.insert('end', 'Loading OK!\n')
                while self.story_index == -1:
                    time.sleep(0.1)
                self.log_message('Loading story...')
                obj = stories[self.story_index].find_element(By.XPATH, './../..')
                obj.click()
                objs = obj.find_elements(By.XPATH, value="//a[@data-test='story-start-button']")
                story_name = objs[0].get_attribute('href')
                story_name = story_name[story_name.find('stories/') + 8: story_name.find('?')]
                self.log_message(f'Loading story "{story_name}"...')
                if story_name not in answers:
                    answers[story_name] = {'first': dict(), 'subsequent': dict()}
                while iteration < self.settings['story_count'] or self.settings['story_count'] == 0:
                    iteration += 1
                    # open the page with the desired story
                    self.driver.get('https://www.duolingo.com/stories/' + story_name + '?mode=conversation')
                    # Click the "Start Story" button
                    time.sleep(1)
                    obj = self.driver.find_element(By.XPATH, value="//button[@data-test='story-start']")
                    obj.click()
                    self.log_message(f'Solving story "{story_name}", iteration {iteration}')
                    btn_next = self.driver.find_element(By.XPATH,
                                                        value="//button[@data-test='stories-player-continue']")
                    # Looking for all the elements of the story
                    stories_elements = self.driver.find_elements(By.XPATH,
                                                                 value='//div[@data-test="stories-element"]')
                    # solving the story
                    loop_flag = True
                    while loop_flag:
                        level_global = go_next(first)  # нажимаем "Далее"
                        loop_flag = go_buttons(level_global, first)  # нажимаем на кнопку с ответом
                    # Click "Next" button
                    btn_next.click()
                    # display the number of experience points
                    experience = None
                    for _ in range(10):
                        time.sleep(0.5)
                        obj = self.driver.find_elements(By.XPATH, value="//span[contains(text(), 'Опыт:')]")
                        if len(obj) > 0 and obj[0].text:
                            experience = obj[0].text
                            self.log_message(experience)
                            experience = int(experience[experience.rfind('+') + 1:])
                            break
                    if experience == 2:
                        self.log_message('Too small experience. Finishing solving this story.')
                        break
                    # one more click of the "Next" button for the first time in a day
                    while len(obj := self.driver.find_elements(By.XPATH,
                                                               value="//span[contains(text(), 'Далее')]")) > 0:
                        obj[0].click()
                    first = 'subsequent'
                self.log_message(f'Finished {iteration} iterations!')
        finally:
            print('closing program')
            self.driver.close()
