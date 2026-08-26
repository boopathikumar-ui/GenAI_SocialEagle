import pyautogui
import time
pyautogui.failSafe = True
pyautogui.PAUSE = 1.0

#keyboard operation
pyautogui.typewrite('Hello, World!', interval=0.1) #type the text
pyautogui.press('enter') #press the enter key
pyautogui.hotkey('ctrl', 'c') #press the ctrl+c keys
pyautogui.hotkey('ctrl', 'v') #press the ctrl+v keys
pyautogui.sleep(1) #wait for 1 second


#keydown operations
pyautogui.keyDown('ctrl') #press and hold the ctrl key
pyautogui.press('c') #press the c key
pyautogui.keyUp('ctrl') #release the ctrl key