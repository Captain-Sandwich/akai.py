import wx
import pygame.midi as pm
import thread
import akai

dummy=[]
parameters = {'Filter Cutoff':{'function':akai.cutoff,
                                'range':99},
            'Filter Resonance':{'function':akai.resonance,
                                'range':15},
            'LFO1 Speed':{'function':dummy,
                                'range':99},
            'LFO1 depth':{'function':dummy,
                                'range':99}
            }

class Midi():
    def __init__(self,parent):
        global parameters
        self.parent = parent
        self.midi_in = None
        self.midi_out = None
        self.mapping = {1:['Filter Cutoff',0],74:['Filter Cutoff',0],71:['Filter Resonance',0]} #tuple is (FUNCTION NAME,PROGRAM NUMBER)
        self.mapping = {}
        self.running = False
        self.thread = None
    
    def connect_Input(self,ID):
        if self.midi_in:
            self.midi_in.close() #Disconnect auf existierende Ports
        self.midi_in = pm.Input(ID)

    def connect_Output(self,ID):
        if self.midi_out:
            self.midi_out.close()
        self.midi_out = pm.Output(ID)

    def handle_forever(self):
        self.thread = thread.start_new_thread(self.midihandle,())
    
    def stop_handling(self):
        self.running = False

    def midihandle(self):
        self.running=True
        keys = self.mapping.keys()
        while self.running:
            if self.midi_in.poll():
                a = self.midi_in.read(1)[0][0] #a ist jetzt eine liste [midistatus,byte1,byte2] zb [note_on,note,velocity]
                print a
                if a[0] == 176 and a[1] in keys:
                    thread.start_new(self.changeParameter,(a[1],a[2])) #handle midi write in different thread, a[1],a[2] = controller,value
                else:
                    thread.start_new(self.writethrough,(a,)) #handle midi write in different thread, this is write-through
    
    def writethrough(self,event):
        self.midi_out.write([[event,0]])

    def changeParameter(self,controller,value):
        global parameters
        tuplelist = self.mapping[controller]
        for i in tuplelist:
            print i
            target,number,controller = i
            func = parameters[target]['function']
            r = parameters[target]['range'] #get range
            value_scaled = int(value/(float(127)/float(r))) #scale to full 127 midi cc range
            print r,value,value_scaled
            s = func(number,value_scaled) #s is a list of hex or int 'bytes' eg [0xF0,0x7D,0x10,0x11,0x12,0x13,0xF7]
                                   #func sets the parameter in program number to value
            s = akai.dec(s)
            self.midi_out.write_sys_ex(0,s) #write it immediately
            controller.SetValue(value_scaled)

    def GetPorts(self):
        i = {}
        o = {}
        for j in range(pm.get_count()):
            s,name,ins,outs,throughs = pm.get_device_info(j)
            if ins > 0:
                i[name] = j
            if outs > 0:
                o[name] = j
        return (i,o)

    def refresh(self):
        pm.init()

    def clear_buffer(self):
        if self.midi_in:
            self.midi_in.read(1024)



class Controller(wx.Panel):
    def __init__(self,parent,pos,size=(900,900)):
        global parameters
        self.parent = parent
        wx.Panel.__init__(self,parent,-1,pos=pos,size=size)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.parlist = parameters.keys()
        self.parlist.sort()
        self.cc = 0 #Standard: Modwheel
        self.parameter = self.parlist[0]
        self.program = 0
        self.value = 0
        self.combo = wx.ComboBox(self,-1,"Parameter",(0,0),(120,-1),
                self.parlist ,wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER|wx.CB_SORT)
        self.spin = wx.SpinCtrl(self,-1,"Program No",(135,0),(50,-1))
        self.ccspin = wx.SpinCtrl(self,-1,"Midi CC",(200,0),(50,-1))
        self.gauge = wx.Gauge(self,-1,300,(245,0),(250,25))

        self.Bind(wx.EVT_COMBOBOX,self.OnSelect,self.combo)
        self.Bind(wx.EVT_SPINCTRL,self.OnSpin,self.spin)
        self.Bind(wx.EVT_SPINCTRL,self.OnCCSpin,self.ccspin)

        self.Bind(wx.EVT_TIMER,self.TimerHandler)
        self.timer = wx.Timer(self)
        self.timer.Start(100)
    
    def TimerHandler(self,event):
        if self.cc != 0:
            print self.value
        self.gauge.SetValue(self.value)

    def SetValue(self,value):
