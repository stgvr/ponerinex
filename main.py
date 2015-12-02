import kivy
# Ponerine.X Multi-Cam Controller for XueTan
kivy.require('1.9.0')

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition, FallOutTransition, RiseInTransition
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.spinner import Spinner

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
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
Builder.load_file('xdata/xcfg_advanced.kv')
Builder.load_file('xdata/xcfg_cameras.kv')

Clock.max_iteration = 100
__version__='0.0.7'

class LSpinner(Spinner):
  pass
  
class RECButton(Button):
  pass

class RSpinner(Spinner):
  pass

class RLabel(Label):
  name = StringProperty()

class CButton(Button):
  pass

class CLabel(AnchorLayout):
  adapter = NumericProperty()
  battery = NumericProperty()
  memory = NumericProperty()
  text = StringProperty()
  status = OptionProperty("disable", options=["disable","enable","on","off","link","busy","beep","error"])

class CStatus(GridLayout):
  enabled = NumericProperty()
  number = NumericProperty()
  name = StringProperty()
  preview = NumericProperty()
  ipaddress = StringProperty()

class SLabel(GridLayout):
  fixcolor = BooleanProperty(False)
  index = NumericProperty()
  option = ListProperty(["disable","enable"])
  
class XRecordScreen(Screen):
  pass

class XAppTitle(BoxLayout):
  pass

class XCamInfo(GridLayout):
  pass

class XCamControl(BoxLayout):
  pass

class XCfgAdvanced(BoxLayout):
  scenename = StringProperty()
  sceneshot = NumericProperty()
  autorename = NumericProperty()
  moveduplicated = NumericProperty()
  buzzeronstart = NumericProperty()
  buzzeronstop = NumericProperty()
  buzzervolume = NumericProperty()
  ledonstart = NumericProperty()
  ledonstop = NumericProperty()
  metermode = NumericProperty()
  systemmode = NumericProperty()

