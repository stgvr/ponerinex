import kivy
# Ponerine.X Multi-Cam Controller for XueTan
kivy.require('1.9.0')

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager , SlideTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.spinner import Spinner

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.lang import Builder, Parser, ParserException
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty, ObjectProperty, OptionProperty

from kivy.graphics import Color, Ellipse, Rectangle
from math import cos, sin, pi
from random import random

# Camera Object[camera.py]
from xcamera import XCamera
from xcameratelnet import XCameraTelnet
'''
platform.system()
"Windows", "Darwin", "Linux"
'''
import json, os, threading, time, socket, platform, inspect, string, copy
from os.path import basename
from functools import partial

Builder.load_file('xdata/xrecord_screen.kv')
Builder.load_file('xdata/xpopupconfig.kv')
Builder.load_file('xdata/xapp_title.kv')
Builder.load_file('xdata/xcam_info.kv')
Builder.load_file('xdata/xcam_control.kv')

Clock.max_iteration = 100
__version__='0.0.4'

class RLabel(Label):
  name = StringProperty()

class CLabel(AnchorLayout):
  adapter = NumericProperty()
  battery = NumericProperty()
  memory = NumericProperty()
  text = StringProperty()
  status = OptionProperty("disable", options=["disable","enable","on","off","link","busy","beep","error"])

class XRecordScreen(Screen):
  pass

class XAppTitle(BoxLayout):
  pass

class XCamInfo(GridLayout):
  pass

class XCamControl(BoxLayout):
  pass

class AdvancedPopup(Popup):
  scenename = StringProperty()
  sceneshot = NumericProperty()
  autorename = BooleanProperty()
  moveduplicated = BooleanProperty()
  buzzeronstart = BooleanProperty()
  buzzeronstop = BooleanProperty()
  buzzermute = BooleanProperty()
  photomode = BooleanProperty()
  apply = BooleanProperty()

class ConfigPopup(Popup):
  cfg = ObjectProperty()
  apply = BooleanProperty()

class CameraSettingPopup(Popup):
  asid = StringProperty()
  format = BooleanProperty()
  reboot = BooleanProperty()
  restore = BooleanProperty()
  syncall = BooleanProperty()
  apply = BooleanProperty()

class ManualExposurePopup(Popup):
  shutter = StringProperty()
  iso = StringProperty()
  apply = BooleanProperty()