#        self.gauge.SetValue(value)
        self.value = value
    def OnSpin(self,event):
        self.program = self.spin.GetValue()
        self.UpdateMapping()

    def OnSelect(self,event):
        global parameters
        self.parameter = self.combo.GetValue()
        self.gauge.SetRange(parameters[self.parameter]['range'])
        self.UpdateMapping()
    def OnCCSpin(self,event):
        self.cc = self.ccspin.GetValue()
        self.UpdateMapping()
    def UpdateMapping(self):
        print 'Update Mapping',self
        m = self.parent.midi_handler.mapping
        for cc,tlist in m.iteritems():
            for i in m[cc]:
                if self in i:
                    print 'removing previous entry'
                    n = m[cc].index(i)
                    m[cc].pop(n)
        if self.cc == 0: #Ignore midiCC 0
            return True
        if self.cc not in m.keys(): 
            m[self.cc] = []
        m[self.cc].append([self.parameter,self.program,self])
        self.parent.midi_handler.stop_handling()
        self.parent.midi_handler.handle_forever()

class myPanel(wx.Panel):
    def __init__(self,parent,midi_handler):
        wx.Panel.__init__(self,parent,-1)
        self.count = 0
        self.midi_handler = midi_handler
        self.midi_ins,self.midi_outs = self.midi_handler.GetPorts()

        wx.StaticText(self,-1,"Midi to Sysex Mapper",(15,15))
        self.button = wx.Button(self,-1,"PORSDONVS",(150,15),(120,-1))
        self.Bind(wx.EVT_BUTTON,self.OnButton,self.button)
        self.controllers = []
        y = 50
        for i in range(8):
            y = y+50
            self.controllers.append(Controller(self,(15,50+i*50),(900,900)))
        self.midicombo_in = wx.ComboBox(self,-1,"Midi Input",(15,y),(200,-1),
                self.midi_ins.keys(), wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER|wx.CB_SORT)
        self.midicombo_out = wx.ComboBox(self,-1,"Midi Output",(215,y),(200,-1),
                self.midi_outs.keys(), wx.CB_DROPDOWN|wx.TE_PROCESS_ENTER|wx.CB_SORT)
        self.Bind(wx.EVT_COMBOBOX,self.OnInputSelect,self.midicombo_in)
        self.Bind(wx.EVT_COMBOBOX,self.OnOutputSelect,self.midicombo_out)


    def OnButton(self,event):
        if self.midi_handler.midi_in and self.midi_handler.midi_out:
            print "Routing Start"
            self.midi_handler.clear_buffer()
            self.midi_handler.handle_forever()
            self.GenerateMapping()
        else:
            print 'Choose Midi Ports first'

    def OnInputSelect(self,event):
        name = self.midicombo_in.GetValue()
        ID = self.midi_ins[name]
        print name,ID
        self.midi_handler.connect_Input(ID)

    def OnOutputSelect(self,event):
        name = self.midicombo_out.GetValue()
        ID = self.midi_outs[name]
        print name,ID
        self.midi_handler.connect_Output(ID)

    def GenerateMapping(self):
        l = {}
        for i in self.controllers:
            i.UpdateMapping()


class myFrame(wx.Frame):
    def __init__(self, title='title',pos=wx.DefaultPosition,size=wx.DefaultSize,style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self,None, title=title, size=size,style=style)
        self.midi_handler = Midi(self)
        self.panel = myPanel(self,self.midi_handler)
        self.Bind(wx.EVT_CLOSE,self.OnCloseWindow)

    def OnCloseWindow(self,event):
        self.Destroy()

pm.init()
app = wx.App()
top = myFrame()
top.Show()
app.MainLoop()

