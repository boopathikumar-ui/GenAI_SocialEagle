import pyautogui
import time
pyautogui.failSafe = True
pyautogui.PAUSE = 1.0

#mouse operation
pyautogui.moveTo(100, 100, duration=1.0) #move the mouse to (100, 100) over 1 second
pyautogui.click() #click the mouse at the current position
pyautogui.leftClick(100,100) #left click the mouse at the current position
pyautogui.rightClick(100,100) #right click the mouse at the current position
pyautogui.doubleClick(100,100) #double click the mouse at the current position
pyautogui.scroll(500) #scroll up 10 units
pyautogui.sleep(1) #wait for 1 second
pyautogui.scroll(-500) #scroll down 10 units