class XPonerine(ScreenManager):
  def InitControls(self):
    idx_button = 0
    idx_meter = 0
    idx_resolution = 1
    idx_camera = 2
    idx_status = 3
    idx_scene = 4
  
    self.xapptitle = XAppTitle() #LOGO
    self.xcamcontrol = XCamControl() #BUTTON
    self.xcaminfo = XCamInfo() #CAM ICONS
    
    self.btnsetting = self.xcamcontrol.children[idx_button].children[2]
    self.btnsetting.bind(text=self.ConfigPopupOpen)
    self.btnrecord = self.xcamcontrol.children[idx_button].children[1]
    self.btnrecord.bind(on_release=self.Record)
    self.btnmeter = self.xcamcontrol.children[idx_button].children[0]
    self.btnmeter.bind(text=self.ConfigPopupOpen)
    
    self.lbliso = self.xcaminfo.children[idx_meter].children[0]
    self.lblshutter = self.xcaminfo.children[idx_meter].children[1]
    self.lblexposure = self.xcaminfo.children[idx_meter].children[2]
    self.lblmetermode = self.xcaminfo.children[idx_meter].children[3]
    
    self.lblaspect = self.xcaminfo.children[idx_resolution].children[0]
    self.lblbitrate = self.xcaminfo.children[idx_resolution].children[1]
    self.lblframe = self.xcaminfo.children[idx_resolution].children[2]
    self.lblresolution = self.xcaminfo.children[idx_resolution].children[3]
    
    self.lblcam = []
    for i in range(7,0,-1):
      lbl = self.xcaminfo.children[idx_camera].children[i-1]
      self.lblcam.append(lbl)

    self.lblrecordtime = self.xcaminfo.children[idx_status].children[0]
    self.lblrecordtime.color = (0.25,0.25,0.25,1)
    self.lblstatus = self.xcaminfo.children[idx_status].children[1]
    print "self.lblstatus.color", self.lblstatus.color
    
    self.lblsceneshot = self.xcaminfo.children[idx_scene].children[0]
    self.lblscenename = self.xcaminfo.children[idx_scene].children[1]
    
    self.lblscenename.text = self.camscenename
    self.lblsceneshot.text = '%02d' %self.camsceneshot
    self.lblstatus.text = self.camstatus
    self.lblrecordtime.text = self.camrecordtime
    self.lblresolution.text = self.camresolution
    self.lblframe.text = self.camframe
    self.lblbitrate.text = self.cambitrate
    self.lblaspect.text = self.camaspect
    self.lblmetermode.text = self.cammetermode
    self.lblexposure.text = self.camexposure
    self.lblshutter.text = self.camshutter
    self.lbliso.text = self.camiso
    
    wg_main = self.current_screen.children[0]
    wg_main.clear_widgets()
    wg_main.add_widget(self.xapptitle)
    wg_main.add_widget(self.xcaminfo)
    wg_main.add_widget(self.xcamcontrol)
      
    self.lblscenename.bind(text=self.LabelText)
    self.lblsceneshot.bind(text=self.LabelText)
    self.lblstatus.bind(text=self.LabelText)
    self.lblrecordtime.bind(text=self.LabelText)
    self.lblresolution.bind(text=self.LabelText)
    self.lblframe.bind(text=self.LabelText)
    self.lblbitrate.bind(text=self.LabelText)
    self.lblaspect.bind(text=self.LabelText)
    self.lblmetermode.bind(text=self.LabelText)
    self.lblexposure.bind(text=self.LabelText)
    self.lblshutter.bind(text=self.LabelText)
    self.lbliso.bind(text=self.LabelText)
    
    if self.inited:
      for lbl in self.lblcam:
        lbl.bind(size=self.DrawCamera,pos=self.DrawCamera,status=self.DrawCamera,battery=self.DrawCamera,adapter=self.DrawCamera,memory=self.DrawCamera)
  
  def DrawCamera(self, *args):
    if len(args) == 0:
      return
    i = 0
    for lbl in self.lblcam:
      if lbl == args[0]:
        lbl = args[0]
        break
      i += 1
    if i >= len(self.lblcam):
      return
    Clock.unschedule(self.DoDrawCamera)
    #print 'DrawCamera',args[0],i
    Clock.schedule_once(partial(self.DoDrawCamera,args[0]))
  
  def DoDrawCamera(self, clabel, *args):
    #print 'DoDrawCamera',clabel,args
    lsize = clabel.size
    lpos = clabel.pos
    lstatus = clabel.status
    lbltext = clabel.children[1]
    imgcanvas = clabel.children[0]
    midx = int(clabel.memory/2)
    bidx = int(clabel.battery/2)
    apt = clabel.adapter
    #options=["disable","enable","on","link","busy","error"]
    a=0.8
    if lstatus == "disable":
      r=0;g=0;b=0;a=0
    elif lstatus in ("enable","beep"): #blue
      r=0;g=0.75;b=1
    elif lstatus == "on": #green
      r=0;g=1;b=0
    elif lstatus == "link": #white
      r=1;g=1;b=1;a=0.25
    elif lstatus == "busy":
      r=1;g=1;b=0.25
    elif lstatus in ("error","off"):
      r=1;g=0;b=0
    lbltext.color = (r,g,b,1)
    imgcanvas.canvas.clear()
    if lstatus == "disable":
      return
    #draw status circle
    with imgcanvas.canvas:
      Color(r,g,b,a)
      Rectangle(size=lsize,pos=lpos,source='ximage/camstatus.png')
    if lstatus in ("enable","on","off"):
      return
    
    #draw memory circle
    a=0.7
    if midx > 40 or midx == -1: #red or no card
      r=1;g=0;b=0
    elif midx > 30: #orange
      r=1;g=0.3;b=0
    elif midx > 20: #yellow
      r=1;g=1;b=0.25
    elif midx > 10: #blue
      r=0;g=0.75;b=1
    elif midx > 0: #green
      r=0;g=1;b=0

    with imgcanvas.canvas:
      if midx > 0:
        Color(.15,.15,.15,1)
        Rectangle(size=lsize,pos=lpos,source='ximage/cammemory.png')
        Color(r,g,b,a)
        Rectangle(size=lsize,pos=lpos,source='ximage/memory/m%02d.png' %midx)
      elif midx == -1:
        Color(r,g,b,a)
        Rectangle(size=lsize,pos=lpos,source='ximage/memory/m50.png')

    #draw battery circle    
    if bidx <= 0 and apt == 0:
      return
    a=0.6
    if apt == 1:
      if bidx <> 0:
        r=0;g=1;b=0
      else:
        r=1;g=0;b=0
    elif bidx < 10: #red
      r=1;g=0;b=0
    elif bidx < 20: #orange
      r=1;g=0.3;b=0
    elif bidx < 30: #yellow
      r=1;g=1;b=0.25
    elif bidx < 40: #blue
      r=0;g=0.75;b=1
    else: #green
      r=0;g=1;b=0
    with imgcanvas.canvas:
      if bidx > 0:
        Color(.15,.15,.15,1)
        Rectangle(size=lsize,pos=lpos,source='ximage/cambattery.png')
        Color(r,g,b,a)
        Rectangle(size=lsize,pos=lpos,source='ximage/battery/b%02d.png' %bidx)
      else:
        Color(r,g,b,a)
        Rectangle(size=lsize,pos=lpos,source='ximage/battery/b50.png')

  def TestBat(self,idx):
    time.sleep(idx*2)
    self.lblcam[2].color = (random(),random(),random(),1)
    self.lblcam[2].battery = idx
    self.lblcam[2].memory = idx
  
  def TestColor(self,*args):
    i = int(random() * 7.0)
    print 'TestColor',i
    self.lblscenename.text = "PonerineX%0.2f" %(random())
    s = ["disable","enable","on","link","busy","error"]
    j = int(random() * 6.0)
    self.lblcam[i].status = s[j]
    self.lblcam[i].battery = int(random() * 100.)
    self.lblcam[i].memory = int(random() * 100.)
    print 'S %s B %s M %s' %(self.lblcam[i].status,self.lblcam[i].battery,self.lblcam[i].memory)
    #for i in range(100):
      #threading.Thread(target=self.TestBat, args=(i,), name="TestBat").start() 
  
  def LabelText(self,*args):
    if len(args) == 0:
      return
    lbl = args[0]
    print 'LabelText',lbl.name,args
    if lbl.name == 'scenename':
      self.camscenename = lbl.text
    elif lbl.name == 'sceneshot':
      self.camsceneshot = int(lbl.text)
    elif lbl.name == 'status':
      self.camstatus = lbl.text
    elif lbl.name == 'recordtime':
      self.camrecordtime = lbl.text
    elif lbl.name == 'resolution':
      self.camresolution = lbl.text
    elif lbl.name == 'frame':
      self.camframe = lbl.text
    elif lbl.name == 'bitrate':
      self.cambitrate = lbl.text
    elif lbl.name == 'aspect':
      self.camaspect = lbl.text
    elif lbl.name == 'metermode':
      self.cammetermode = lbl.text
    elif lbl.name == 'exposure':
      self.camexposure = lbl.text
    elif lbl.name == 'shutter':
      self.camshutter = lbl.text
    elif lbl.name == 'iso':
      self.camiso = lbl.text
    
  def __init__(self, appevent):
    super(XPonerine, self).__init__()
    self.inited = False
    
    self.applyconfig = False
    self.appexit = appevent[0]

    #camera config settings
    self.cfglist = []
    self.autorename = False
    self.moveduplicated = False
    self.buzzeronstart = False
    self.buzzeronstop = False
    self.buzzermute = False
    self.photomode = False
    #camera label settings
    self.camscenename = ''#'PonerineX'
    self.camsceneshot = ''#1
    self.camstatus = ''#'REC'
    self.camrecordtime = '00:00:00'#'00:00:00'
    self.camresolution = ''#'1600x1200'
    self.camframe = ''#'60P'
    self.cambitrate = ''#'35M'
    self.camaspect = ''#'4:3'
    self.cammetermode = ''#'average'
    self.camexposure = ''#'auto'
    self.camshutter = ''#'1/60s'
    self.camiso = ''#'800'
    
    self.shutter = '1 / 60s'
    self.iso = 'ISO 100'
    
    self.linked = 0
    self.recstart = 0
    self.maxcam = 0
    self.cfglist = self.ReadConfig()
    self.stopdetect = threading.Event()
    #self.resizecam = threading.Event()
    #self.connect = threading.Event()
    self.recordstart = threading.Event()
    self.recordstop = threading.Event()
    
    sysname = platform.system()
    if sysname == "Windows":
      Window.size = (600,960) #(560,896) #(560,800) #(720,800)
      #Window.borderless = '1'
    elif sysname == "Darwin":
      Window.size = (600,720) #(520,700)
    elif sysname == "Linux":
      if platform.linux_distribution()[0] == "Ubuntu":
        Window.size = (560,800)
        
  def DetectCam(self):
    self.cam = []
    self.quitcam = []
    self.renlist = []
    self.linked = 0
    self.maxcam = 0
    for i in range(self.cameras):
      self.quitcam.append(threading.Event())
      cam = XCamera()
      cam.number = i
      if self.cfglist[i]["ip"] <> "" and self.cfglist[i]["enabled"] == 1:
        cam.enabled = True
        cam.ip = self.cfglist[i]["ip"]
        self.maxcam += 1
        self.lblcam[i].status = 'enable'
        threading.Thread(target=self.DoDetectCam, name="%sDoDetectCam" %cam.ip, args=(i,)).start()
      else:
        self.lblcam[i].status = 'disable'
      self.cam.append(cam)
      self.renlist.append({})
      
