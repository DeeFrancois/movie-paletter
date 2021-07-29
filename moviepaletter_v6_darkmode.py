#TODO: Functionality is done, just gotta work on bug fixes/crash proofing now
#Maybe add new window for grid that gives a preview of twitter post (build 2x2 photo grid as matches are saved (click bottom left photo to save))
#Well, pretty much done, only major bug left is sometimes current_frame.jpg doesn't appear fast enough(?) or is just missing.. can fix this by doing a try except on every image open and put in a blank jpg 
import tkinter as tk
from tkinter.constants import DISABLED, HORIZONTAL
import tkinter.font as font
from typing_extensions import final

import numpy as np
import cv2
import sys
import PIL.ImageGrab
from PIL import Image, ImageDraw, ImageTk, ImageEnhance
from TikTokApi import TikTokApi
from tkinter import filedialog as fd
import threading
import shutil
from tkinter import messagebox, colorchooser
import time
import math
import tkinter.ttk as ttk


class windowMaker:

    def __init__(self):
        self.idk=1        
        self.img_array=[0,1,2,3]
        self.current_frame_num=0
        self.start_flag=0
        self.payload_available=0
        self.lock=0
        self.color_selected = 0
        self.p_diff=30
        self.color_accuracy = .05
        self.old_slider_val = 1
        self.opened_file=0
        self.process_flag=1
        self.seek_speed=0
        self.threshold=30
        self.current_palette_diffs=[]
        self.color_match_threshold=30
        self.finished=1
        self.stop_request=0
        self.to_save=0
    def palette(self,img):
        """
        Return palette in descending order of frequency
        """
        arr = np.asarray(img)
        palette, index = np.unique(self.asvoid(arr).ravel(), return_inverse=True)
        palette = palette.view(arr.dtype).reshape(-1, arr.shape[-1])
        count = np.bincount(index)
        order = np.argsort(count)
        #print(len(palette[order[::-1]]))
        return palette[order[::-1]]

    def asvoid(self,arr):
        """View the array as dtype np.void (bytes)
        This collapses ND-arrays to 1D-arrays, so you can perform 1D operations on them.
        http://stackoverflow.com/a/16216866/190597 (Jaime)
        http://stackoverflow.com/a/16840350/190597 (Jaime)
        Warning:
        >>> asvoid([-0.]) == asvoid([0.])
        array([False], dtype=bool)
        """
        arr = np.ascontiguousarray(arr)
        return arr.view(np.dtype((np.void, arr.dtype.itemsize * arr.shape[-1])))
    
    def palette_process(self,palette_array):
        #Crushing blacks
        new_array=[]
        black_count = 0
        for i in palette_array:
            x,y,z = i
            if (x < 40) and (y < 40) and (z < 40) and black_count==0:
                new_array.append([0,0,0])
                black_count=1
                #print("Crushing black")
            elif (x < 40) and (y < 40) and (z < 40) and black_count==1:
                continue
            else:
                new_array.append([x, y, z])

        return new_array
    
    
    def palette_process_two(self,palette_array):
        #print("printing palette_array from p2")
        #print(palette_array)
        #prevent similar colors
        new_array=[]
        new_array_diffs=[]
        #black_count = 0
        new_array.append(palette_array[0])
        
        count = 0
        temp = []

        if len(palette_array) > 1:
            for i in range(1,len(palette_array)):
                curr = palette_array[i]
                prev = palette_array[i-1]
                #if current color is within 3% of last, don't add
                #if ( abs(int(x)-int(a)) > int(int(x)*.1) and abs(int(y)-int(b)) > int(int(y)*.1) and abs(int(z)-int(c)) > int(int(z)*.1)): 
                #    new_array.append(curr)
                #    count +=1
                #print("Checking is different")
                if self.is_different_enough(curr,prev): #if different compared to previous, add if..
                    good_to_add = True
                    if len(new_array) > 0:
                        for i in new_array: #compare with all previous added as well

                            

                            if not self.is_different_enough(curr,i): 
                                #diff = math.sqrt((int(a)-int(x))**2+(int(b)-int(y))**2+(int(c)-int(z))**2)
                                #print(curr, "conflicts with previous value: ", i)
                                good_to_add = False
                    if good_to_add:
                        a,b,c = curr
                        x,y,z = prev
                        curr_diff = math.sqrt((int(a)-int(x))**2+(int(b)-int(y))**2+(int(c)-int(z))**2)
                        #print("Adding ", curr)
                        if(len(self.current_palette_diffs)<5):
                            self.current_palette_diffs.append(curr_diff)
                        new_array.append(curr)
                        #self.current_palette_diffs.append(curr_diff)
                        #print(new_array)
                        


        return new_array

    def is_different_enough(self,color_a,color_b):
        a,b,c = color_a
        x,y,z = color_b
        #p_diff = percent_diff
        #print(abs(a-x) > a*p_diff)
        #print(abs(b-y) > b*p_diff)
        #print(abs(c-z) > c*p_diff)

        #print("Comparing ", color_a, " to ", color_b)
        diff = math.sqrt((int(a)-int(x))**2+(int(b)-int(y))**2+(int(c)-int(z))**2)
        #print(diff)
        #print(color_a," and " ,color_b, "Have difference value of: ",new_diff)
        #diff =  (abs(int(a)-int(x)) > int(a)*p_diff and abs(int(b)-int(y)) > int(b)*p_diff and abs(int(c)-int(z)) > int(c)*p_diff)
        #if not diff:
            #print("Match Found: ",color_a, " and ", color_b)
        #print("Color A: ", color_a, " Color B: ", color_b, " Diff Value: ", diff, "Threshold: ", self.threshold)
        return (diff >= self.threshold)
    
    def is_similar_enough(self,color_a,color_b):
        a,b,c = color_a
        x,y,z = color_b
        p_diff = self.threshold
        #print(abs(a-x) > a*p_diff)
        #print(abs(b-y) > b*p_diff)
        #print(abs(c-z) > c*p_diff)

        #print("Comparing ", color_a, " to ", color_b)
        
        diff = math.sqrt((int(a)-int(x))**2+(int(b)-int(y))**2+(int(c)-int(z))**2)
        #print(diff)
        #diff =  (abs(int(a)-int(x)) < int(a)*p_diff and abs(int(b)-int(y)) < int(b)*p_diff and abs(int(c)-int(z)) < int(c)*p_diff)
        #if diff < self.color_match_threshold:
            #print("Match Found: ",color_a, " and ", color_b, " with diff_val= ",diff)
            #print(color_a," and " ,color_b, "Have difference value of: ",new_diff)

        
        return (diff < self.color_match_threshold)
    
    def display_diffs(self):
        if self.color_selected==0:
            return
        array = self.current_palette_array[:5]
        rgb = self.current_entry_rgb
        diff_array = []
        for i in array:
            #print(i)
            a,b,c = i
            x,y,z = rgb
            diff = math.sqrt((int(a)-int(x))**2+(int(b)-int(y))**2+(int(c)-int(z))**2)
            diff_array.append(int(diff))
            #print(diff)
        #print(self.current_palette_array[:5])

        result = "" + str(diff_array[0])+ "," + str(diff_array[1]) + "," + str(diff_array[2])+ "," + str(diff_array[3])+ "," + str(diff_array[4])
        result = diff_array
        self.diff_bar.delete(0,tk.END)
        self.diff_bar.insert(0,result)
        diff_array=[]


    def close(self,event): #ESC
        self.root.destroy()
        sys.exit(0)
    
    def open_file(self):
        self.current_frame_num=0
        self.filename=fd.askopenfilename()
        self.vc = cv2.VideoCapture(self.filename)
        self.frame_count = self.vc.get(7)
        self.left_frame_photo_slider.config(to=self.frame_count)
        if(self.frame_count == 0):
            print("Could not detect frames.")

        self.vc.set(1,0)
        rval, framei = self.vc.read()
        try:
            cv2.imwrite('current_frame.jpg',framei)
        except:
            print("Frame glitch")
        img = Image.open('current_frame.jpg')
        img.thumbnail((540,225))
        img.save('current_frame.jpg')
        photo = ImageTk.PhotoImage(file='current_frame.jpg')
        self.img_array[0]=photo
        self.left_frame_photo.config(image=photo)
        self.opened_file = 1
        self.start_button.config(state='active')
        self.grab_palette()
    
    def grab_frame(self):
        #ONLY USED BY EXECUTION THREAD
        self.current_frame_num+=self.seek_speed
        if self.current_frame_num > self.frame_count:
            self.current_frame_num=0
        self.vc.set(1,self.current_frame_num)
        
        rval, framei = self.vc.read()
        try:
            cv2.imwrite('current_frame.jpg',framei)
        except:
            print("Frame glitched")
        img = Image.open('current_frame.jpg')
        img.thumbnail((540,225))
        img.save('current_frame.jpg')

    def grab_frame_specific(self,frame_num):
        self.current_frame_num = frame_num
        self.vc.set(1,frame_num)
        rval, framei = self.vc.read()
        try:
            cv2.imwrite('current_frame.jpg',framei)
        except:
            print("Frame glitched")
        img = Image.open('current_frame.jpg')
        img.thumbnail((540,225))
        img.save('current_frame.jpg')
        
    def refresh_frame(self):
        #ONLY USED BY UPDATE FUCNTION
        self.left_frame_photo_slider.set(self.current_frame_num)
        img = Image.open('current_frame.jpg','r').convert('RGB')
        photo=ImageTk.PhotoImage(file='current_frame.jpg')
        self.img_array[0]=photo
        self.left_frame_photo.config(image=photo)


    
    def grab_palette(self):
        #ONLY USED BY EXECUTION THREAD
        img = Image.open('current_frame.jpg','r').convert('RGB')
        #Filter before processing
        #increase brightness
        #enhancer = ImageEnhance.Contrast(temp_img)
        #factor = 1
        #img = enhancer.enhance(2)
        #img.save('current_frame.jpg')
        #im_output.save('')

        #
        temp = self.palette(img)[:500] #500 is good default but maybe add advanced mode where u use like 10000
        self.current_palette_array=[(0,0,0),(0,0,0),(0,0,0),(0,0,0),(0,0,0)]
        self.current_palette_diffs=[]
        if self.process_flag == 1:
            temp =self.palette_process(temp)
            if len(temp)>4:
                temp = self.palette_process_two(temp)
            else:
                if len(temp)==0:
                    fill_color = temp[0]
                    self.current_palette_array[fill_color,fill_color,fill_color,fill_color,fill_color]
                else:
                    fill_color = temp[len(temp)-1]
                    for i in range(len(temp),5):
                        self.current_palette_array[i]=fill_color
            
            if len(temp)>4:
                self.current_palette_array=[temp[0],temp[1],temp[2],temp[3],temp[4]]
            else:
                if len(temp)==0:
                    fill_color = temp[0]
                    self.current_palette_array[fill_color,fill_color,fill_color,fill_color,fill_color]
                else:
                    fill_color = temp[len(temp)-1]
                    for i in range(0,len(temp)):
                        self.current_palette_array[i]=temp[i]
                    for i in range(len(temp),5):
                        self.current_palette_array[i]=fill_color
        else:
            self.current_palette_array=[temp[0],temp[1],temp[2],temp[3],temp[4]]

                
                
        
        #try:
        #    temp = self.palette(img)[:500]
        #    if self.process_flag == 1:
        #        temp=self.palette_process(temp)
        #        if len(temp) > 5:    
        #            temp=self.palette_process_two(temp)
        #            #print("after processing..")
        #            #print(temp[:5])
        #        
        #    self.current_palette_array=[temp[0],temp[1],temp[2],temp[3],temp[4]] #25 50
        #except:
        #    temp = self.palette(img)[0]
        #    self.current_palette_array= [temp,temp,temp,temp,temp]

        
        

        final_img = Image.new('RGB',(540,225))
        colors=[]
        for i in range(0,5):
            colors.append(Image.new('RGB',(108,225),tuple(self.current_palette_array[i])))
        
        for i in range(0,5):
            final_img.paste(colors[i],(i*108,0))
        
        #final_img.show()
        final_img.save('current_palette.jpg')
        #print("Current Palette: ",self.current_palette_array)

    def refresh_palette(self):
        #ONLY USED BY UPDATE FUCNTIOn
        

        img = Image.open('current_palette.jpg','r').convert('RGB')
        photo = ImageTk.PhotoImage(file='current_palette.jpg')
        self.img_array[1]=photo
        self.right_frame_photo.config(image=photo)
        if self.color_selected==1:
            for i in range(0,5):
                #print(i)
                #print(self.current_palette_array[i])
                self.color_match(self.current_entry_rgb,tuple(self.current_palette_array[i]))
                
    def color_match(self,entry_color,palette_color):
        #print("Comparing: ", entry_color, " to: ", palette_color)
        a,b,c = palette_color
        x,y,z = entry_color
        xmin = x - x*self.p_diff
        xmax = x + x*self.p_diff
        ymin = y - y*self.p_diff
        ymax = y + y*self.p_diff
        zmin = z - z*self.p_diff
        zmax = z + z*self.p_diff

        if self.is_similar_enough(entry_color,palette_color):
            #print("COLOR MAX HPLY FUCK ")
            photo=ImageTk.PhotoImage(file='current_frame.jpg')
            self.to_save=(self.filename,self.current_frame_num)
            self.img_array[3]=photo
            self.left_frame_photo_bottom.config(image=photo)
            time.sleep(2)
            #answer = messagebox.askyesnocancel("Question", "Found. Continue?")

    
    
    def threadedUpdate(self):
        while self.continue_loop==1:
            #print("Here")
            self.finished=0
            #print("Working..")
            self.grab_frame()
            #print("Grabbed Frame")
            self.grab_palette()
            #print("Grabbed Palette")
            self.refresh_frame()
            #print("Refreshing Frame")
            self.refresh_palette()
            #print("Refreshing Palette")
            #print("Finished")
            self.finished=1
        
    def save_frame(self):
        return
    
    def create_input(self):
        return
    
    def execute(self):
        #start the thread, enable update function
        
        if self.start_flag == 0 and self.stop_request==0:
            self.continue_loop = 1
            t1 = threading.Thread(target=self.threadedUpdate)
            t1.start()
            self.start_button.config(text="Stop")
            self.start_flag=1
        else:
            self.start_button.config(text="Start")
            self.continue_loop=0
            self.start_flag=0
            self.stop_request=1
            
    
    def scriptloop(self):
        #Save frame, grab next..
        while self.continue_loop==1:
            if count==3:
                count = 0
                self.payload_available=0
                shutil.copyfile('current_frame.jpg','new_frame.jpg')
                shutil.copyfile('current_palette.jpg','new_palette.jpg')
                self.payload_available=1
                
            count+=1
            self.grab_frame()
            self.grab_palette()
        #grab frame
        #grab palette
        #check if match
    
    def process_switch(self):
        if self.process_flag == 0:
            self.process_flag = 1
            self.process_button.config(text='Processed')
        else:
            self.process_flag = 0
            self.process_button.config(text='Unprocessed')
    
    def print_palette(self):
        if self.opened_file==1:
            self.rgb_bar.delete(0,tk.END)
            self.rgb_bar.insert(0,self.current_palette_array[:5])
        #print(self.current_palette_array[:5])

    def save_file(self):
        if self.to_save:
            
            #print(save_as)
            self.vc2 = cv2.VideoCapture(self.to_save[0]) #filename
            self.vc2.set(1,self.to_save[1]) #frame num
            rval, framei = self.vc2.read()
            fn = self.to_save[0].split('/')[len(self.to_save[0].split('/'))-1]
            #save_as=fd.asksaveasfilename(defaultextension='.jpg',initialfile='test.jpg') For Saving As
            save_as = ''+ fn + '_' + str(self.to_save[1]) +'.jpg'
            print(save_as)
            try:
                cv2.imwrite(save_as,framei)
            except:
                pass

    def createWindow(self):
        #Main Window Setup
        #print("Initializing")
        self.root = tk.Tk()
        self.root.tk.eval("""
set base_theme_dir ./awthemes-10.4.0/

package ifneeded awthemes 10.4.0 \
    [list source [file join $base_theme_dir awthemes.tcl]]
package ifneeded colorutils 4.8 \
    [list source [file join $base_theme_dir colorutils.tcl]]
package ifneeded awdark 7.12 \
    [list source [file join $base_theme_dir awdark.tcl]]
package ifneeded awlight 7.6 \
    [list source [file join $base_theme_dir awlight.tcl]]
""")
        self.root.tk.call("package","require",'awdark')
        
        ttk.Style().theme_use('awdark')
        ttk.Style().configure('black.TButton',foreground='black',background='black')
        ttk.Style().configure('C.TLabel',padding=[0,0,0,0],foreground='#33393b')
        ttk.Style().map('C.TLabel',
        relief=[('pressed', 'raised'),
            ('!pressed', 'raised')]
        )


        self.root.title("Movie Paletter - github.com/DeeFrancois")
        self.root.geometry("1280x600")
        #self.root.minsize(824,598)
        self.root.resizable(False,False)
        self.root.bind('<Escape>',self.close)
        self.button_font = font.Font(size=30)
        #self.root.protocol("WM_DELETE_WINDOW",self.on_closing_main)
        #temp_photo = Image.new('RGB',(540,225),(115,115,115))
        #temp_photo.save('placeholder_new.jpg')
        photo = ImageTk.PhotoImage(file='placeholder_new.jpg')
        self.img_array[0]=photo
        self.button_font = font.Font(size=30)

        self.mainFrame = ttk.Frame(self.root)
        self.mainFrame.pack(side='left', fill='both',expand=True)
        self.mainFrame.grid_rowconfigure(0,weight=1)
        self.mainFrame.grid_columnconfigure(0,weight=1)
        self.mainFrame.grid_columnconfigure(1,weight=1)
        self.mainFrame.grid_columnconfigure(2,weight=1)
        self.mainFrame.grid_columnconfigure(3,weight=1)
        self.mainFrame.grid_columnconfigure(4,weight=1)
        #Left Frame
        self.left_frame = ttk.Frame(self.mainFrame)
        self.left_frame.grid_rowconfigure(0,weight=1)
        self.left_frame.grid_rowconfigure(1,weight=1)
        self.left_frame.grid_columnconfigure(0,weight=1)
        self.left_frame.grid(column=0,row=0,sticky='nsew',columnspan=2)
        #Left Frame Pictures
        #Left Frame Topside
        self.left_frame_photo_and_slider=ttk.Frame(self.left_frame)
        self.left_frame_photo_and_slider.grid(row=0,column=0)
        self.left_frame_photo = ttk.Button(self.left_frame_photo_and_slider,style='C.TLabel')
        self.left_frame_photo.pack()
        self.left_frame_photo_slider=tk.Scale(self.left_frame_photo_and_slider,bg='#33393b',fg='white',highlightthickness=0,from_=1,to=100,length=540,orient=HORIZONTAL)
        self.left_frame_photo_slider.set(1)
        self.left_frame_photo_slider.pack()
        self.left_frame_photo_speed_bar = tk.Scale(self.left_frame_photo_and_slider,bg='#33393b',fg='white',highlightthickness=0,from_=-1000,to=1000,tickinterval=200,resolution=10,length=540,orient=HORIZONTAL)
        self.left_frame_photo_speed_bar.pack(pady=(21,0))
        self.left_frame_photo_speed_bar.set(10)
        #
        self.left_frame_photo_bottom = ttk.Button(self.left_frame,command=self.save_file,style='C.TLabel')
        self.left_frame_photo_bottom.grid(row=1,column=0)

        self.left_frame_photo.config(image=photo)
        self.left_frame_photo_bottom.config(image=photo)
        
        #Middle Frame
        self.mid_frame = ttk.Frame(self.mainFrame)
        self.mid_frame.grid(column=2,row=0,sticky='nsew')
        self.mid_frame.grid_columnconfigure(0,weight=1)
        self.mid_frame.grid_rowconfigure(0,weight=1)
        #Control Center
        self.control_grid = ttk.Frame(self.mid_frame,width=180)
        self.control_grid.grid(row=0,column=0,sticky='ew')
        self.control_grid.grid_columnconfigure(0,weight=1)

        self.rgb_bar = ttk.Entry(self.control_grid,width=20,font=("tk.DefaultFont",8))
        self.rgb_bar.pack(pady=5)

        self.mid_file_button = ttk.Button(self.control_grid,text="Open File",command=self.open_file)
        self.mid_file_button.pack(expand=False,fill='x')
        #self.entry_rgb = ttk.Entry(self.control_grid)
        #self.entry_rgb.pack(expand=False,fill='x')
        self.entry_rgb_start = ttk.Button(self.control_grid,text="Choose A Color",command=self.pull_color)
        self.entry_rgb_start.pack(expand=False,fill='x')
        #entry_percent_diff = ttk.Entry(self.control_grid)
        #self.entry_percent_diff.pack(expand=False,fill='x')
        self.start_button = ttk.Button(self.control_grid,text="Start",state='disabled',command=self.execute)
        self.start_button.pack(expand=False,fill='x')
        self.process_button = ttk.Button(self.control_grid,text="Processed",command=self.process_switch)
        self.process_button.pack(expand=False,fill='x')
        
        self.diff_bar = ttk.Entry(self.control_grid,width=20,font=("tk.DefaultFont",8))
        self.diff_bar.pack(pady=5)

        #Right Frame
        self.right_frame = ttk.Frame(self.mainFrame)
        self.right_frame.grid_columnconfigure(0,weight=1)
        self.right_frame.grid_rowconfigure(0,weight=1)
        self.right_frame.grid_rowconfigure(1,weight=1)
        self.right_frame.grid(column=3,row=0,sticky='nsew',columnspan=2)
        #Right Frame Pictures
        self.right_frame_tophalf = ttk.Frame(self.right_frame)
        self.right_frame_tophalf.grid(row=0,column=0)
    
        self.right_frame_photo = ttk.Button(self.right_frame_tophalf,style='C.TLabel',command=self.print_palette)
        self.right_frame_photo.pack()
        self.right_frame_photo.config(image=photo)
        self.right_frame_slider = tk.Scale(self.right_frame_tophalf,bg='#33393b',fg='white',highlightthickness=0,from_=0,to=100,tickinterval=10,length=540,orient=HORIZONTAL)
        self.right_frame_slider.pack()
        self.right_frame_slider.set(30)
        
        self.right_frame_bottom_slider = tk.Scale(self.right_frame_tophalf,bg='#33393b',fg='white',highlightthickness=0,from_=0,to=100,tickinterval=10,length=540,orient=HORIZONTAL)
        self.right_frame_bottom_slider.pack()
        self.right_frame_bottom_slider.set(30)
        
        self.right_frame_bothalf = ttk.Frame(self.right_frame)
        self.right_frame_bothalf.grid(row=1,column=0)

        self.right_frame_photo_bottom = ttk.Button(self.right_frame_bothalf,text="current palette",style='C.TLabel',command=self.display_diffs)
        self.right_frame_photo_bottom.pack()
        self.right_frame_photo_bottom.config(image=photo)
        #self.right_frame_color_accuracy_slider = ttk.Scale(self.right_frame_bothalf,from_=0,to=50,resolution=1,tickinterval=5,length=540,orient=HORIZONTAL)
        #self.right_frame_color_accuracy_slider.pack()
        #self.right_frame_color_accuracy_slider.set(10)
        



        #print(self.is_different_enough((120,20,29),(131,64,32),.07))
        self.root.after(3000,self.update)
        #print("Running main loop")
        self.root.mainloop()
    


        
        

    def pull_color(self):
        color_code = colorchooser.askcolor(title="Choose color")
        #print(color_code[0])
        self.color_selected = 1
        final_img = Image.new('RGB',(540,225),(255,255,255)) #create canvas 
        #TEST_IMAGE = Image.new('RGB',(540,255),rgb[0])
        #TEST_IMAGE.show()
        entry_color=color_code[0]
        a,b,c = (int(x) for x in entry_color)
        #print(a,b,c)
        self.current_entry_rgb = (a,b,c)
        #print(entry_color)
        #a,b,c = entry_color
        rgb = (a,b,c)
        single_colors=[]
        for i in range(0,3):
            single_colors.append(Image.new('RGB',(180,225),rgb)) #creates individual colors
        
        for i in range(0,3):
            final_img.paste(single_colors[1],(i*180,0))
        
        final_img.save('right_bottom_photo.jpg')
        photo = ImageTk.PhotoImage(file='right_bottom_photo.jpg')
        self.img_array[2] = photo
        self.right_frame_photo_bottom.config(image=photo)

    def update(self): #Without threading - On update: grab next frame and display, grab palette and display, check for match set match_found flag
        #if self.entry_percent_diff.get():
        #    self.color_accuracy = float(int(self.entry_percent_diff.get())/100)
        #self.color_accuracy = float(int(self.entry_percent_diff.get())/100)

        current_slider = int(self.left_frame_photo_slider.get())

        if self.start_flag==0 and (self.old_slider_val != current_slider) and self.opened_file==1:
            #print("IN HERE")
            #print("From ",self.old_slider_val, " to ",current_slider)
            self.old_slider_val=current_slider
            self.grab_frame_specific(current_slider)
            self.grab_palette()
            self.refresh_frame()
            self.refresh_palette()

        self.threshold = float(self.right_frame_slider.get())
        self.color_match_threshold = float(self.right_frame_bottom_slider.get())
        #self.color_accuracy=float(self.right_frame_color_accuracy_slider.get()/100)
        #if self.color_accuracy_old == self.color_accuracy
        self.seek_speed=int(self.left_frame_photo_speed_bar.get())

        if self.finished==1:
            self.stop_request=0

        self.root.after(1000,self.update)
    
    
def main():
    window = windowMaker()
    window.createWindow()

main()