class XCfgCameras(BoxLayout):
  network = StringProperty()
  cfg = ObjectProperty()
  
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
    
    self.btnredraw = self.xapptitle.children[6].children[0]
    self.btnredraw.bind(on_release=self.RedrawAll)
    self.lblapptitle = self.xapptitle.children[6].children[2]
    
    self.btnsetting = self.xcamcontrol.children[idx_button].children[2]
    #self.btnsetting.bind(text=self.ConfigPopupOpen)
    self.btnsetting.bind(on_release=self.XCfgAdvancedOpen)
    self.btnrecord = self.xcamcontrol.children[idx_button].children[1]
    self.btnrecord.bind(on_release=self.Record)
    if self.systemmode == 0:
      self.btnrecord.text = 'RECORD'
    elif self.systemmode == 1:
      self.btnrecord.text = 'PHOTO'
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
    self.lblmetermode.text = self.meterlist[self.cammetermode]
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
        lbl.bind(size=self.DrawCamera,pos=self.DrawCamera,status=self.DrawCamera)
  
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
    Clock.schedule_once(partial(self.DoDrawCamera,args[0]))
  
  def DoDrawCamera(self, clabel, *args):
    lsize = clabel.size
    lpos = clabel.pos
    lstatus = clabel.status
    lbltext = clabel.children[1]
    imgcanvas = clabel.children[0]
    midx = int(clabel.memory/2)
    bidx = int(clabel.battery/2)
    apt = clabel.adapter
    #options=["disable","enable","on","link","busy","error"]
    if lstatus == "disable":
      r=1;g=1;b=1;a=0.05
    elif lstatus in ("enable","beep"): #blue
      r=0;g=0.75;b=1;a=0.8
    elif lstatus == "on": #green
      r=0;g=1;b=0;a=0.8
    elif lstatus == "link": #white
      r=1;g=1;b=1;a=0.5
    elif lstatus == "busy":
      r=1;g=1;b=0.25;a=0.8
    elif lstatus in ("error","off"):
      r=1;g=0;b=0;a=0.8
    if a >= 0.5:
      lbltext.color = (r,g,b,0.8)
    else:
      lbltext.color = (r,g,b,a)
    imgcanvas.canvas.clear()
    #draw status circle
    with imgcanvas.canvas:
      Color(r,g,b,a)
      Rectangle(size=lsize,pos=lpos,source='ximage/camstatus.png')
    if lstatus in ("disable","enable","on","off"):
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
    #print 'LabelText',lbl.name,args
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
      i = 0
      for m in self.meterlist:
        if m == lbl.text:
          self.cammetermode = i
        i += 1
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
    self.autorename = 0
    self.moveduplicated = 0
    self.buzzeronstart = 0
    self.buzzeronstop = 0
    self.buzzervolume = 0
    self.ledonstart = 0
    self.ledonstop = 0
    self.systemmode = 0
    #camera label settings
    self.camscenename = ''#'PonerineX'
    self.camsceneshot = ''#1
    self.camstatus = ''#'REC'
    self.camrecordtime = '00:00:00'#'00:00:00'
    self.camresolution = ''#'1600x1200'
    self.camframe = ''#'60P'
    self.cambitrate = ''#'35M'
    self.camaspect = ''#'4:3'
    self.meterlist = ['average','center','spot']
    self.cammetermode = 0#'average'
    self.camexposure = ''#'auto'
    self.camshutter = ''#'1/60s'
    self.camiso = ''#'800'
    
    self.shutter = '1 / 60s'
    self.iso = 'ISO 100'
    
    self.linked = 0
    self.recstart = 0
    self.reccam = 0
    self.maxcam = 0
    
    self.cfglist = self.ReadConfig()
    self.recordstart = threading.Event()
    self.recordstop = threading.Event()
    
    sysname = platform.system()
    if sysname == "Windows":
      Window.size = (600,960) #(560,896) #(560,800) #(720,800)
      #Window.borderless = '1'
    elif sysname == "Darwin":
      Window.size = (520,700)
    elif sysname == "Linux":
      if platform.linux_distribution()[0] == "Ubuntu":
        Window.size = (560,800)
  
  def CheckIPAddress(self, ipaddress, segmentlength=4):
    segment = ipaddress.split('.')
    if len(segment) == segmentlength:
      for i in range(segmentlength):
        if segment[i].isdigit():
          if int(segment[i]) > 255:
            return False
        else:
          return False
      return True
    else:
      return False
      
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
      if self.CheckIPAddress(self.cfglist[i]["ip"]) and self.cfglist[i]["enabled"] == 1:
        cam.enabled = True
        cam.ip = self.cfglist[i]["ip"]
        cam.preview = self.cfglist[i]["preview"] == 1
        self.maxcam += 1
        self.lblcam[i].status = 'enable'
      else:
        self.lblcam[i].status = 'disable'
      threading.Thread(target=self.DoDetectCam, name="%sDoDetectCam" %cam.ip, args=(i,)).start()
      self.cam.append(cam)
      self.renlist.append({})
    Clock.unschedule(self.XCfgAdvancedDraw)
    Clock.schedule_once(self.XCfgAdvancedDraw)
    Clock.unschedule(self.XCfgCamerasDraw)
    Clock.schedule_once(self.XCfgCamerasDraw)
    
  def DoDetectCam(self, index):
    while self.quitcam[index].isSet():
      pass
    print 'Start DoDetectCam %d %s' %(index,self.lblcam[index].status)
    bind = False
    # slow down detect for first time
    while self.inited == False:
      bind = True
      time.sleep(1)
    self.DrawCamera(self.lblcam[index])
    self.lblcam[index].bind(size=self.DrawCamera,pos=self.DrawCamera,status=self.DrawCamera)
    if self.lblcam[index].status == "disable":
      return
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
      t1 = time.time()
      while (time.time() - t1) < timewait:
        self.quitcam[index].wait(0.5)
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
      #print "index %d ip %s port %d retry %d open %d" %(index, self.cam[index].ip, port[retry], retry, open)
      if open == 0:
        self.lblcam[index].status = "on"
        time.sleep(1)
        threading.Thread(target=self.DoConnect, name="%dDoConnect" %index, args=(index,)).start()
        return
      elif retry == 0:
        if timewait < 10:
          timewait += 1
        self.lblcam[index].status = "off"

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
    
    #check app status
    cam.CheckSetting("app_status")
    recstatus = ""
    t1 = time.time()
    while True:
      time.sleep(0.5)
      if cam.cfgdict.has_key("app_status"):
        recstatus = cam.cfgdict["app_status"]
        break
      if (time.time() - t1) > 10.0:
        break
    if recstatus in ("record","recording"):
      self.reccam += 1
      self.btnsetting.disabled = True
      self.btnrecord.text = 'START'
      self.btnrecord.disabled = True
      self.btnmeter.disabled = True
    else:
      # sync time
      setok = cam.setok
      #offset index*12=0,10,20,30,40,50,60
      t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()+ index * 10))
      print "time offset: %s" %t
      cam.ChangeSetting("camera_clock", t)
      setok.wait(5)
      cam.msgbusy = 0
      #set meter mode
      cam.CheckSetting("meter_mode")
      #check preview
      cam.CheckSetting("preview_status")
      #check led mod
      cam.CheckSetting("led_mode")
      # set buzzer volume
      if self.buzzervolume != 0:
        opt = ['remain','high','low','mute']
        cam.CheckSetting("buzzer_volume")
        t1 = time.time()
        while True:
          if cam.cfgdict.has_key("buzzer_volume"):
            break
          if (time.time() - t1) > 10.0:
            cam.msgbusy = 0
            break
        if cam.cfgdict.has_key("buzzer_volume"):
          if cam.cfgdict["buzzer_volume"] <> opt[self.buzzervolume]:
            cam.ChangeSetting("buzzer_volume",opt[self.buzzervolume])
            setok.wait(5)
            cam.msgbusy = 0
        else:
          cam.ChangeSetting("buzzer_volume",opt[self.buzzervolume])
          setok.wait(5)
          cam.msgbusy = 0
      # set led mode
      if cam.cfgdict.has_key("meter_mode"):
        if cam.cfgdict["meter_mode"] != self.meterlist[self.cammetermode]:
          cam.ChangeSetting("meter_mode",self.meterlist[self.cammetermode])
          setok.wait(5)
          cam.msgbusy = 0
      else:
        cam.ChangeSetting("meter_mode",self.meterlist[self.cammetermode])
        setok.wait(5)
        cam.msgbusy = 0
      # set preview status
      if cam.cfgdict.has_key("preview_status"):
        #print 'cam.cfgdict.has_key("preview_status")'
        if cam.preview:
          if cam.cfgdict["preview_status"] == "off":
            cam.ChangeSetting("preview_status","on")
            setok.wait(5)
            cam.msgbusy = 0
          #cam.StartViewfinder()
        else:
          if cam.cfgdict["preview_status"] == "on":
            cam.StopViewfinder()
            cam.ChangeSetting("preview_status","off")
            setok.wait(5)
            cam.msgbusy = 0
      else:
        #print 'cam.cfgdict.has_no_key("preview_status")'
        if cam.preview:
          cam.StopViewfinder()
          cam.ChangeSetting("preview_status","on")
          setok.wait(5)
          cam.msgbusy = 0
          #cam.StartViewfinder()
        else:
          cam.StopViewfinder()
          cam.ChangeSetting("preview_status","off")
          setok.wait(5)
          cam.msgbusy = 0
    self.lblcam[index].battery = 0
    self.lblcam[index].memory = 0
    self.lblcam[index].adapter = 0
    self.lblcam[index].status = "link"
    self.lblcam[index].bind(battery=self.DrawCamera,adapter=self.DrawCamera,memory=self.DrawCamera)
    #cam.CheckSetting("system_mode")
    threading.Thread(target=self.DoFileTaken, args=(index,recstatus,), name="%sDoFileTaken" %cam.name).start()
    threading.Thread(target=self.DoStartRecord, args=(index,recstatus,), name="%sDoStartRecord" %cam.name).start()
    
  def DoDisconnect(self, index):
    cam = self.cam[index]
    name = cam.name
    ilen = len(name)
    print name, ilen
    try:
      if cam.link:
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

  def DoStartRecord(self, index, recstatus=""):
    while self.quitcam[index].isSet():
      pass
    cam = self.cam[index]
    while not cam.quit.isSet():
      if recstatus in ("record","recording"):
        self.lblcam[index].status = 'busy'
        recstatus = ""
        if self.recstart == 0:
          recstatus = "record"
          self.firstcam = index
        self.recstart += 1
        threading.Thread(target=self.DoStopRecord, args=(index,recstatus,), name="DoStopRecord%d" %index).start()
        recstatus = ""
        if self.recstart == self.reccam:
          while self.linked < self.maxcam:
            pass
          while cam.recordsec == 0:
            pass
          self.trec = time.time() - cam.recordsec
          self.btnrecord.text = "STOP"
          self.btnrecord.disabled = False
          self.recordstart.clear()
          self.lblstatus.color = (0,0,0,0)
          self.lblstatus.text = 'REC'
          self.lblrecordtime.text = self.Second2Time(cam.recordsec)
          self.lblrecordtime.color = (1,1,1,1)
          Clock.schedule_interval(self.DoShowTime, 0.5)
          for lbl in self.lblcam:
            if lbl.status == 'busy':
              lbl.status = 'link'
        self.recordstop.wait()
      else:
        self.recordstart.wait()
        self.lblcam[index].status = 'busy'
        if self.ledonstart != 0:
          opt = ['remain','all enable','all disable', 'status enable']
          setok = cam.setok
          if cam.cfgdict.has_key('led_mode'):
            print 'check led mode'
            print cam.cfgdict['led_mode']
            print opt[self.ledonstart]
            if cam.cfgdict['led_mode'] != opt[self.ledonstart]:
              cam.ChangeSetting("led_mode",opt[self.ledonstart])
              setok.wait(10)
              cam.msgbusy = 0
          else:
            cam.ChangeSetting("led_mode",opt[self.ledonstart])
            setok.wait(10)
            cam.msgbusy = 0
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
            if self.buzzeronstart == 1:
              self.lblcam[self.firstcam].status = 'beep'
              threading.Thread(target=self.DoBuzzerRing, args=(0,), name="DoBuzzerRing").start()
            self.btnrecord.text = "STOP"
            self.btnrecord.disabled = False
            self.recordstart.clear()
            self.lblstatus.color = (0,0,0,0)
            self.lblstatus.text = 'REC'
            self.lblrecordtime.text = '00:00:00'
            self.lblrecordtime.color = (1,1,1,1)
            Clock.schedule_interval(self.DoShowTime, 0.5)          
        else:
          self.lblcam[index].status = "error"
        self.recordstop.wait()
        
  def DoShowTime(self, *args):
    isec = int(time.time() - self.trec)
    self.lblrecordtime.text = self.Second2Time(isec)
    if isec % 2 == 0:
      self.lblstatus.color = (0,0,0,1)
    else:
      self.lblstatus.color = (1,0,0,1)
    
  def DoStopRecord(self, index, recstatus=""):
    if self.moveduplicated == 1:
      threading.Thread(target=self.RenameDuplicated, args=(index,),name="RenameDuplicated%d" %index).start()
    self.recordstop.wait()
    print 'DoStopRecord %d' %index
    self.lblcam[index].status = "busy"
    cam = self.cam[index]
    cam.taken.clear()
    if cam.recording.isSet():
      #if self.buzzeronstop:
      #  cam.msgbusy = 0
      cam.StopRecord()
    #print "DoStopRecord", index
    #print cam.filetaken
    # stopfirst = self.recstart
    # if stopfirst == 0: #show last record time
      # self.firstcam = index
    if recstatus in ("record","recording"):
      self.ftaken += (self.maxcam - self.reccam)
      self.recstart += (self.maxcam - self.reccam)
      self.rename += (self.maxcam - self.reccam)
    self.recstart += 1
    if self.recstart == self.maxcam:
      self.trec = time.time()
      Clock.schedule_interval(self.FlashTimeOn, 0.5)
      self.recordstop.clear()
      self.lblstatus.text = ''
      #self.btnsetting.disabled = False
      #self.btnmeter.disabled = False
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
    if type == 1 and self.buzzeronstop == 1:
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
      if self.buzzeronstop == 1:
        self.lblcam[self.firstcam].status = 'beep'
        threading.Thread(target=self.DoBuzzerRing, args=(1,),name="DoBuzzerRing").start()
      else:
        Clock.unschedule(self.DoShowTime)
        self.trec = 0
        self.recordstart.clear()
        self.recordstop.set()
    elif btnrecord.text == "PHOTO":
      btnrecord.disabled = True
      self.btnsetting.disabled = True
      self.btnmeter.disabled = True
      i = 0
      for lbl in self.lblcam:
        if lbl.status == 'link':
          lbl.status = 'busy'
          self.recstart += 1
          self.cam[i].TakePhoto()
        i += 1

  def ConfigPopupOpen(self, btn, text):
    if text == "":
      return
    btn.text = ""
    if btn == self.btnsetting:
      print "btnsetting",text      
      if text == "Advanced":
        popup = XCfgCameras() #XCfgAdvanced()
        popup.scenename = self.camscenename
        popup.sceneshot = self.camsceneshot
        popup.autorename = self.autorename
        popup.moveduplicated = self.moveduplicated
        popup.buzzeronstart = self.buzzeronstart
        popup.buzzeronstop = self.buzzeronstop
        popup.ledonstart = self.ledonstart
        popup.ledonstop = self.ledonstop
        popup.buzzervolume = self.buzzervolume
        popup.metermode = self.cammetermode
        popup.systemmode = self.systemmode
        wg_advanced = self.get_screen('advanced').children[0]
        wg_advanced.clear_widgets()
        wg_advanced.add_widget(popup)
        
        # print 'self',self
        # print 'self.screen[0]',self.screen[0]
        # print 'self.screen[1]',self.screen[1]
        # print 'self.current',self.current
        # print 'self.previous()', self.previous()
        
        #self.transition = RiseInTransition()
        self.transition = SlideTransition(direction='right')
        #self.direction = 'right'
        self.current = 'advanced'
        #self.switch_to(self.screen[1])
      else: #camera ip setting
        index = int(text.split(" ")[1]) - 1
        if self.cam[index].link:
          self.cam[index].CheckSetting("preview_status")
        camcfg = {}
        camcfg["camera"] = self.cfglist[index]["camera"]
        camcfg["ip"] = self.cfglist[index]["ip"]
        camcfg["name"] = self.cfglist[index]["name"]
        camcfg["enabled"] = self.cfglist[index]["enabled"]
        camcfg["preview"] = self.cfglist[index]["preview"]
        popup = ConfigPopup(title='Camera %d Config' %(index+1), size_hint=(0.8, 0.6), size=self.size, cfg=camcfg, index=index)
        popup.bind(on_dismiss=self.ConfigPopupApply)
        popup.apply = False
        popup.index = index
        popup.open()
    if btn == self.btnmeter:
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
        popup = CameraSettingPopup(title='Camera %d Options' %(index+1), size_hint=(0.8, 0.8), size=self.size, asid=self.cam[index].asid, index=index)
        popup.bind(on_dismiss=self.CameraSettingPopupApply)
        popup.apply = False
        popup.index = index
        popup.open()
        pass
  
  def XCfgCamerasDraw(self,*args):
    wg_config = self.get_screen('config').children[0]
    popup = XCfgCameras()
    cfg = []
    for i in range(7):
      segment = self.cfglist[i]["ip"].split(".")
      if self.CheckIPAddress(self.cfglist[i]["ip"]):
        ip = segment[3]
        if i == 0:
          popup.network = segment[0] + '.' + segment[1] + '.' + segment[2]
      else:
        ip = 101 + i
        if i == 0:
          popup.network = '192.168.31'
      initstr = '{"camera": %d,"ip": "%s","enabled": %d,"name": "%s","preview": %d}' %(self.cfglist[i]["camera"], ip, self.cfglist[i]["enabled"], self.cfglist[i]["name"], self.cfglist[i]["preview"])
      cfg.append(json.loads(initstr))
    popup.cfg = cfg
    wg_config.clear_widgets()
    wg_config.add_widget(popup)
  
  def XCfgCamerasOpen(self, btn):
    self.transition = SlideTransition(direction='right')
    self.current = 'config'
  
  def TestFocus(self,*args):
    print "TestFocus",args 
    print args[0].focus
    args[0].text = '%s' %Window.keyboard_height
  
  def TestTripleTap(self,*args):
    popup = self.get_screen('advanced').children[0].children[0]
    popup.scenename = '%s' %Window.keyboard_height
  
  def XCfgAdvancedDraw(self,*args):
    while not self.inited:
      pass
    wg_advanced = self.get_screen('advanced').children[0]
    popup = XCfgAdvanced()
    popup.scenename = self.camscenename
    popup.sceneshot = self.camsceneshot
    popup.autorename = self.autorename
    popup.moveduplicated = self.moveduplicated
    popup.buzzeronstart = self.buzzeronstart
    popup.buzzeronstop = self.buzzeronstop
    popup.ledonstart = self.ledonstart
    popup.ledonstop = self.ledonstop
    popup.buzzervolume = self.buzzervolume
    popup.metermode = self.cammetermode
    popup.systemmode = self.systemmode
    wg_advanced.clear_widgets()
    wg_advanced.add_widget(popup)
    
  def XCfgAdvancedOpen(self, btn, direction='right'):
    if direction == 'left':
      self.transition = SlideTransition(direction='left')
    else:
      self.transition = SlideTransition(direction='right')
    self.current = 'advanced'
    # wg_config = self.get_screen('config').children[0]
    # if len(wg_config.children) == 0:
      # Clock.unschedule(self.XCfgCamerasDraw)
      # Clock.schedule_once(self.XCfgCamerasDraw)

  def XCfgAdvancedApply(self, apply=False):
    #self.transition = FallOutTransition()
    #self.direction = 'left'
    self.transition = SlideTransition(direction='left')
    self.current = 'main'
    if apply:
      # advanced setting
      popup = self.get_screen('advanced').children[0].children[0]
      if self.camscenename <> self.StringFilter(popup.scenename):
        self.lblscenename.text = self.StringFilter(popup.scenename)
        self.lblsceneshot.text = '01'
      self.autorename = popup.autorename
      self.moveduplicated = popup.moveduplicated
      self.buzzeronstart = popup.buzzeronstart
      self.buzzeronstop = popup.buzzeronstop
      self.buzzervolume = popup.buzzervolume
      if self.buzzervolume != 0:
        opt = ['remain','high','low','mute']
        for cam in self.cam:
          if cam.link:
            if cam.cfgdict.has_key('buzzer_volume'):
              if cam.cfgdict['buzzer_volume'] != opt[self.buzzervolume]:
                cam.ChangeSetting("buzzer_volume", opt[self.buzzervolume])
            else:
              cam.ChangeSetting("buzzer_volume", opt[self.buzzervolume])
      self.ledonstart = popup.ledonstart
      self.ledonstop = popup.ledonstop
      self.lblmetermode.text = self.meterlist[popup.metermode]
      for cam in self.cam:
        if cam.link:
          if cam.cfgdict.has_key('meter_mode'):
            if cam.cfgdict['meter_mode'] != self.meterlist[popup.metermode]:
              cam.ChangeSetting("meter_mode", self.meterlist[popup.metermode])
          else:
            cam.ChangeSetting("meter_mode", self.meterlist[popup.metermode])
      self.systemmode = popup.systemmode
      if self.systemmode == 0:
        self.btnrecord.text = 'RECORD'
      elif self.systemmode == 1:
        self.btnrecord.text = 'PHOTO'
      # camera config
      cfg_change = False
      if len(self.get_screen('config').children[0].children) > 0:
        popup = self.get_screen('config').children[0].children[0]
        if self.CheckIPAddress(popup.network,3):
          segment = popup.network.split(".")
          network = segment[0] + '.' + segment[1] + '.' + segment[2]
        else:
          network = '192.168.31'
        oldcfglist = []
        for i in range(7):
          oldcfglist.append(dict(self.cfglist[i]))
          ip = network + '.' + popup.cfg[i]["ip"]
          newcfg = dict(popup.cfg[i])
          if self.CheckIPAddress(ip):
            newcfg["ip"] = popup.network + '.' + newcfg["ip"]
          else:
            newcfg["ip"] = popup.network + '.%d' %(101 + i)
          
          if json.dumps(newcfg,sort_keys=True) <> json.dumps(self.cfglist[i],sort_keys=True):
            self.cfglist[i] = dict(newcfg)
            cfg_change = True
      self.WriteConfig()
      self.cfglist = self.ReadConfig()
      if cfg_change:
        Clock.unschedule(self.RenewCameraConfig)
        Clock.schedule_once(partial(self.RenewCameraConfig, oldcfglist))
    #reset value
    else:
      Clock.unschedule(self.XCfgAdvancedDraw)
      Clock.schedule_once(self.XCfgAdvancedDraw,1)
      Clock.unschedule(self.XCfgCamerasDraw)
      Clock.schedule_once(self.XCfgCamerasDraw,1)
      
  def RenewCameraConfig(self,*args):
    for index in range(7):
      oldcfg = args[0][index]
      newcfg = dict(self.cfglist[index])
      if oldcfg["ip"] <> newcfg["ip"] or oldcfg["enabled"] <> newcfg["enabled"]:
        print "RenewCameraConfig %d" %index
        cam = self.cam[index]
        if oldcfg["enabled"] == 1:
          print "oldcfg %d enable" %index
          if cam.link:
            self.linked -= 1
            threading.Thread(target=self.DoDisconnect, args=(index,),name="DoDisconnect%d" %index).start()
          self.maxcam -= 1
          ilen = len(cam.ip)
          for thread in threading.enumerate():
            if thread.isAlive() and thread.name[0:ilen] == cam.ip:
              print '_Thread__stop link',thread.name
              self.quitcam[index].set()
              break
        self.lblcam[index].status = 'disable'

        if self.CheckIPAddress(newcfg["ip"]) and newcfg["enabled"] == 1:
          self.maxcam += 1
        if self.linked == self.maxcam and self.maxcam > 0:
          self.btnrecord.disabled = False
          self.btnmeter.disabled = False
          Clock.unschedule(self.RedrawMeter)
          Clock.schedule_once(self.RedrawMeter)
        else:
          self.btnrecord.disabled = True
          self.btnmeter.disabled = True
        cam = XCamera()
        cam.index = index
        self.cam[index] = cam
        if self.CheckIPAddress(newcfg["ip"]) and newcfg["enabled"] == 1:
          cam.ip = newcfg["ip"]
          cam.enabled = True
          self.lblcam[index].status = 'enable'
        else:
          self.lblcam[index].status = 'disable'
        threading.Thread(target=self.DoDetectCam, args = (index,),name="%sDoDetectCam" %cam.ip).start()
      elif oldcfg["preview"] <> newcfg["preview"]:
        if self.cam[index].link:
          self.lblcam[index].status = 'busy'
          threading.Thread(target=self.DoSetPreview, args = (index,newcfg["preview"],),name="DoSetPreview%d" %index).start()
  
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
        #self.lblcam[index].unbind(size=self.DrawCamera,pos=self.DrawCamera,status=self.DrawCamera,battery=self.DrawCamera,adapter=self.DrawCamera,memory=self.DrawCamera)
       
        if cam.link:
          threading.Thread(target=self.DoDisconnect, args = (index,),name="DoDisconnect%d" %index).start()
        
        if self.linked == self.maxcam and self.maxcam > 0:
          self.btnrecord.disabled = False
          self.btnmeter.disabled = False
          Clock.unschedule(self.RedrawMeter)
          Clock.schedule_once(self.RedrawMeter)
        else:
          self.btnrecord.disabled = True
          self.btnmeter.disabled = True
        cam = XCamera()
        cam.index = index
        self.cam[index] = cam
        if self.CheckIPAddress(newcfg["ip"]) and newcfg["enabled"] == 1:
          cam.ip = newcfg["ip"]
          cam.enabled = True
          self.lblcam[index].status = 'enable'
          threading.Thread(target=self.DoDetectCam, args = (index,),name="%sDoDetectCam" %cam.ip).start()
      else:
        if self.cam[index].link:
          self.lblcam[index].status = 'busy'
          threading.Thread(target=self.DoSetPreview, args = (index,newcfg["preview"],),name="DoSetPreview%d" %index).start()
  
  def DoSetPreview(self, index, preview):
    cam = self.cam[index]
    if cam.cfgdict.has_key("preview_status"):
      oldpreview = cam.cfgdict["preview_status"]
    else:
      oldpreview = ""
    setok = cam.setok
    if preview == 0 and oldpreview != "off": #off
      cam.StopViewfinder()
      i = 0
      while cam.vfstart:
        if i >= 20:
          return
        time.sleep(0.5)
        i += 1
        pass
      cam.ChangeSetting("preview_status","off")
      setok.wait(10)
      cam.msgbusy = 0
      time.sleep(1)
    elif preview == 1 and oldpreview != "on": #on
      cam.StopViewfinder()
      i = 0
      while cam.vfstart:
        if i >= 20:
          return
        time.sleep(0.5)
        i += 1
        pass
      cam.ChangeSetting("preview_status","on")
      setok.wait(10)
      cam.msgbusy = 0
      cam.StartViewfinder()
      time.sleep(1)
    self.lblcam[index].status = 'link'        
        
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
    #self.lblcam[index].unbind(size=self.DrawCamera,pos=self.DrawCamera,status=self.DrawCamera,battery=self.DrawCamera,adapter=self.DrawCamera,memory=self.DrawCamera)
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
    #self.lblcam[index].unbind(size=self.DrawCamera,pos=self.DrawCamera,status=self.DrawCamera,battery=self.DrawCamera,adapter=self.DrawCamera,memory=self.DrawCamera)
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
  
  def RedrawSayHello(self,*args):
    oldtext = self.lblapptitle.text
    title = oldtext.split()[0]
    version = oldtext.split()[1]
    newtext = '[color=c0c0c0]%s[/color] %s' %(title,version)
    Clock.unschedule(self.DoRedrawSayHello)
    Clock.schedule_once(partial(self.DoRedrawSayHello,newtext))
    for i in range(len(title)):
      newtext = '[color=000000]%s[/color]' %title[0:i]
      newtext += '[color=c0c0c0]%s[/color]' %title[i:len(title)]
      newtext += ' %s' %version
      Clock.unschedule(self.DoRedrawSayHello)
      Clock.schedule_once(partial(self.DoRedrawSayHello,newtext),0.3*(i+1))
    Clock.unschedule(self.DoRedrawSayHello)
    Clock.schedule_once(partial(self.DoRedrawSayHello,oldtext),3.3)
    Clock.schedule_once(partial(self.DoRedrawSayHello,oldtext),5)
    
  def DoRedrawSayHello(self,newtext,*args):
    self.lblapptitle.text = newtext
    
  def RedrawAll(self,*args):
    Clock.unschedule(self.RedrawRecord)
    Clock.schedule_once(self.RedrawRecord)
    for lbl in self.lblcam:
      self.DrawCamera(lbl)
    Clock.unschedule(self.XCfgAdvancedDraw)
    Clock.schedule_once(self.XCfgAdvancedDraw)
    Clock.unschedule(self.XCfgCamerasDraw)
    Clock.schedule_once(self.XCfgCamerasDraw)
    Clock.unschedule(self.RedrawMeter)
    Clock.schedule_once(self.RedrawMeter)
    Clock.unschedule(self.RedrawSayHello)
    Clock.schedule_once(self.RedrawSayHello)
    
  def RedrawRecord(self,*args):
    new = RECButton()
    new.text = self.btnrecord.text
    new.disabled = self.btnrecord.disabled
    self.btnrecord.unbind(on_release=self.Record)
    self.xcamcontrol.children[0].remove_widget(self.btnrecord)
    self.xcamcontrol.children[0].add_widget(new,index=1)
    self.btnrecord = new
    self.btnrecord.bind(on_release=self.Record)
    
  def RedrawMeter(self,*args):
    new = RSpinner()
    option = []
    i = 0
    for cam in self.cam:
      i += 1
      if cam.link:
        option.append('Option %d' %i)
    option.append('Metering')
    option.append('M.Exposure')
    new.values = option
    new.disabled = self.btnmeter.disabled
    self.btnmeter.unbind(text=self.ConfigPopupOpen)
    self.xcamcontrol.children[0].remove_widget(self.btnmeter)
    self.xcamcontrol.children[0].add_widget(new)
    self.btnmeter = new
    self.btnmeter.bind(text=self.ConfigPopupOpen)
  
  def StringFilter(self, strin):
    filter = list(string.ascii_letters + string.digits)
    strout = ""
    for i in range(len(strin)):
      if strin[i] in filter:
        strout += strin[i]
    if strout == "":
      strout = "PonerineX"
    return strout[0:20]
      
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
    
  def DoFileTaken(self, index, recstatus=""):
    while self.quitcam[index].isSet():
      pass
    print 'Start DoFileTaken %d' %index
    cam = self.cam[index]
    midx = 0
    if cam.token <> 0:
      self.linked += 1
    # check card usage
    cam.CardUsage()
    # check battery
    cam.CheckBatteryState()
    if self.linked == self.maxcam:
      Clock.unschedule(self.RedrawMeter)
      Clock.schedule_once(self.RedrawMeter)
    if recstatus not in ("record","recording"):
      # check resolution
      cam.CheckSetting("video_resolution")
      if self.linked == self.maxcam:
        self.btnrecord.disabled = False
        self.btnmeter.disabled = False
      if cam.preview:
        t = time.time()
        while cam.msgbusy != 0:
          if (time.time() - t) > 10.0:
            return
        cam.StartViewfinder()
    midx = self.lblcam[index].memory
    while not cam.quit.isSet():
      cam.taken.wait(1)
      if cam.status.has_key("battery"):
        if self.lblcam[index].battery <> int(cam.status["battery"]):
          self.lblcam[index].battery = int(cam.status["battery"])
          #print 'battery %d' %self.lblcam[index].battery
      if cam.status.has_key("adapter_status"):
        if self.lblcam[index].adapter <> int(cam.status["adapter_status"]):
          self.lblcam[index].adapter = int(cam.status["adapter_status"])
          #print 'adapter %d' %self.lblcam[index].adapter
      if midx <> cam.memory:
        midx = cam.memory
        self.lblcam[index].memory = cam.memory
        #print 'memory %d' %self.lblcam[index].memory
      if cam.taken.isSet():
        if self.systemmode == 0: #video
          if self.ledonstop != 0:
            opt = ['remain','all enable','all disable', 'status enable']
            setok = cam.setok
            if cam.cfgdict.has_key('led_mode'):
              if cam.cfgdict['led_mode'] != opt[self.ledonstop]:
                cam.ChangeSetting("led_mode",opt[self.ledonstop])
                setok.wait(10)
                cam.msgbusy = 0
            else:
              cam.ChangeSetting("led_mode",opt[self.ledonstop])
              setok.wait(10)
              cam.msgbusy = 0
          self.renlist[index] = dict()
          cam.taken.clear()
          if cam.filetaken <> "":
            if cam.preview:
              cam.StartViewfinder()
            fileinfo = {"index":index,"old":cam.filetaken,"new":"","ok":0}
            self.renlist[index]=dict(fileinfo)
            if self.autorename == 1:
              threading.Thread(target=self.RenameVideoFiles, args=(index,), name="RenameVideoFiles%d" %index).start()
            #else:
              #self.lblrecordtime.text = ''
          self.ftaken += 1
          # update record time, use the minimum seconds to display
          if self.ftaken == 1: #first cam
            t = time.time()
            while cam.recordsec == 0:
              if time.time() - t > 2.0: #wait 2 seconds for timeout
                break
            if cam.recordsec != 0:
              self.lblrecordtime.text = self.Second2Time(cam.recordsec)
          else: #other cam
            t = time.time()
            while cam.recordsec == 0:
              if time.time() - t > 2.0: #wait 2 seconds for timeout
                break
            if cam.recordsec != 0 and self.lblrecordtime.text > self.Second2Time(cam.recordsec):
              self.lblrecordtime.text = self.Second2Time(cam.recordsec)
          if self.ftaken == self.maxcam and self.autorename == 0:
            self.FlashTimeOff()
            self.btnsetting.disabled = False
            self.btnrecord.disabled = False
            self.btnmeter.disabled = False
        elif self.systemmode == 1: #photo
          print 'do taken %d' %index, cam.filetaken
          if cam.filetaken <> "":
            self.lblcam[index].status = 'link'
          else:
            self.lblcam[index].status = 'error'
          cam.taken.clear()
          self.ftaken += 1
          if self.ftaken == self.maxcam:
            self.btnsetting.disabled = False
            self.btnrecord.disabled = False
            self.btnmeter.disabled = False
    #print 'Quit DoFileTaken %d' %index
    
  def RenameVideoFiles(self, index):
    self.lblcam[index].status = "busy"
    cam = self.cam[index]
    camletter = list(string.ascii_lowercase)
    camname = self.cfglist[index]["name"]
    if camname == '':
      camname = camletter[index]
    date = time.strftime('%Y%m%d')
    
    failure = False
    old = cam.status["video_record_complete"]
    #print "old file name:", old
    new = '/tmp/fuse_d/DCIM/%s/%s-%s-%02d-%s.mp4' %(self.camscenename,date,self.camscenename,self.camsceneshot,camname)
    #print "new file name:", new
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
        #print 'do FlashShotOn'
        Clock.schedule_interval(self.FlashShotOn, 0.5)
        #print 'after FlashShotOn'
        threading.Thread(target=self.FlashShotOff, name="FlashShotOff").start()
      self.btnsetting.disabled = False
      self.btnrecord.disabled = False
      self.btnmeter.disabled = False
      
  def RenameDuplicated(self, index):
    if self.buzzeronstart == 0:
      time.sleep(3)
    else:
      time.sleep(8)
    cam = self.cam[index]
    camletter = list(string.ascii_lowercase)
    camname = self.cfglist[index]["name"]
    if camname == '':
      camname = camletter[index]
    date = time.strftime('%Y%m%d')
    failure = False
    new = '/tmp/fuse_d/DCIM/%s/%s-%s-%02d-%s.mp4' %(self.camscenename,date,self.camscenename,self.camsceneshot,camname)
    stime = time.strftime('%H%M%S')
    duplicated = '/tmp/fuse_d/trashbin/%s-%s-%s-%02d-%s.mp4' %(date,stime,self.camscenename,self.camsceneshot,camname)
    ctelnet = XCameraTelnet(ip=cam.ip,username="")
    ctelnet.Rename(new, duplicated)
  
  def FlashShotOff(self):
    i = time.time()
    while ((time.time() - i) < 5.5):
      pass
    Clock.unschedule(self.FlashShotOn)
    self.lblsceneshot.color = (1,1,1,1)
    Clock.unschedule(self.XCfgAdvancedDraw)
    Clock.schedule_once(self.XCfgAdvancedDraw,1)
  
  def FlashShotOn(self, *args):
    isec = int((time.time() - self.trec) / 0.5) #refresh 0.5 seconds
    #print "FlashShotOn args %s" %args
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
      "camera": 0,
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
        self.autorename = int(cfg["autorename"])
      else:
        self.autorename = 0
      if cfg.has_key("moveduplicated"):
        self.moveduplicated = int(cfg["moveduplicated"])
      else:
        self.moveduplicated = 0
      if cfg.has_key("buzzeronstart"):
        self.buzzeronstart = int(cfg["buzzeronstart"])
      else:
        self.buzzeronstart = 0
      if cfg.has_key("buzzeronstop"):
        self.buzzeronstop = int(cfg["buzzeronstop"])
      else:
        self.buzzeronstop = 0
      if cfg.has_key("buzzervolume"):
        self.buzzervolume = int(cfg["buzzervolume"])
      else:
        self.buzzervolume = 0
      if cfg.has_key("ledonstart"):
        self.ledonstart = int(cfg["ledonstart"])
      else:
        self.ledonstart = 0
      if cfg.has_key("ledonstop"):
        self.ledonstop = int(cfg["ledonstop"])
      else:
        self.ledonstop = 0
      if cfg.has_key("systemmode"):
        self.systemmode = int(cfg["systemmode"])
      else:
        self.systemmode = 0
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
        self.cammetermode = int(cfg["meter"])
      else:
        self.cammetermode = 0
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
            cfginit["camera"] = i+1
            r.append(cfginit)
      else:
        for i in range(self.cameras):
          cfginit = json.loads(initstr)
          cfginit["camera"] = i+1
          r.append(cfginit)
    except StandardError:
      print "read error"
      for i in range(self.cameras):
        cfginit = json.loads(initstr)
        cfginit["camera"] = i+1
        r.append(cfginit)
      self.camscenename = "PonerineX"
      self.camsceneshot = 1
      self.camresolution = '1600x1200'
      self.camframe = '60P'
      self.cambitrate = '35M'
      self.camaspect = '4:3'
      self.cammetermode = 0
      self.camexposure = 'auto'
      self.camshutter = 'auto'
      self.camiso = 'auto'
      self.autorename = 0
      self.moveduplicated = 0
      self.buzzeronstart = 0
      self.buzzeronstop = 0
      self.buzzervolume = 0
      self.systemmode = 0
      self.ledonstart = 0
      self.ledonstop = 0
      
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
    cfg["meter"] = int(self.cammetermode)
    cfg["exposure"] = 'auto' # self.camexposure
    cfg["shutterspeed"] = 'auto' #self.camshutter
    cfg["iso"] = 'auto' #self.camiso
    cfg["autorename"] = int(self.autorename)
    cfg["moveduplicated"] = int(self.moveduplicated)
    cfg["buzzeronstart"] = int(self.buzzeronstart)
    cfg["buzzeronstop"] = int(self.buzzeronstop)
    cfg["buzzervolume"] = int(self.buzzervolume)
    cfg["ledonstart"] = int(self.ledonstart)
    cfg["ledonstop"] = int(self.ledonstop)
    cfg["systemmode"] = int(self.systemmode)
    
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
    xponerine.duration = 0.5
    #xponerine.transition = SlideTransition()

    #xponerine.screen = [XRecordScreen(name="main"),XRecordScreen(name="advanced")]
    xponerine.add_widget(XRecordScreen(name="main"))
    xponerine.add_widget(XRecordScreen(name="advanced"))
    xponerine.add_widget(XRecordScreen(name="config"))
    #xponerine.switch_to(xponerine.screen[0])
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