#     t = threading.Thread(target=self.DoRefreshConnectControl, name="DoRefreshConnectControl")
#     t.setDaemon(True)
#     t.start()
  
  def DoDetectCam(self, index):
    while self.quitcam[index].isSet():
      pass
    print 'Start DoDetectCam %d' %index
    bind = False
    # slow down detect for first time
    while self.inited == False:
      bind = True
      time.sleep(1)
    self.DrawCamera(self.lblcam[index])
    self.lblcam[index].bind(size=self.DrawCamera,pos=self.DrawCamera,status=self.DrawCamera) #,battery=self.DrawCamera,adapter=self.DrawCamera,memory=self.DrawCamera)
    port = [7878, 8787, 554, 23]
    # while True:
      # if self.cam[index].enabled:
        # self.lblcam[index].status = "enable"
        # self.DrawCamera(self.lblcam[index])
        # break
    socket.setdefaulttimeout(5)
    retry = 0
    timewait = 1
    while True:
      self.quitcam[index].wait(timewait)
      if self.quitcam[index].isSet():
        self.quitcam[index].clear()
        print 'Quit DoDetectCam %d' %index
        return
      retry = (retry + 1) % len(port)
      srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      srv.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
      open = srv.connect_ex((self.cam[index].ip, port[retry])) #7878
      srv.close()
      print "index %d ip %s port %d retry %d open %d" %(index, self.cam[index].ip, port[retry], retry, open)
      if open == 0:
        self.lblcam[index].status = "on"
        time.sleep(1)
        threading.Thread(target=self.DoConnect, name="%dDoConnect" %index, args=(index,)).start()
        #self.DrawCamera(self.lblcam[index])
        return
      elif retry == 0:
        if timewait < 10:
          timewait += 1
        self.lblcam[index].status = "off"
        #if self.lblcam[index].status <> "error":
          #self.lblcam[index].status = "error"
          #self.DrawCamera(self.lblcam[index])
  
  def DoConnect(self, index):
    print "Doconnect camera %d" %index
    cam = self.cam[index]
    cam.LinkCamera()
    t = time.time()
    while True:
      if cam.socketopen == 0:
        break
      if time.time() - t > 30.0:
        self.lblcam[index].status = "off"
        threading.Thread(target=self.DoDetectCam, name="%sDoDetectCam" %cam.ip, args=(index,)).start()
        return
    t = time.time()
    while True:
      if cam.link:
        break
      if time.time() - t > 30.0:
        self.lblcam[index].status = "off"
        threading.Thread(target=self.DoDetectCam, name="%sDoDetectCam" %cam.ip, args=(index,)).start()
        return
    while cam.token == 0:
      pass
    print "name", cam.name, "token", cam.token
    
    # sync time
    setok = cam.setok
    #offset index*12=0,10,20,30,40,50,60
    t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()+ index * 10))
    print "time offset: %s" %t
    cam.ChangeSetting("camera_clock", t)
    setok.wait(10)
    cam.msgbusy = 0
    #set meter mode
    cam.ChangeSetting("meter_mode",self.cammetermode)
    setok.wait(10)
    cam.msgbusy = 0
    # mute buzzer
    if self.buzzermute:
      cam.SendMsg('{"type":"buzzer_volume","msg_id":1}')
      t1 = time.time()
      while True:
        if cam.cfgdict.has_key("buzzer_volume"):
          break
        if (time.time() - t1) > 10.0:
          cam.msgbusy = 0
          break
      if cam.cfgdict.has_key("buzzer_volume"):
        #print "cam.volume", cam.cfgdict["buzzer_volume"]
        cam.volume = cam.cfgdict["buzzer_volume"]
        if cam.volume <> "mute":
          # Mute Camera
          cam.ChangeSetting("buzzer_volume","mute")
          setok.wait(10)
          cam.msgbusy = 0
      else:
        cam.volume = "low"
    self.lblcam[index].battery = 0
    self.lblcam[index].memory = 0
    self.lblcam[index].adapter = 0
    self.lblcam[index].status = "link"
    self.lblcam[index].bind(battery=self.DrawCamera,adapter=self.DrawCamera,memory=self.DrawCamera)
    #cam.CheckSettings("system_mode")
    threading.Thread(target=self.DoFileTaken, args=(index,), name="%sDoFileTaken" %cam.name).start()
    threading.Thread(target=self.DoStartRecord, args=(index,), name="%sDoStartRecord" %cam.name).start()
    
  def DoDisconnect(self, index):
    cam = self.cam[index]
    name = cam.name
    ilen = len(name)
    print name, ilen
    try:
      if cam.link:
        if self.buzzermute and cam.volume <> "mute":
          setok = cam.setok
          cam.ChangeSetting("buzzer_volume",cam.volume)
          setok.wait(5)
          cam.msgbusy = 0
        time.sleep(1)
        cam.UnlinkCamera()
        cam.quit.wait(5)
    except:
      pass
    cam.socketopen = -1
    cam.quit.set()
    for thread in threading.enumerate():
      if thread.isAlive():
        tname = thread.name
        if len(tname) > ilen and tname[ilen] == name:
          try:
            print "DoDisconnect %d kill %s" %(index, thread.name)
            thread._Thread__stop()
          except:
            pass
    #if cam.socketopen == 0:
    #  cam.socketopen = -1
    try:
      cam.srv.close()
    except:
      pass
    finally:
      cam.quit.set()
    self.quitcam[index].clear()

  def DoStartRecord(self, index):
    while self.quitcam[index].isSet():
      pass
    cam = self.cam[index]
    while not cam.quit.isSet():
      self.recordstart.wait()
      self.lblcam[index].status = 'busy'
      cam.StartRecord(False)
      cam.recording.wait(10)
      if cam.recording.isSet():
        print "\nDoStartRecord", index
        
        threading.Thread(target=self.DoStopRecord, args=(index,), name="DoStopRecord%d" %index).start()
        self.lblcam[index].status = 'link'
        if self.recstart == 0:
          self.firstcam = index
          print "self.firstcam", self.firstcam
        self.recstart += 1
        if self.recstart == self.maxcam:
          self.trec = time.time()
          if self.buzzeronstart:
            self.lblcam[self.firstcam].status = 'beep'
            threading.Thread(target=self.DoBuzzerRing, args=(0,), name="DoBuzzerRing").start()
          self.btnrecord.text = "STOP"
          self.btnrecord.disabled = False
          #threading.Thread(target=self.ButtonText, args=(self.btnrecord,"STOP",1,), name="ButtonText").start()
          #threading.Thread(target=self.DoShowRecord, name="DoShowRecord").start()
          #threading.Thread(target=self.DoShowTime, name="DoShowTime").start()
          self.recordstart.clear()
          self.lblstatus.color = (0,0,0,0)
          self.lblstatus.text = 'REC'
          self.lblrecordtime.text = '00:00:00'
          self.lblrecordtime.color = (1,1,1,1)
          Clock.schedule_interval(self.DoShowTime, 0.5)
          #self.btnconctrl[1]["disabled"] = "False"
          #self.recordtime = self.Second2Time(time.time() - self.trec)
          #self.lblrecordtime.text = "[color=0000ff]%s - %d[/color]\n" %(self.camscenename,self.camsceneshot) + ("[color=ff0000]%s[/color]" %self.recordtime if self.recordtime <> "" else "")
        if cam.preview:
          cam.StartViewfinder()
        self.recordstop.wait()
      else:
        self.lblcam[index].status = "error"
        
  def DoShowTime(self, *args):
    isec = int(time.time() - self.trec)
    self.lblrecordtime.text = self.Second2Time(isec)
    if isec % 2 == 0:
      self.lblstatus.color = (0,0,0,1)
    else:
      self.lblstatus.color = (1,0,0,1)
    
  def DoStopRecord(self, index):
    if self.moveduplicated:
      threading.Thread(target=self.RenameDuplicated, args=(index,),name="RenameDuplicated%d" %index).start()
    self.recordstop.wait()
    self.lblcam[index].status = "busy"
    cam = self.cam[index]
    cam.taken.clear()
    if cam.recording.isSet():
      #if self.buzzeronstop:
      #  cam.msgbusy = 0
      cam.StopRecord()
    print "DoStopRecord", index
    print cam.filetaken
    # stopfirst = self.recstart
    # if stopfirst == 0: #show last record time
      # self.firstcam = index
    self.recstart += 1
    if self.recstart == self.maxcam:
      self.trec = time.time()
      Clock.schedule_interval(self.FlashTimeOn, 0.5)
      self.recordstop.clear()
      self.lblstatus.text = ''
      self.btnsetting.disabled = False
      self.btnmeter.disabled = False
    self.lblcam[index].status = "link"
    
  def FlashTimeOn(self, *args):
    isec = int((time.time() - self.trec) / 0.5)
    if isec % 2 == 0:
      self.lblrecordtime.color = (0,0,0,1)
    else:
      self.lblrecordtime.color = (1,1,1,1)
    
  def FlashTimeOff(self):
    Clock.unschedule(self.FlashTimeOn)
    self.btnrecord.text = 'RECORD'
    self.btnrecord.disabled = False
    self.btnsetting.disabled = False
    self.btnmeter.disabled = False
    #self.lblrecordtime.text = '00:00:00'
    self.lblrecordtime.color =(0.25,0.25,0.25,1)
    self.lblstatus.color = (0,0,0,0)
    
  def Buzzer(self, btnbuzzer):
    self.lblcam[self.firstcam].status = 'beep'
    threading.Thread(target=self.DoBuzzerRing, args=(2,),name="DoBuzzerRing").start()
    
  def DoBuzzerRing(self, type): #0-start, 1-stop, 2-manual
    print "DoBuzzerRing", self.lblcam[self.firstcam].status, self.firstcam
    
    #self.DoDrawCamera(self.lblcam[self.firstcam])
    cam = self.cam[self.firstcam]
    cam.Buzzer()
    if type == 1 and self.buzzeronstop:
      cam.getexp.wait()
      Clock.unschedule(self.DoShowTime)
      self.trec = 0
      self.recordstart.clear()
      self.recordstop.set()
    else:
      cam.getexp.wait(5)
    self.lblcam[self.firstcam].status = 'link'
    
  def DoFindCamera(self):
    cam = self.cam[self.firstcam]
    setok = cam.setok
    seterror = cam.seterror
    cam.ChangeSetting("buzzer_ring","on")
    t = time.time()
    setok.wait(5)
    if setok.isSet():
      if time.time() - t < 2.0:
        time.sleep(1)
    cam.ChangeSetting("buzzer_ring","off")
  
  def Meter(self):
    i = 0
    for lbl in self.lblcam:
      if lbl.status == 'link':
        lbl.status = 'busy'
        threading.Thread(target=self.DoMeter, args=(i,),name="DoMeter%d" %i).start()
      i += 1
      
  def DoMeter(self, index):
    cam = self.cam[index]
    getexp = cam.getexp
    cam.GetAEInfo()
    getexp.wait()
    if cam.asid <> "":
      self.lblcam[index].status = 'link'
      print 'exposure %s' %cam.asid
    else:
      self.lblcam[index].status = 'error'
   
  def ButtonBackground(self, button, type, imagefilepath):
    if type == "background_normal":
      button.background_normal = imagefilepath
    elif type == "background_down":
      button.background_down = imagefilepath
    elif type == "background_disabled_normal":
      button.background_disabled_normal = imagefilepath
    elif type == "background_disabled_down":
      button.background_disabled_normal = imagefilepath
  
  def Record(self, btnrecord):
    self.recstart = 0
    self.rename = 0
    self.ftaken = 0
    if btnrecord.text == "RECORD":
      self.firstcam = 0
      self.recordstop.clear()
      self.recordstart.set()
      btnrecord.text = "START"
      btnrecord.disabled = True
      self.btnsetting.disabled = True
      self.btnmeter.disabled = True
    elif btnrecord.text == "STOP":
      btnrecord.disabled = True
      if self.buzzeronstop:
        self.lblcam[self.firstcam].status = 'beep'
        threading.Thread(target=self.DoBuzzerRing, args=(1,),name="DoBuzzerRing").start()
      else:
        Clock.unschedule(self.DoShowTime)
        self.trec = 0
        self.recordstart.clear()
        self.recordstop.set()

  def ConfigPopupOpen(self, btn, text):
    if text in ("<",">"):
      return
    if btn == self.btnsetting:
      btn.text = "<"
      print "btnsetting",text
      if text == "Advanced":
        popup = AdvancedPopup(title='Camera Advanced Config', size_hint=(0.8, 0.8), size=self.size)
        popup.bind(on_dismiss=self.AdvancedPopupApply)
        popup.apply = False
        popup.scenename = self.camscenename
        popup.sceneshot = self.camsceneshot
        popup.autorename = self.autorename
        popup.moveduplicated = self.moveduplicated
        popup.buzzeronstart = self.buzzeronstart
        popup.buzzeronstop = self.buzzeronstop
        popup.buzzermute = self.buzzermute
        popup.photomode = self.photomode
        popup.open()
      else: #camera ip setting
        index = int(text.split(" ")[1]) - 1
        self.stopdetect.set()
        camcfg = {}
        camcfg["camera"] = self.cfglist[index]["camera"]
        camcfg["ip"] = self.cfglist[index]["ip"]
        camcfg["name"] = self.cfglist[index]["name"]
        camcfg["enabled"] = self.cfglist[index]["enabled"]
        camcfg["preview"] = self.cfglist[index]["preview"]
        popup = ConfigPopup(title='Camera Connection Config', size_hint=(0.8, 0.6), size=self.size, cfg=camcfg, index=index)
        popup.bind(on_dismiss=self.ConfigPopupApply)
        popup.apply = False
        popup.index = index
        popup.open()
    if btn == self.btnmeter:
      btn.text = ">"
      print "btnmeter",text
      if text == "Metering":
        self.Meter()
      elif text == "M.Exposure":
        popup = ManualExposurePopup(title='Manual Exposure Setting', size_hint=(0.8, 0.5), size=self.size)
        popup.bind(on_dismiss=self.ManualExposurePopupApply)
        popup.apply = False
        popup.shutter = "1 / 60s"
        popup.iso = "ISO 100"
        popup.open()
        pass
      else: #camera option setting
        index = int(text.split(" ")[1]) - 1
        popup = CameraSettingPopup(title='Camera Options', size_hint=(0.8, 0.8), size=self.size, asid=self.cam[index].asid, index=index)
        popup.bind(on_dismiss=self.CameraSettingPopupApply)
        popup.apply = False
        popup.index = index
        popup.open()
        pass

  def ManualExposurePopupApply(self, popup):
    #1/ 30s: 1012
    #1/ 60s: 1140
    #1/100s: 1234
    #ISO  100: 448 XXXX 0 4096
    #ISO  200: 384 XXXX 0 4096
    #ISO  400: 320 XXXX 0 4096
    #ISO  800: 256 XXXX 0 4096
    #ISO 1600: 192 XXXX 0 4906
    #ISO 3200: 192 XXXX 0 8192
    if popup.apply:
      self.lblexposure.text = 'manual'
      self.lblshutter.text = popup.shutter.replace(' ','')
      self.lbliso.text = popup.iso.replace('ISO ','')
      
      self.shutter = popup.shutter
      self.iso = popup.iso
      i = 0
      if popup.iso == "ISO 100":
        a = 448
        d = 4096
      elif popup.iso == "ISO 200":
        a = 384
        d = 4096
      elif popup.iso == "ISO 400":
        a = 320
        d = 4096
      elif popup.iso == "ISO 800":
        a = 256
        d = 4096
      elif popup.iso == "ISO 1600":
        a = 192
        d = 4096
      elif popup.iso == "ISO 3200":
        a = 192
        d = 8192
      
      if popup.shutter == "1 / 30s":
        s = 1012
      elif popup.shutter == "1 / 60s":
        s = 1140
      elif popup.shutter == "1 / 100s":
        s = 1234
        
      asid = '%d %d %d %d' %(a,s,i,d)
      #print 'Manual Exposure %s' %asid
      index = 0
      #display = '%s %s' %(popup.shutter, popup.iso)
      for cam in self.cam:
        if cam.link:
          self.lblcam[index].status = 'busy'
          threading.Thread(target=self.DoSetExposure, args=(index,asid,), name="DoThrSetExposure%d" %index).start()
        index += 1
          
  def CameraSettingPopupApply(self, popup):
    if popup.apply:
      print 'CameraSettingPopupApply', popup.index
      cam = self.cam[popup.index]
      #print "sync cam %d to all %s" %(cam.number, cam.asid)
      if popup.syncall:
        self.lblexposure.text = 'sync'
        self.lblshutter.text = 'auto'
        self.lbliso.text = 'auto'
        asid = cam.asid
        index = 0
        for cam in self.cam:
          if cam.link:
            self.lblcam[index].status = 'busy'
            threading.Thread(target=self.DoSetExposure, args=(index,asid,),name="DoThrSetExposure%d" %index).start()
          index += 1
        return
      #print "format cam %d" %cam.number
      if popup.format:
        self.lblcam[popup.index].status = 'busy'
        threading.Thread(target=self.DoCamFormatWait, args = (popup.index,),name="DoCamFormatWait%d" %popup.index).start()
        return
      #print "restore cam %d" %cam.number
      if popup.reboot:
        self.lblcam[popup.index].status = 'beep'
        threading.Thread(target=self.DoCamRebootWait, args = (popup.index,),name="DoCamRebootWait%d" %popup.index).start()
        return
      #print "restore cam %d" %cam.number
      if popup.restore:
        self.lblcam[popup.index].status = 'beep'
        threading.Thread(target=self.DoRestoreFactory, args = (popup.index,),name="DoRestoreFactory%d" %popup.index).start()
        return
  
  def DoRestoreFactory(self, index):
    self.cam[index].RestoreFactory()
    time.sleep(5)
    ip = self.cam[index].ip
    self.linked -= 1
    self.lblcam[index].status = 'disable'
    self.lblcam[index].unbind(size=self.DrawCamera,pos=self.DrawCamera,status=self.DrawCamera,battery=self.DrawCamera,adapter=self.DrawCamera,memory=self.DrawCamera)
    self.btnrecord.disabled = True
    self.btnmeter.disabled = True
    self.DoDisconnect(index)
    time.sleep(60)
    cam = XCamera()
    cam.ip = ip
    cam.index = index
    self.cam[index] = cam
    cam.enabled = True
    self.lblcam[index].status = 'enable'
    threading.Thread(target=self.DoDetectCam, args = (index,),name="%sDoDetectCam" %cam.ip).start()
  
  def DoCamFormatWait(self, index):
    cam = self.cam[index]
    setok = cam.setok
    cam.FormatCard()
    setok.wait()
    if cam.seterror.isSet():
      self.lblcam[index].status = 'error'
    else:
      self.lblcam[index].status = 'link'
  
  def DoCamRebootWait(self, index):
    self.cam[index].Reboot()
    time.sleep(5)
    ip = self.cam[index].ip
    self.linked -= 1
    self.lblcam[index].status = 'disable'
    self.lblcam[index].unbind(size=self.DrawCamera,pos=self.DrawCamera,status=self.DrawCamera,battery=self.DrawCamera,adapter=self.DrawCamera,memory=self.DrawCamera)
    self.btnrecord.disabled = True
    self.btnmeter.disabled = True
    self.DoDisconnect(index)
    time.sleep(30)
    cam = XCamera()
    cam.ip = ip
    cam.index = index
    self.cam[index] = cam
    cam.enabled = True
    self.lblcam[index].status = 'enable'
    threading.Thread(target=self.DoDetectCam, args = (index,),name="%sDoDetectCam" %cam.ip).start()
   
  def DoSetExposure(self, index, asid):
    getexp = self.cam[index].getexp
    self.cam[index].SetAEInfo(asid)
    getexp.wait()
    if self.cam[index].asid <> "":
      self.lblcam[index].status = 'link'
    else:
      self.lblcam[index].status = 'error'
  
  def RefreshOption(self):
    print 'RefreshOption'
    option = []
    i = 0
    for cam in self.cam:
      i += 1
      if cam.link:
        option.append('Option %d' %i)

    option.append('Metering')
    option.append('M.Exposure')
    print 'new options: %s' %option
    self.btnmeter.values = option
  
  def ConfigPopupApply(self, popup):
    if popup.apply:
      index = popup.index
      oldcfg = dict(self.cfglist[index])
      self.cfglist[index] = popup.cfg
      self.WriteConfig()
      self.cfglist = self.ReadConfig()
      newcfg = dict(self.cfglist[index])
      print "index %d old config: %s" %(index, oldcfg)
      print "index %d new config: %s" %(index, newcfg)
      if oldcfg["ip"] <> newcfg["ip"] or oldcfg["enabled"] <> newcfg["enabled"]:
        if oldcfg["enabled"] == 1:
          if self.cam[index].link:
            self.linked -= 1
          self.maxcam -= 1
        if newcfg["enabled"] == 1:
          self.maxcam += 1
        cam = self.cam[index]
        ilen = len(cam.ip)
        for thread in threading.enumerate():
          if thread.isAlive() and thread.name[0:ilen] == cam.ip:
            self.quitcam[index].set()
            break
        self.lblcam[index].status = 'disable'
        self.lblcam[index].unbind(size=self.DrawCamera,pos=self.DrawCamera,status=self.DrawCamera,battery=self.DrawCamera,adapter=self.DrawCamera,memory=self.DrawCamera)
       
        if cam.link:
          threading.Thread(target=self.DoDisconnect, args = (index,),name="DoDisconnect%d" %index).start()
        
        if self.linked == self.maxcam and self.maxcam > 0:
          self.btnrecord.disabled = False
          self.btnmeter.disabled = False
          self.RefreshOption()
        else:
          self.btnrecord.disabled = True
          self.btnmeter.disabled = True
        cam = XCamera()
        cam.index = index
        self.cam[index] = cam
        if newcfg["ip"] <> "" and newcfg["enabled"] == 1:
          cam.ip = newcfg["ip"]
          cam.enabled = True
          self.lblcam[index].status = 'enable'
          threading.Thread(target=self.DoDetectCam, args = (index,),name="%sDoDetectCam" %cam.ip).start()
      else:
        if self.cam[index].link:
          if newcfg["preview"] == 0:
            self.cam[index].StopViewfinder()
          else:
            self.cam[index].StartViewfinder()
  
  def StringFilter(self, strin):
    filter = list(string.ascii_letters + string.digits)
    strout = ""
    for i in range(len(strin)):
      if strin[i] in filter:
        strout += strin[i]
    if strout == "":
      strout = "scene"
    return strout[0:20]
    
  def AdvancedPopupApply(self, popup):
    if popup.apply:
      # Different Scene Name Reset Counter
      if self.camscenename <> self.StringFilter(popup.scenename):
        self.lblscenename.text = self.StringFilter(popup.scenename)
        #self.lblscenename.text = self.camscenename
        self.lblsceneshot.text = '01'
        #self.lblsceneshot.text = "No.%d" %self.camsceneshot
      self.autorename = popup.autorename
      self.moveduplicated = popup.moveduplicated
      self.buzzeronstart = popup.buzzeronstart
      self.buzzeronstop = popup.buzzeronstop
      self.buzzermute = popup.buzzermute
      self.photomode = popup.photomode
      self.WriteConfig()
      
  def Photo(self):
    self.tphoto= threading.Thread(target=self.DoPhoto)
    self.tphoto.setName('DoPhoto')
    self.tphoto.start()
  
  def Second2Time(self, seconds):
    seconds = int(seconds)
    rectime = "00:00:00"
    ihour = 0
    iminute = 0
    isecond = 0
    if seconds <> 0:
      ihour = seconds / 3600
      seconds = seconds % 3600
      iminute = seconds / 60
      isecond = seconds % 60
      rectime = "%02d:%02d:%02d" %(ihour, iminute, isecond)
    return rectime
    
  def DoPhoto(self):
    i = 0
    #self.current_screen.ids.btnpreview.state = "down"
    self.current_screen.ids.btnpreview.text = "Taking Photo"
    for cam in self.cam:
      cam.TakePhoto()
    for cam in self.cam:
      while cam.cambusy:
        i = i % 3 + 1
        time.sleep(0.5)
        self.current_screen.ids.btnpreview.text = "Taking Photo %s" %("." * i)
    #self.current_screen.ids.btnpreview.state = "normal"
    self.current_screen.ids.btnpreview.text = "Take Photo"
  
  def DoPreview(self):
    for cam in self.cam:
      if cam.link and cam.preview:
        cam.StartViewfinder()
        #time.sleep(1)
        #cam.msgbusy = 0
  
  def DoWifi(self, index):
    print "DoWifi Start %d" %index
    wifioff = self.cam[index].wifioff
    wifioff.wait()
    threading.Thread(target=self.DoDisconnect, args=(45,), name="DoDisconnect%d" %index).start()
    wifioff.clear()
    
  def DoFileTaken(self, index):
    while self.quitcam[index].isSet():
      pass
    print 'Start DoFileTaken %d' %index
    cam = self.cam[index]
    # check resolution
    cam.CheckSettings("video_resolution")
    # check battery
    cam.CheckBatteryState()
    # check card usage
    cam.CardUsage()
    
    aidx = self.lblcam[index].adapter
    bidx = self.lblcam[index].battery
    midx = self.lblcam[index].memory
    if cam.token <> 0:
      self.linked += 1
    print 'link %d / %d' %(self.linked,self.maxcam)
    if self.linked == self.maxcam:
      self.btnrecord.disabled = False
      self.btnmeter.disabled = False
      self.RefreshOption()
    while not cam.quit.isSet():
      cam.taken.wait(1)
      if cam.status.has_key("battery"):
        if self.lblcam[index].battery <> int(cam.status["battery"]):
          self.lblcam[index].battery = int(cam.status["battery"])
          print 'battery %d' %self.lblcam[index].battery
      if cam.status.has_key("adapter_status"):
        if self.lblcam[index].adapter <> int(cam.status["adapter_status"]):
          self.lblcam[index].adapter = int(cam.status["adapter_status"])
          print 'adapter %d' %self.lblcam[index].adapter
      if midx <> cam.memory:
        midx = cam.memory
        self.lblcam[index].memory = cam.memory
        print 'memory %d' %self.lblcam[index].memory
      if cam.taken.isSet():
        
        self.renlist[index] = dict()
        cam.taken.clear()
        if cam.filetaken <> "":
          if cam.preview:
            cam.StartViewfinder()
          fileinfo = {"index":index,"old":cam.filetaken,"new":"","ok":0}
          self.renlist[index]=dict(fileinfo)
          if self.autorename:
            threading.Thread(target=self.RenameVideoFiles, args=(index,), name="RenameVideoFiles%d" %index).start()
          else:
            self.lblrecordtime.text = ''
        self.ftaken += 1
        if self.ftaken == self.maxcam and not self.autorename:
          self.FlashTimeOff()
    print 'Quit DoFileTaken %d' %index
    
  def RenameVideoFiles(self, index):
    self.lblcam[index].status = "busy"
    cam = self.cam[index]
    date = time.strftime('%Y%m%d')
    camletter = list(string.ascii_lowercase)
    failure = False
    old = cam.status["video_record_complete"]
    #cam.SendMsg('{"msg_id":1026,"param":"%s"}' %old.replace('.mp4','.THM')) 
    print "old file name:", old
    new = '/tmp/fuse_d/DCIM/%s/%s-%s-%s-%03d.mp4' %(self.camscenename,date,self.camscenename,camletter[index],self.camsceneshot)
    print "new file name:", new
    fileinfo = dict(self.renlist[index])
    fileinfo["new"] = new
    ctelnet = XCameraTelnet(ip=cam.ip,username="")
    commit = ctelnet.commit
    ctelnet.Rename(old, new)
    while True:
      commit.wait(1)
      if commit.isSet():
        fileinfo["ok"] = 1
        cam.SendMsg('{"msg_id":1026,"param":"%s"}' %new)
        self.lblcam[index].status = "link"
        break
      elif ctelnet.failure:
        failure = failure or ctelnet.failure
        self.lblcam[index].status = "error"
        fileinfo["ok"] = 0
        break
    cam.status["video_record_complete"] = ""
    cam.dirtaken = ""
    cam.filetaken = ""
    self.renlist[index] = dict(fileinfo)
    self.rename += 1
    self.renfail = False
    if self.rename == self.maxcam:
      self.FlashTimeOff()
      for item in self.renlist:
        if item.has_key('ok'):
          if item['ok'] == 0:
            self.renfail = True
            break
      self.trec = time.time()
      self.lblsceneshot.color = (0,0,0,1)
      if self.renfail:
        Clock.schedule_interval(self.FlashShotOn, 0.5)
      else:       
        self.lblsceneshot.text = '%02d' %(self.camsceneshot + 1)
        self.WriteConfig()
        print 'do FlashShotOn'
        Clock.schedule_interval(self.FlashShotOn, 0.5)
        print 'after FlashShotOn'
        threading.Thread(target=self.FlashShotOff, name="FlashShotOff").start()
  
  def RenameDuplicated(self, index):
    time.sleep(3)
    cam = self.cam[index]
    date = time.strftime('%Y%m%d')
    camletter = list(string.ascii_lowercase)
    failure = False
    new = '/tmp/fuse_d/DCIM/%s/%s-%s-%02d%s.mp4' %(self.camscenename,date,self.camscenename,camletter[index],self.camsceneshot)
    stime = time.strftime('%H%M%S')
    duplicated = '/tmp/fuse_d/trashbin/%s-%s-%s-%02d%s.mp4' %(date,stime,self.camscenename,self.camsceneshot,camletter[index])
    ctelnet = XCameraTelnet(ip=cam.ip,username="")
    ctelnet.Rename(new, duplicated)
  
  def FlashShotOff(self):
    i = time.time()
    while ((time.time() - i) < 5.0):
      pass
    Clock.unschedule(self.FlashShotOn)
    self.lblsceneshot.color = (1,1,1,1)
  
  def FlashShotOn(self, *args):
    
    isec = int((time.time() - self.trec) / 0.5) #refresh 0.5 seconds
    print "FlashShotOn args %s" %args
    if isec % 2 == 0:
      self.lblsceneshot.color = (0,0,0,1)
    else:
      if self.renfail:
        self.lblsceneshot.color = (1,0,0,1)
      else:
        self.lblsceneshot.color = (0,1,0,1)
      
  def ReadConfig(self):
    self.cameras = 7 #default 6 cameras
    cfgfile = __file__.replace(basename(__file__), "xdata/xcamera.cfg")
    initstr = '''
    {
      "camera": "0",
      "ip": "",
      "enabled": 0,
      "name": "",
      "preview": 0
    }
    '''
    r = []
    try:
      with open(cfgfile) as file:
        readstr = file.read()
        #print "readstr", readstr
        cfg = json.loads(readstr)
      if cfg.has_key("scenename"):
        self.camscenename = cfg["scenename"]
      else:
        self.camscenename = 'PonerineX'
      if cfg.has_key("sceneshot"):
        self.camsceneshot = cfg["sceneshot"]
      else:
        self.camsceneshot = 1
      if self.camsceneshot <= 0:
        self.camsceneshot = 1
      if cfg.has_key("autorename"):
        self.autorename = cfg["autorename"] == 1
      else:
        self.autorename = False
      if cfg.has_key("moveduplicated"):
        self.moveduplicated = cfg["moveduplicated"] == 1
      else:
        self.moveduplicated = False
      if cfg.has_key("buzzeronstart"):
        self.buzzeronstart = cfg["buzzeronstart"] == 1
      else:
        self.buzzeronstart = False
      if cfg.has_key("buzzeronstop"):
        self.buzzeronstop = cfg["buzzeronstop"] == 1
      else:
        self.buzzeronstop = False
      if cfg.has_key("buzzermute"):
        self.buzzermute = cfg["buzzermute"] == 1
      else:
        self.buzzermute = False
      if cfg.has_key("photomode"):
        self.photomode = cfg["photomode"] == 1
      else:
        self.photomode = False
      if cfg.has_key("resolution"):
        self.camresolution = cfg["resolution"]
      else:
        self.camresolution = "1600x1200"
      if cfg.has_key("framerate"):
        self.camframe = cfg["framerate"]
      else:
        self.camframe = "60P"
      if cfg.has_key("bitrate"):
        self.cambitrate = cfg["bitrate"]
      else:
        self.cambitrate = "35M"
      if cfg.has_key("aspect"):
        self.camaspect = cfg["aspect"]
      else:
        self.camaspect = "4:3"
      if cfg.has_key("meter"):
        self.cammetermode = cfg["meter"]
      else:
        self.cammetermode = "average"
      if cfg.has_key("exposure"):
        self.camexposure = cfg["exposure"]
      else:
        self.camexposure = "auto"
      if cfg.has_key("shutterspeed"):
        self.camshutter = cfg["shutterspeed"]
      else:
        self.camshutter = "auto"
      if cfg.has_key("iso"):
        self.camiso = cfg["iso"]
      else:
        self.camiso = "auto"
      if cfg.has_key("config"):
        for item in cfg["config"]:
          cfginit = json.loads(initstr)
          cfginit.update(item)
          r.append(cfginit)
        print "config read len %d of %d" %(len(r), self.cameras)
        if len(r) < self.cameras:
          for i in range(len(r), self.cameras):
            cfginit = json.loads(initstr)
            cfginit["camera"] = str(i+1)
            r.append(cfginit)
      else:
        for i in range(self.cameras):
          cfginit = json.loads(initstr)
          cfginit["camera"] = str(i+1)
          r.append(cfginit)
    except StandardError:
      print "read error"
      for i in range(self.cameras):
        cfginit = json.loads(initstr)
        cfginit["camera"] = str(i+1)
        r.append(cfginit)
      self.camscenename = "scene"
      self.camsceneshot = 1
      self.camresolution = '1600x1200'
      self.camframe = '60P'
      self.cambitrate = '35M'
      self.camaspect = '4:3'
      self.cammetermode = 'average'
      self.camexposure = 'auto'
      self.camshutter = 'auto'
      self.camiso = 'auto'
      self.autorename = False
      self.moveduplicated = False
      self.buzzeronstart = False
      self.buzzeronstop = False
      self.buzzermute = False
      self.photomode = False
      
    if self.inited:
      pass
    return r

  def WriteConfig(self):
    cfg = {}
    cfg["scenename"] = self.camscenename
    cfg["sceneshot"] = self.camsceneshot
    cfg["resolution"] = self.camresolution
    cfg["framerate"] = self.camframe 
    cfg["bitrate"] = self.cambitrate
    cfg["aspect"] = self.camaspect
    cfg["meter"] = self.cammetermode
    cfg["exposure"] = 'auto' # self.camexposure
    cfg["shutterspeed"] = 'auto' #self.camshutter
    cfg["iso"] = 'auto' #self.camiso
    cfg["autorename"] = int(self.autorename)
    cfg["moveduplicated"] = int(self.moveduplicated)
    cfg["buzzeronstart"] = int(self.buzzeronstart)
    cfg["buzzeronstop"] = int(self.buzzeronstop)
    cfg["buzzermute"] = int(self.buzzermute)
    cfg["photomode"] = int(self.photomode)
    
    cfg["config"] = self.cfglist
    cfgfile = __file__.replace(basename(__file__), "xdata/xcamera.cfg")
    try:
      with open(cfgfile,'w') as file:
        file.write(json.dumps(cfg, indent=2))
    except StandardError:
      pass

class XPonerineApp(App):
  sysname = platform.system()
  if sysname == "Windows":
    kivy.resources.resource_add_path('c:/Windows/Fonts')
  elif sysname == "Darwin":
    pass
  elif sysname == "Linux":
    kivy.resources.resource_add_path('/system/fonts')

  #DroidSansFallback = kivy.resources.resource_find('DroidSansFallback.ttf')
  #RobotoThin = kivy.resources.resource_find('Roboto-Thin.ttf')
  version = __version__

  def build(self):
    self.appexit = threading.Event()
    evt = []
    evt.append(self.appexit)
    xponerine = XPonerine(evt)
    xponerine.duration = 0.7

    xponerine.screen = [XRecordScreen(name="mconnect")]
    xponerine.switch_to(xponerine.screen[0])
    xponerine.InitControls()
    xponerine.DetectCam()
    xponerine.inited = True
    return xponerine
    
  def on_pause(self):
    return True
    
  def on_resume(self):
    pass
    
  def on_stop(self):
    self.appexit.set()
    for thread in threading.enumerate():
      if thread.isAlive():
        print "APP.on_stop kill: %s" %thread.name
        try:
          thread._Thread__stop()
        except:
          pass

if __name__ == '__main__':
  XPonerineApp().run() 
