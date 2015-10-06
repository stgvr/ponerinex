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
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty

# Camera Object[camera.py]
from xcamera import XCamera
from xcameratelnet import XCameraTelnet
'''
platform.system()
"Windows", "Darwin", "Linux"
'''
import json, os, threading, time, socket, platform, inspect, string
from os.path import basename

Builder.load_file('xdata/xconnectscreen.kv')
Builder.load_file('xdata/xpopupconfig.kv')

Clock.max_iteration = 100
__version__='0.0.1'

class XConnectScreen(Screen):
  pass

class AdvancedPopup(Popup):
  scenename = StringProperty()
  scenecount = NumericProperty()
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
  
class XPonerine(ScreenManager):
  def __init__(self, appevent):
    super(XPonerine, self).__init__()

    self.applyconfig = False
    self.appexit = appevent[0]
    #self.apppause = appevent[1]
    #self.appresume = appevent[2]
    self.inited = False
    self.textcaminfo = ""  # Camera Information
    self.timecontitle = time.time() # Connect Title
    self.textctrlbtn = ""  # Control Buttons
    self.cfglist = []
    self.autorename = False
    self.moveduplicated = False
    self.buzzeronstart = False
    self.buzzeronstop = False
    self.buzzermute = False
    self.photomode = False
    self.scenename = "scene"
    self.scenecount = 1
    self.linked = 0
    self.maxcam = 0
    self.cfglist = self.ReadConfig()
    self.stopdetect = threading.Event()
    self.resizecam = threading.Event()
    self.connect = threading.Event()
    self.recordstart = threading.Event()
    self.recordstop = threading.Event()
    
    sysname = platform.system()
    if sysname == "Windows":
      Window.size = (560,800) #(1200,800)
      #Window.borderless = '1'
    elif sysname == "Darwin":
      Window.size = (520,700)
    elif sysname == "Linux":
      if platform.linux_distribution()[0] == "Ubuntu":
        Window.size = (560,800)
        
  def InitialCamIcon(self):
    for child in self.current_screen.children[0].children[:]:
      # title
      if isinstance(child, BoxLayout):
        self.btncamsetup = child.children[0]
      # camera icons
      elif isinstance(child, GridLayout):
        pass
      # control or recordtime
      elif isinstance(child, AnchorLayout):
        i = 0
        for btn in child.children[0].children[:]:
          if isinstance(btn, Button):
            i += 1
        # control
        if i == 3:
          self.btnpreview = child.children[0].children[0]
          self.btnrecord = child.children[0].children[1]
          self.btnrecord.text = "%s-%02d" %(self.scenename,self.scenecount)
          self.btnbuzzer = child.children[0].children[2]
        # record time
        else:
          self.lblrecordtime = child.children[0].children[1]
          self.btnrecordtime = child.children[0].children[2]
    # add all cams in list
    self.cam = []
    self.lblcamtext = []
    self.btncamstatus = []
    self.linked = 0
    self.maxcam = 0
    for i in range(self.cameras):
      cam = XCamera()
      cam.index = i
      if self.cfglist[i]["ip"] <> "" and self.cfglist[i]["enabled"] == 1:
        cam.enabled = True
        cam.ip = self.cfglist[i]["ip"]
        self.maxcam += 1
      self.cam.append(cam)
      self.lblcamtext.append("")
      self.btncamstatus.append("ximage/cam_disabled_none_bat.png")
      threading.Thread(target=self.DoDetectCam, name="%dDoDetectCam" %i, args=(i,)).start()
    return
    self.btnconctrl = []
    self.btnconctrl.append({"color":"0,0,0,1",
                         "disabled_color":"0,0,0,0.5",
                         "disabled":"False",
                         "text":"CONNECT",
                         "background_normal":"image/mcamera_normal.png",
                         "background_down":"image/mcamera_down.png",
                         "background_disabled_normal":"image/mcamera_noip.png",
                         "background_disabled_down":"image/mcamera_noip.png"})
    self.btnconctrl.append({"color":"0,0,0,1",
                         "disabled_color":"0,0,0,0.5",
                         "disabled":"True",
                         "text":"RECORD",
                         "background_normal":"image/mcamera_normal.png",
                         "background_down":"image/mcamera_down.png",
                         "background_disabled_normal":"image/mcamera_noip.png",
                         "background_disabled_down":"image/mcamera_noip.png"})
    self.btnconctrl.append({"color":"0,0,0,1",
                         "disabled_color":"0,0,0,0.5",
                         "disabled":"True",
                         "text":"BUZZER",
                         "background_normal":"image/mcamera_normal.png",
                         "background_down":"image/mcamera_down.png",
                         "background_disabled_normal":"image/mcamera_noip.png",
                         "background_disabled_down":"image/mcamera_noip.png"})
    #self.recordtime = ""
    #self.lblrecordtime.text = "[color=0000ff]%s - %d[/color]\n" %(self.scenename,self.scenecount) + ("[color=ff0000]%s[/color]" %self.recordtime if self.recordtime <> "" else "")
    
    for i in range(self.cameras):
      if self.cfglist[i]["ip"] <> "" and self.cfglist[i]["enabled"] == 1:
        if self.cfglist[i]["name"] == "":
          self.current_screen.ids['lblCamName%d' %i].text = "[b][sup]%s[/sup][/b] CAM" %(self.cfglist[i]["camera"])
        else:
          self.current_screen.ids['lblCamName%d' %i].text = "[b][sup]%s[/sup][/b] %s" %(self.cfglist[i]["camera"],self.cfglist[i]["name"])
        self.lblcamname.append(self.current_screen.ids['lblCamName%d' %i].text)
        self.current_screen.ids['lblCamStatus%d' %i].text = "[color=000000]searching[/color]"
        self.lblcamstatus.append("[color=000000]searching[/color]")
        threading.Thread(target=self.DoDetectCam, name="DoDetectCam%d" %i,
                         args=(i, self.cfglist[i]["ip"], 1,)).start()
      else:
        self.current_screen.ids['lblCamName%d' %i].text = ""
        self.lblcamname.append("")
        self.current_screen.ids['lblCamStatus%d' %i].text = ""
        self.lblcamstatus.append("")
    self.inited = True
    t = threading.Thread(target=self.DoRefreshConnectControl, name="DoRefreshConnectControl")
    t.setDaemon(True)
    t.start()
        
  def DoDetectCam(self, index):
    port = [7878, 8787, 554, 23]
    while True:
      if self.cam[index].enabled:
        break
    socket.setdefaulttimeout(5)
    retry = 0
    timewait = 1
    while True:
      time.sleep(timewait)
      retry = (retry + 1) % len(port)
      srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      srv.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
      open = srv.connect_ex((self.cam[index].ip, port[retry])) #7878
      srv.close()
      print "DoDetectCam %d port %d retry %d open %d" %(index, port[retry], retry, open)
      if open == 0:
        self.lblcamtext[index] = "[b][color=50e3c2]ON[/color][/b]"
        self.btncamstatus[index] = "ximage/cam_link_none_bat.png"
        self.RefreshCameraInformation()
        threading.Thread(target=self.DoConnect, name="%dDoConnect" %index, args=(index,)).start()
        return
      elif retry == 0:
        if timewait < 10:
          timewait += 1
        self.lblcamtext[index] = "[b][color=d0021b]OFF[/color][/b]"
        self.btncamstatus[index] = "ximage/cam_err_none_bat.png"
        self.RefreshCameraInformation(2)
  
  def DoConnect(self, index):
    print "Doconnect camera %d" %index
    cam = self.cam[index]
    cam.LinkCamera()
    t = time.time()
    while True:
      if cam.socketopen == 0:
        break
      if time.time() - t > 30.0:
        self.lblcamtext[index] = "[b][color=d0021b]ERR[/color][/b]"
        self.btncamstatus[index] = "ximage/cam_err_none_bat.png"
        print "Fail to connect camera %d" %index
        threading.Thread(target=self.DoDetectCam, name="%dDoDetectCam" %index, args=(index,)).start()
        return
    while True:
      if cam.link:
        break
      if time.time() - t > 30.0:
        self.lblcamtext[index] = "[b][color=d0021b]ERR[/color][/b]"
        self.btncamstatus[index] = "ximage/cam_err_none_bat.png"
        print "Fail to connect camera %d" %index
        threading.Thread(target=self.DoDetectCam, name="%dDoDetectCam" %index, args=(index,)).start()
        return
    while cam.token == 0:
      pass
    print "name", cam.name, "token", cam.token
    # check battery
    cam.CheckBatteryState()
    time.sleep(1)
    # sync time
    setok = cam.setok
    #offset index*12=0,12,24,36,48,60
    t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()+ index * 12))
    print "time offset: %s" %t
    cam.ChangeSetting("camera_clock", t)
    setok.wait(10)
    self.msgbusy = 0
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
          self.msgbusy = 0
      else:
        cam.volume = "low"
    self.lblcamtext[index] = "[b][color=7ed321]OK[/color][/b]"
    if cam.status.has_key("battery"):
      self.lblcamtext[index] = self.AddBatteryInfo(self.lblcamtext[index], cam.status["battery"])
      self.btncamstatus[index] = self.AddBatteryIcon(self.lblcamtext[index], cam.status["battery"], cam.status["adapter_status"])
    else:
      self.btncamstatus[index] = "ximage/cam_on_none_bat.png"
      
    self.RefreshCameraInformation()
    self.linked += 1
    
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
    for thread in threading.enumerate():
      if thread.isAlive():
        tname = thread.name
        if len(tname) > ilen and tname[ilen] == name:
          try:
            print "DoDisconnect %d kill %s" %(index, thread.name)
            thread._Thread__stop()
          except:
            pass

  def DoStartRecord(self, index, number):
    cam = self.cam[index]
    retry = False
    while True:
      self.recordstart.wait()
      cam.StartRecord(False)
      cam.recording.wait(10)
      if cam.recording.isSet():
        retry = False
        print "\nDoStartRecord", index
        if self.linked == 0:
          self.firstcam = index
          print "self.firstcam", self.firstcam
        self.linked += 1
        self.btnrecord.text = 'CAM %d / %d' %(self.linked, len(self.cam))
        self.btnconctrl[1]["text"] = 'CAM %d / %d' %(self.linked, len(self.cam))
        self.lblcamstatus[number] = "[color=ff0000]recording[/color]"
        threading.Thread(target=self.DoStopRecord, args=(index,number,), name="DoStopRecord%d" %index).start()
        if self.linked == len(self.cam):
          self.trec = time.time()
          if self.buzzeronstart:
            #threading.Thread(target=self.DoBuzzerRing, args=(3,), name="DoBuzzerRing").start()
            threading.Thread(target=self.DoBuzzerRing, name="DoBuzzerRing").start()
          self.btnconctrl[1]["text"] = "STOP"
          self.RefreshConnectControl(1)
          #threading.Thread(target=self.ButtonText, args=(self.btnrecord,"STOP",1,), name="ButtonText").start()
          threading.Thread(target=self.DoShowRecord, name="DoShowRecord").start()
          threading.Thread(target=self.DoShowTime, name="DoShowTime").start()
          self.recordstart.clear()
          self.btnrecord.disabled = False
          self.btnconctrl[1]["disabled"] = "False"
          self.recordtime = self.Second2Time(time.time() - self.trec)
          self.lblrecordtime.text = "[color=0000ff]%s - %d[/color]\n" %(self.scenename,self.scenecount) + ("[color=ff0000]%s[/color]" %self.recordtime if self.recordtime <> "" else "")
          
        if cam.preview:
          cam.StartViewfinder()
        self.RefreshCameraInformation(1)
        #*#self.RefreshConnectControl(1)
        self.recordstop.wait()
      elif retry:
        retry = False
        self.recordstart.clear()
        self.btnrecord.disabled_color = (1,0,0,1)
        self.btnrecord.text = "ERROR"
        time.sleep(2)
        self.btnrecord.disabled_color = (0,0,0,1)
        self.btnrecord.text == "STOP"
        self.btnconctrl[1]["disabled_color"] = "0,0,0,1"
        self.btnconctrl[1]["text"] = "STOP"
        #*#self.RefreshConnectControl(1)
        self.Record(self.btnrecord) #STOP
        self.recordstop.wait()
      else:
        retry = True
        
  def DoShowTime(self):
    txtold = self.Second2Time(time.time() - self.trec)
    txtnew = txtold
    while True:
      txtnew = self.Second2Time(time.time() - self.trec)
      if txtnew <> txtold:
        self.recordtime = txtnew
        self.lblrecordtime.text = "[color=0000ff]%s - %d[/color]\n" %(self.scenename,self.scenecount) + ("[color=ff0000]%s[/color]" %self.recordtime if self.recordtime <> "" else "")
        txtold = txtnew
      if self.btnrecord.text == "STOP":
        break
    while True:
      txtnew = self.Second2Time(time.time() - self.trec)
      if txtnew <> txtold:
        self.recordtime = txtnew
        self.lblrecordtime.text = "[color=0000ff]%s - %d[/color]\n" %(self.scenename,self.scenecount) + ("[color=ff0000]%s[/color]" %self.recordtime if self.recordtime <> "" else "")
        txtold = txtnew
      if self.btnrecord.text <> "STOP":
        break
    
  def DoShowRecord(self):
    i = 0
    while True:
      if self.btnrecord.text == "STOP":
        if i == 0:
          i = 1
          self.btnrecord.background_normal = 'image/mcamera_disconnect.png'
          self.btnconctrl[1]["background_normal"] = "image/mcamera_disconnect.png"
        else:
          i = 0
          self.btnrecord.background_normal = 'image/mcamera_normal.png'
          self.btnconctrl[1]["background_normal"] = "image/mcamera_normal.png"
        
        #print self.btnrecord.text, self.btnrecord.background_normal, i
      self.recordstop.wait(1)
      if self.recordstop.isSet() or self.btnrecord.text in ("RECORD", "STOPPING", "ERROR"):
        self.btnrecord.background_normal = 'image/mcamera_normal.png'
        self.btnconctrl[1]["background_normal"] = "image/mcamera_normal.png"
        #*#self.RefreshConnectControl(1)
        return
      #*#self.RefreshConnectControl(1)
    
  def DoStopRecord(self, index, number):
    self.recordstop.wait()
    cam = self.cam[index]
    cam.taken.clear()
    if cam.recording.isSet():
      #if self.buzzeronstop:
      #  cam.msgbusy = 0
      cam.StopRecord()
    print "DoStopRecord", index
    print cam.filetaken
    stopfirst = self.linked
    self.linked += 1
    if stopfirst == 0: #show last record time
      self.firstcam = index
      self.recordtime = self.Second2Time(time.time() - self.trec)
      self.lblrecordtime.text = "[color=0000ff]%s - %d[/color]\n" %(self.scenename,self.scenecount) + ("[color=ff0000]%s[/color]" %self.recordtime if self.recordtime <> "" else "")
    self.btnrecord.text = 'CAM %d / %d' %(self.linked, len(self.cam))
    self.btnconctrl[1]["text"] = 'CAM %d / %d' %(self.linked, len(self.cam))
    self.lblcamstatus[number] = "[color=0000ff]stop record[/color]"
    self.RefreshCameraInformation(1)
    if self.linked == len(self.cam):
      self.btnconctrl[1]["text"] = "RECORD"
      self.btnrecord.text = "RECORD"
      #threading.Thread(target=self.ButtonText, args=(self.btnrecord,"RECORD",1.5,), name="ButtonText").start()
      self.recordstop.clear()
      self.btnrecord.background_normal = 'image/mcamera_normal.png'
      self.btnrecord.disabled = False
      self.btnconctrl[1]["background_normal"] = 'image/mcamera_normal.png'
      self.btnconctrl[1]["disabled"] = 'False'
    #*#self.RefreshConnectControl(1)
    
  def Buzzer(self, btnbuzzer):
    threading.Thread(target=self.DoBuzzerRing, args = (True,),name="DoBuzzerRing").start()
    
  def DoBuzzerRing(self, force=False):
    print "self.firstcam",self.firstcam
    cam = self.cam[self.firstcam]
    if force == False:
      while True:
        if cam.vfstart == False:
          break
      cam.SendMsg('{"msg_id":515}')
      rtime = cam.recordtime
      while True:
        if cam.recordtime <> rtime:
          rtime = cam.recordtime
          print "first rtime", rtime
          break
        else:
          time.sleep(1)
          cam.SendMsg('{"msg_id":515}')

    setok = cam.setok
    seterror = cam.seterror

    cam.ChangeSetting("buzzer_ring","on")
    if force:
      t = time.time()
      setok.wait(5)
      if setok.isSet():
        if time.time() - t < 3.0:
          time.sleep(2)
        #cam.SendMsg('{"msg_id":1,"type":"app_status"}')
    else:
      rtime = cam.recordtime
      print "second rtime", rtime
      cam.SendMsg('{"msg_id":515}')
      while True:
        if int(cam.recordtime.split(':')[2]) - 2 >= int(rtime.split(':')[2]):
          break
        else:
          time.sleep(1)
          cam.SendMsg('{"msg_id":515}')
    cam.ChangeSetting("buzzer_ring","off")
    #cam.msgbusy = 0
            
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
    if btnrecord.text == "RECORD":
      self.linked = 0
      self.rename = 0
      self.renlist = []
      self.firstcam = 0
      self.recordstop.clear()
      self.recordstart.set()
      btnrecord.text == "STARTING"
      btnrecord.disabled = True
      self.btnconctrl[1]["text"] = 'STARTING'
    elif btnrecord.text == "STOP":
      self.linked = 0
      self.rename = 0
      self.renlist = []
      btnrecord.text == "STOPPING"
      btnrecord.disabled = True
      self.btnconctrl[1]["text"] = 'STOPPING'
      if self.buzzeronstop:
        self.DoBuzzerRing()
      self.recordstart.clear()
      self.recordstop.set()
    self.btnconctrl[1]["disabled"] = 'True'
    #*#self.RefreshConnectControl()

  def ConfigPopupOpen(self, btnsetup, text):
    if btnsetup.text <> "":
      text = btnsetup.text
      btnsetup.text = ""
      if text == "Advanced":
        popup = AdvancedPopup(title='Camera Advanced Config', size_hint=(0.8, 0.8), size=self.size)
        popup.bind(on_dismiss=self.AdvancedPopupApply)
        popup.apply = False
        popup.scenename = self.scenename
        popup.scenecount = self.scenecount
        popup.autorename = self.autorename
        popup.moveduplicated = self.moveduplicated
        popup.buzzeronstart = self.buzzeronstart
        popup.buzzeronstop = self.buzzeronstop
        popup.buzzermute = self.buzzermute
        popup.photomode = self.photomode
        popup.open()
      else:
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
        #print self.configpop.apply, self.configpop.index, self.configpop.cfg
        popup.open()
  
  def ConfigPopupApply(self, popup):
    if popup.apply:
      index = popup.index
      oldcfg = {}
      oldcfg["ip"] = self.cfglist[index]["ip"]
      oldcfg["enabled"] = self.cfglist[index]["enabled"]
      oldcfg["preview"] = self.cfglist[index]["preview"]
      print "index %d old config: %s" %(index, oldcfg)
      self.cfglist[index] = popup.cfg
      self.WriteConfig()
      self.cfglist = self.ReadConfig()
      newcfg = self.cfglist[index]
      print "index %d new config: %s" %(index, newcfg)
      if oldcfg["ip"] <> newcfg["ip"] or oldcfg["enabled"] <> newcfg["enabled"]:
        print "ConfigPopupApply self.cam[index].link", self.cam[index].link
        if self.cam[index].link:
          self.linked -= 1
          threading.Thread(target=self.DoDisconnect, args = (index,),name="DoDisconnect%d" %index).start()
          
        for thread in threading.enumerate():
          if thread.isAlive() and thread.name[0] == str(index):
              try:
                print "ConfigPopupApply %d kill %s" %(index, thread.name)
                thread._Thread__stop()
              except:
                pass
        self.lblcamtext.append("")
        self.btncamstatus.append("ximage/cam_disabled_none_bat.png")
        self.textcaminfo = ""
        self.RefreshCameraInformation()
        cam = XCamera()
        cam.index = index
        if newcfg["ip"] <> "" and newcfg["enabled"] == 1:
          cam.ip = newcfg["ip"]
          cam.enabled = True
        else:
          self.maxcam -= 1
        
        self.cam[index] = cam
        threading.Thread(target=self.DoDetectCam, args = (index,),name="%dDoDetectCam" %index).start()
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
      if self.scenename <> self.StringFilter(popup.scenename):
        self.scenename = self.StringFilter(popup.scenename)
        #self.lblscenename.text = self.scenename
        self.scenecount = 1
        #self.lblscenecount.text = "No.%d" %self.scenecount
      self.autorename = popup.autorename
      self.moveduplicated = popup.moveduplicated
      self.buzzeronstart = popup.buzzeronstart
      self.buzzeronstop = popup.buzzeronstop
      self.buzzermute = popup.buzzermute
      self.photomode = popup.photomode
      self.WriteConfig()
      self.RefreshConnectControl()
      
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
    
  def DoFileTaken(self, index, number):
    cam = self.cam[index]
    time.sleep(1)
    t1 = time.time()
    cam.CheckBatteryState()
    while True:
      if cam.status.has_key("battery"):
          break
      if (time.time() - t1) > 10.0:
        cam.msgbusy = 0
        break
      
    setok = cam.setok
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
          self.msgbusy = 0
      else:
        cam.volume = "low"
    # Sync Camera Time, range of: (0,8,16,24,32,40,48,56)
    # self.synctime = time.strftime('%Y-%m-%d %H:%M:')
    t = self.synctime + '%02d' %(number * 8)
    cam.ChangeSetting("camera_clock",t)
    setok.wait(10)
    self.msgbusy = 0
    
    if self.loadallsettings:
      cam.SendMsg('{"type":"video_resolution","msg_id":1}')
      t1 = time.time()
      while True:
        if cam.cfgdict.has_key("video_resolution"):
          break
        if (time.time() - t1) > 10.0:
          cam.msgbusy = 0
          break
      if cam.cfgdict.has_key("video_resolution"):
        self.lblcamstatus[number] = "[color=00cc00]%s[/color]" %cam.cfgdict["video_resolution"]
        
    i = 0
    if cam.status.has_key("battery"):
      self.lblcamstatus[number] = self.AddBatteryInfo(self.lblcamstatus[number], cam.status["battery"], cam.status["adapter_status"])
      
    self.RefreshCameraInformation()
    
    while not cam.quit.isSet():
      i = i % 5 + 1
      cam.taken.wait(1)
      if i >= 5 and cam.status.has_key("battery"):
        self.lblcamstatus[number] = self.AddBatteryInfo(self.lblcamstatus[number], cam.status["battery"], cam.status["adapter_status"])
        self.RefreshCameraInformation(1)
          
      if cam.taken.isSet():
        self.rename += 1
        cam.taken.clear()
        self.recordtime = ""
        self.lblrecordtime.text = "[color=0000ff]%s - %d[/color]\n" %(self.scenename,self.scenecount) + ("[color=ff0000]%s[/color]" %self.recordtime if self.recordtime <> "" else "")
        if cam.filetaken <> "":
          #debugtxt += "\nCAM %d : " %(index+1) + self.cam[index].filetaken
          self.lblcamstatus[number] = "[sup][b]%s[/b][/sup] [color=0000ff]%s[/color]" %(cam.dirtaken,cam.filetaken)
          if cam.preview:
            cam.StartViewfinder()
          self.RefreshCameraInformation()
          fileinfo = {"index":index,"number":number,"old":cam.status["video_record_complete"],"new":"","ok":0}
          self.renlist.append(fileinfo)
          if self.autorename:
            threading.Thread(target=self.RenameVideoFiles, args=(index,number,), name="RenameVideoFiles%d" %index).start()
    #print "DoFileTaken stop %d" %index
  
  def RenameVideoFiles(self, index, number):
    cam = self.cam[index]
    date = time.strftime('%Y%m%d')
    camletter = list(string.ascii_lowercase)
    failure = False
    old = cam.status["video_record_complete"]
    cam.SendMsg('{"msg_id":1026,"param":"%s"}' %old.replace('.mp4','.THM')) 
    print "old file name:", old
    new = '/tmp/fuse_d/DCIM/%s/%s-%s-%s-%03d.mp4' %(self.scenename,date,self.scenename,camletter[number],self.scenecount)
    print "new file name:", new
    fileinfo = {}
    for item in self.renlist:
      if item["index"] == index:
        item["new"] = new
        fileinfo = item
        break
    ctelnet = XCameraTelnet(ip=cam.ip,username="")
    commit = ctelnet.commit
    ctelnet.Rename(old, new)
    while True:
      commit.wait(1)
      if commit.isSet():
        arr = new.split('/')
        self.lblcamstatus[number] = "[color=0000ff]%s[/color]" %(arr[len(arr)-1])
        if fileinfo <> {}:
          fileinfo["ok"] = 1
        cam.SendMsg('{"msg_id":1026,"param":"%s"}' %new)
        break
      elif ctelnet.failure:
        failure = failure or ctelnet.failure
        self.lblcamstatus[number] = "[color=ff0000]Rename %s Error[/color]" %self.cam[index].filetaken
        print "Rename Error"
        if fileinfo <> {}:
          fileinfo["ok"] = 0
        break
    cam.status["video_record_complete"] = ""
    cam.dirtaken = ""
    cam.filetaken = ""
    self.RefreshCameraInformation()
    if len(self.renlist) == len(self.cam):
      for item in self.renlist:
        if item["ok"] == 0:
          failure = True
          break
      if not failure:
        self.scenecount += 1
        self.WriteConfig()
        self.lblrecordtime.text = "[color=0000ff]%s - %d[/color]\n" %(self.scenename,self.scenecount) + ("[color=ff0000]%s[/color]" %self.recordtime if self.recordtime <> "" else "")
  
  def AddBatteryInfo(self, camstatus, battery):
    if battery == "":
      return camstatus
    else:
      bat = int(battery)
      if bat >= 30: # green
        str = "[b] - [color=7ed321]%d%%[/color][/b]" %bat
      else: # red
        str = "[b] - [color=d0021b]%d%%[/color][/b]" %bat
      return camstatus + str
      
  def AddBatteryIcon(self, camstatus, battery, adapter):
    arr = camstatus.split("[/color]")[0].split("]")
    sta = arr[len(arr)-1]
    if battery == "":
      if sta == "OK":
        return "ximage/cam_on_none_bat.png"
      elif sta == "ON":
        return "ximage/cam_link_none_bat.png"
      else:
        return "ximage/cam_err_none_bat.png"
    elif adapter == "1":
      if sta == "OK":
        return "ximage/cam_on_charge.png"
      elif sta == "ON":
        return "ximage/cam_link_charge.png"
      else:
        return "ximage/cam_err_charge.png"
    else:
      bat = int(battery)
      if bat >= 60: # green
        if sta == "OK":
          return "ximage/cam_on_full_bat.png"
        elif sta == "ON":
          return "ximage/cam_link_full_bat.png"
        else:
          return "ximage/cam_err_full_bat.png"
      if bat >= 30: # green
        if sta == "OK":
          return "ximage/cam_on_mid_bat.png"
        elif sta == "ON":
          return "ximage/cam_link_mid_bat.png"
        else:
          return "ximage/cam_err_mid_bat.png"
      else: # red
        if sta == "OK":
          return "ximage/cam_on_low_bat.png"
        elif sta == "ON":
          return "ximage/cam_link_low_bat.png"
        else:
          return "ximage/cam_err_low_bat.png"
      
  def ReadConfig(self):
    self.cameras = 6 #default 6 cameras
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
        self.scenename = cfg["scenename"]
      if cfg.has_key("scenecount"):
        self.scenecount = cfg["scenecount"]
      if self.scenecount <= 0:
        self.scenecount = 1
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
      for i in range(self.cameras):
        cfginit = json.loads(initstr)
        cfginit["camera"] = str(i+1)
        r.append(cfginit)
      self.scenename = "scene"
      self.scenecount = 1
      self.autorename = False
      self.moveduplicated = False
      self.buzzeronstart = False
      self.buzzeronstop = False
      self.buzzermute = False
      self.photomode = False
      
    if self.inited:
      cname = []
      cstatus = []
      csetup = []
      i = 0
      for item in r:
        if item["ip"] <> "" and item["enabled"] == 1:
          cname.append("[b][sup]%s[/sup][/b] %s" %(item["camera"],item["name"]))
        else:
          cname.append("")
        cstatus.append("")
        i += 1
        csetup.append("Camera %d" %i)
      csetup.append("Advanced")
      self.lblcamname = cname
      self.lblcamstatus = cstatus
      self.btncamsetup.values = csetup
    return r

  def WriteConfig(self):
    cfg = {}
    cfg["scenename"] = self.scenename
    cfg["scenecount"] = self.scenecount
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
  
  def GetCameraInformation(self):
    shead = '''
#:kivy 1.9.0

GridLayout:
  size_hint: None, None
  size: root.width, (root.width - root.width/12*4)/3*2 + root.width/6 + root.width/25*1
  spacing: root.width/12, root.width/25
  padding: root.width/12, root.width/6, root.width/12, 0
  cols: 3
'''

    sdetail = '''
  Button:
    background_normal: '{$background}'
    background_down: '{$background}'
    text_size: self.size
    font_size: root.width/35
    halign: 'center'
    valign: 'bottom'
    text: '{$text}'
    markup: True
'''
    for i in range(self.cameras):
      shead += sdetail.replace("{$background}",self.btncamstatus[i]).replace("{$text}",self.lblcamtext[i])
    return shead.replace("root.width",str(self.width))

  def BuildCameraInformation(self, *largs):
    txt = self.GetCameraInformation()
    if txt == self.textcaminfo:
      return
    kv_container = self.current_screen.children[0]
    for child in kv_container.children[:]:
      if isinstance(child, GridLayout):
        kv_widget = child
        break
    try:
      parser = Parser(content=txt)
      kv_container.remove_widget(kv_widget)
      widget = Factory.get(parser.root.name)()
      Builder._apply_rule(widget, parser.root, parser.root)
      kv_container.add_widget(widget)
      self.textcaminfo = txt
    except (SyntaxError, ParserException) as e:
      print "SyntaxError, ParserException", e
    except Exception as e:
      print "Exception", e
      
  def RefreshCameraInformation(self, timewait = 0):
    Clock.unschedule(self.BuildCameraInformation)
    if timewait == 0:
      Clock.schedule_once(self.BuildCameraInformation)
    else:
      Clock.schedule_once(self.BuildCameraInformation, timewait)

  def GetConnectTitle(self):
    sbuild = '''
#:kivy 1.9.0

BoxLayout:
  orientation: 'horizontal'
  canvas:
    Color: 
      rgba: 0.95,0.95,0.95,1
    Rectangle:
      size: self.size
      pos: self.pos
  size_hint: None, None
  size: root.width, root.width/15 + root.width/20
  padding: root.width/40, root.width/40, root.width/20, root.width/40
  spacing: root.width/40
  Button:
    size_hint: None, None
    size: root.width/15, root.width/15
    background_normal: 'ximage/logo.png'
    background_down: 'ximage/logo.png'
  Label:
    text_size: self.size
    size_hint: None, None
    size: root.width-(root.width/15+root.width/15*5+root.width/40*3+root.width/20), root.width/15
    halign: 'left'
    valign: 'middle'
    color: 0,0,0,1
    font_size: root.width/25
    text: '[size=%d]Ponerine.[/size][size=%d][b]X[/b][/size][sub] %s[/sub]' %(root.width/22,root.width/18,app.version)
    markup: True
  Spinner:
    size_hint: None, None
    size: root.width/15*5, root.width/15
    text_size: self.size
    halign: 'right'
    valign: 'middle'
    color: 0,0,1,1
    values: ("Camera 1","Camera 2","Camera 3","Camera 4","Camera 5","Camera 6","Advanced")
    background_normal: 'ximage/setting.png'
    background_down: 'ximage/setting.png'
'''
    return sbuild.replace("root.width",str(self.width)) #.replace("{$disabled}",self.setupdisabled)

  def BuildConnectTitle(self, *largs):
    t1 = time.time()
    if t1 - self.timecontitle < 30.0: #allow update every 30seconds
      return
    txt = self.GetConnectTitle()
    #print txt
    #print "BuildConnectTitle"
    kv_container = self.current_screen.children[0]
    for child in kv_container.children[:]:
      if isinstance(child, BoxLayout):
        kv_widget = child
        break
    try:
      parser = Parser(content=txt)
      kv_container.remove_widget(kv_widget)
      widget = Factory.get(parser.root.name)()
      Builder._apply_rule(widget, parser.root, parser.root)
      for child in widget.children[:]:
        if isinstance(child, Button):
          if isinstance(child, Spinner):
            print "Spinner", child
            child.bind(text=self.ConfigPopupOpen)
            self.btncamsetup = child
          else:
            print "Button", child
            child.bind(on_release=self.RefreshAllControls)
      kv_container.add_widget(widget)
      #self.current_screen.ids['btnCamSetup'].bind(text=self.ConfigPopupOpen) #.btnCamSetup.text #bind(on_text=self.ConfigPopupOpen)
      self.timecontitle = t1
    except (SyntaxError, ParserException) as e:
      print "BuildConnectTitle: SyntaxError, ParserException", e
    except Exception as e:
      print "BuildConnectTitle: Exception", e

  def RefreshConnectTitle(self, timewait = 0):
    Clock.unschedule(self.BuildConnectTitle)
    if timewait == 0:
      Clock.schedule_once(self.BuildConnectTitle)
    else:
      Clock.schedule_once(self.BuildConnectTitle, timewait)
  
  def GetConnectControl(self):
    shead = '''
#:kivy 1.9.0

AnchorLayout:
  anchor_x: 'center'
  anchor_y: 'bottom'
  size_hint: None, None
  size: root.width, root.height * 0.95
  GridLayout:
    size_hint: None, None
    size: root.width, root.width/6 + root.width/12 + (root.width - root.width/12*4)/3
    spacing: root.width/12, 0
    padding: root.width/12, root.width/6, root.width/12, 0
    cols: 3
    Label:
      size_hint: 1, None
      height: root.width/12
    Label:
      size_hint: 1, None
      height: root.width/12
      text_size: self.size
      font_size: root.width/30
      text: "{$recordtime}"
      halign: 'center'
      valign: 'top'
      markup: True
    Label:
      size_hint: 1, None
      height: root.width/12
    '''
    sdetail = '''
    Button:
      size_hint: 1, None
      height: (root.width - root.width/12*4)/3
      color: {$color}
      disabled_color: {$disabled_color}
      disabled: {$disabled}
      text: "{$text}"
      font_size: root.width/38
      text_size: self.size
      halign: 'center'
      valign: 'middle'
      background_normal: '{$background_normal}'
      background_down: '{$background_down}'
      background_disabled_normal: '{$background_disabled_normal}'
      background_disabled_down: '{$background_disabled_down}'
      always_release: False
      '''
    sbtnbuzzer = sdetail
    for key, value in self.btnconctrl[0].items():
      sbtnbuzzer = sbtnbuzzer.replace("{$%s}" %key, value)
    sbtnrecord = sdetail
    for key, value in self.btnconctrl[1].items():
      sbtnrecord = sbtnrecord.replace("{$%s}" %key, value)
    sbtnpreview = sdetail
    for key, value in self.btnconctrl[2].items():
      sbtnpreview = sbtnpreview.replace("{$%s}" %key, value)
    stime = "[color=0000ff]%s - %d[/color]\\n" %(self.scenename,self.scenecount) + ("[color=ff0000]%s[/color]" %self.recordtime if self.recordtime <> "" else "")
    shead = shead.replace("{$recordtime}",stime)
    #shead = shead.replace("{$recordtime}","11.22.33")
    shead += sbtnbuzzer + sbtnrecord + sbtnpreview
    #print shead.replace("root.width",str(self.width)).replace("root.height",str(self.height))
    return shead.replace("root.width",str(self.width)).replace("root.height",str(self.height))

  def BuildConnectControl(self, *largs):
    txt = self.GetConnectControl()
    if txt == self.textctrlbtn:
      return
    kv_container = self.current_screen.children[0]
    kv_widget = kv_container.children[0]
    for child in kv_container.children[:]:
      if isinstance(child, AnchorLayout):
        kv_widget = child
        break
    try:
      parser = Parser(content=txt)
      if isinstance(kv_widget, AnchorLayout):
        kv_container.remove_widget(kv_widget)
      widget = Factory.get(parser.root.name)()
      Builder._apply_rule(widget, parser.root, parser.root)
      widget.children[0].children[2].bind(on_release=self.Connect)
      widget.children[0].children[1].bind(on_release=self.Record)
      widget.children[0].children[0].bind(on_release=self.Buzzer)
      self.btnpreview = widget.children[0].children[0]
      self.btnrecord = widget.children[0].children[1]
      self.btnbuzzer = widget.children[0].children[2]
      #self.lblscenecount = widget.children[0].children[3]
      self.lblrecordtime = widget.children[0].children[4]
      #self.lblscenename = widget.children[0].children[5]
      #print "self.lblrecordtime.text",self.lblrecordtime.text
      kv_container.add_widget(widget)
      self.textctrlbtn = txt
    except (SyntaxError, ParserException) as e:
      print "BuildConnectControl: SyntaxError, ParserException", e
    except Exception as e:
      print "BuildConnectControl: Exception", e
      
  def DoRefreshConnectControl(self):
    time.sleep(30)
    while True:
      time.sleep(30)
      print "DoRefreshConnectControl"
      self.RefreshConnectControl()
  
  def RefreshConnectControl(self, timewait = 0):
    Clock.unschedule(self.BuildConnectControl)
    if timewait == 0:
      Clock.schedule_once(self.BuildConnectControl)
    else:
      Clock.schedule_once(self.BuildConnectControl, timewait)
      
  def RefreshAllControls(self, btnicon):
    #pngfile = __file__.replace(basename(__file__), ("data/%s-.png" %time.ctime()).replace(':',''))
    #Window.screenshot(name=pngfile)
    #time.sleep(1)
    #print "RefreshAllControls"
    #self.textctrlbtn = ""
    #*#self.RefreshConnectControl(1)
    #self.textcaminfo = ""
    #self.RefreshCameraInformation(1)
    #print self.timecontitle
    self.timecontitle = 0.0
    self.RefreshConnectTitle()
    
class XPonerineApp(App):
  version = __version__
  def build(self):
    self.appexit = threading.Event()
    evt = []
    evt.append(self.appexit)
    xponerine = XPonerine(evt)
    xponerine.duration = 0.7

    xponerine.screen = [XConnectScreen(name="mconnect")]
    xponerine.switch_to(xponerine.screen[0])
    xponerine.InitialCamIcon()
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
