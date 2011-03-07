#!/usr/bin/python2
# -'- encoding=utf-8 -*-

import subprocess as sp
import sys,time,os
from functools import reduce
from bitstring import BitArray

"""
class akai():
    def __init__(self):
        self.port = self.getport()
        self.programs=[]
        self.samples=[]
        
        self.version = ''
        self.maxblocks = 0
        self.freeblocks = 0
        self.maxwords = 0
        self.freewords = 0
        self.sysexchannel = 0

    def getstatus(self):
        data = self.request('F0 47 00 00 48 F7')




    def getport(self):
        p = sp.Popen(['amidi','-l'],stdout=sp.PIPE)
        out = p.stdout.readlines()
        m = ''
        port = ''
        for line in out:
            if line.find('hw') != -1:
                if line.find('USB Midi Cable') != -1:
                    port = line.split()[1]
                    m = line[4:-1]
                elif line.find('Keystation') != -1 and not port:
                    port = line.split()[1]
                    m = line[4:-1]
        print 'Using port',m
        return port

    def deletesample(self,number):
        lst =  ['F0 47 00 14 48',numberstring(number), 'F7']
        self.send(' '.join(lst))

    def deleteprogram(self,number):
        lst =  ['F0 47 00 12 48',numberstring(number), 'F7']
        self.send(' '.join(lst))

    def renamesample(self,number,name):
        lst = ['F0 47 00 2C 48',numberstring(number),'03 00 0C 00', str_to_akai(name), 'F7']
        self.send(' '.join(lst))

    def renameprogram(number,name):
        lst = ['F0 47 00 28 48', numberstring(number),'03 00 0C 00', str_to_akai(name), 'F7']
        self.send(' '.join(lst))

    def handlefile(self,path,number):
        d,f = os.path.split(path)
        filename, ext = os.path.splitext(f)
        lst = []
        for i in filename.upper():
            if i in alph:
                lst.append(i)
        name = ''.join(lst)
        print 'converting',f
        sp.call(['sox',path,'-t','.sds','-r','44100','-b','16','-D','-c','1',filename+'.sds'])
        #sp.call(['2sds',filename])
        #sp.call(['sendsds',filename[:-4]+'.sds'])
        print 'sending',filename+'.sds','over sysex'
        sp.call(['amidi','-p','hw:1,0,0','-s',filename+'.sds'])
        time.sleep(1)
        sp.call(['rm',filename+'.sds'])
        print 'renaming sample to', name
        renamesample(number,name)
        time.sleep(1)


    def dump_plist(self):
        data = self.request('F0 47 00 02 48 F7').split()#format: f0,47,cc,PLIST,48,pp,pp, NAMES, f7
        num = int(data[5],16) #number of resident programs
        index = 7 #ab dem 8ten byte kommen die namen
        programs = []
        for i in range(num):
            print i, akai_to_str(data[index:index+12])
            programs.append(akai_to_str(data[index:index+12]))
            index = index+12
        return programs

    def dump_slist(self):
        data = self.request('F0 47 00 04 48 F7').split()#format: f0,47,cc,PLIST,48,pp,pp, NAMES, f7
        num = int(data[5],16) #number of resident programs
        index = 7 #ab dem 8ten byte kommen die namen
        for i in range(num):
            print i, akai_to_str(data[index:index+12])
            index = index+12

    def dump_pdata(self,number):
        data = self.request('F0 47 00 06 48 '+numberstring(number)+' F7').split()
        print data
        name = data[39:51]
        print number
        self.programs[number] = akai_to_str(name)

    def request(self,reqstring):
        p = sp.Popen(['amidi','-p',port,'-d','-t','1'],stdout=sp.PIPE) #prepare dump, one second timeout
        self.send(reqstring) #request program list
        data = p.stdout.readlines()
        return data

    def send(self,s):
        sp.call(['amidi','-p',port,'-S',s])
        print s
"""




#erstmal ein paar Hilfsfunktionen:

port = ''
port = 'hw:1,0,0'


def convert_nibbles(nibbles):
   it = iter(nibbles)
   l = list(zip(it, it))
   l2 = []
   for i in l:
       l2.append( ''.join([i[1][1],i[0][1]]) ) #führende Null raushauen und bytes in die richtige Reihenfolge bringen
   return l2

def signed_int(string):
    a = BitArray(hex=string)
    return a.int

def toInt(s):
    return int(s.replace(' ',''),16)

def toHex(s): # String nach Hex
    lst = []
    for ch in s.upper():
        hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0'+hv
        lst.append(hv)
    
    return reduce(lambda x,y:x+y, lst)

def inthex(i):
    return hex(i).replace('0x','')

def reverse(s):
    return ''.join(reversed(s)) 

def numberstring(number):
    numeral = inthex(number).upper()
    numeral = reverse(numeral).ljust(3,'0')
    lst = []
    for i in numeral:
        lst.append(i.rjust(2,'0'))
    return ' '.join(lst)



#generate alphabet:
alph = '0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZ#+-.'
pitch = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

def num_to_pitch(number):
    number = number-24 #offset nach spezifikation
    global pitch
    octave = int(number / 12)
    a = pitch[number % 12]
    return ''.join([a,str(octave)])

def akai_to_str(akai):
    global alph
    if type(akai) == str:
        akai = akai.split()
    s = []
    for i in akai:
#        print int(i,16)
        s.append( alph[int(i,16)] )
    return ''.join(s)


def str_to_akai(s):
    global alph
    lst = []
    for i in s.upper():
        if i in alph:
            lst.append(i)
    s = ''.join(lst)
    if len(s) > 12:
        s = s[:12]
    lst = []
    s = s.ljust(12,' ')
    for i in s.upper():
        num = alph.index(i)
        num = inthex(num).upper()
        num = reverse(num).ljust(2,'0')
        for j in num:
            lst.append(j.rjust(2,'0'))
    return ' '.join(lst)


#Hauptfunktionen:
#allgemein Sysex: F0 47 00 <function> 48 <bytes> F7
#F0 Exclusive
#47 Akai
#00 exclusive channel(0-127)
status = {}
def getstatus():
    global status
    data = request('F0 47 00 00 48 F7')
    status['blocks'] = int(''.join(data[7:9]),16)
    status['blocks_free'] = int(''.join(data[9:11]),16)
    status['version'] = str(toInt(data[6]))+'.'+str(toInt(data[7]))
    status['words'] = 0
    status['words_free'] = 0
    return status

def deletesample(number):
    lst =  ['F0 47 00 14 48',numberstring(number), 'F7']
    send(' '.join(lst))

def deleteprogram(number):
    lst =  ['F0 47 00 12 48',numberstring(number), 'F7']
    send(' '.join(lst))

def renamesample(number,name):
    lst = ['F0 47 00 2C 48',numberstring(number),'03 00 0C 00', str_to_akai(name), 'F7']
    send(' '.join(lst))

def renameprogram(number,name):
    lst = ['F0 47 00 28 48', numberstring(number),'03 00 0C 00', str_to_akai(name), 'F7']
    send(' '.join(lst))

def handlefile(path,number):
    d,f = os.path.split(path)
    filename, ext = os.path.splitext(f)
    lst = []
    for i in filename.upper():
        if i in alph:
            lst.append(i)
    name = ''.join(lst)
    print('converting',f)
    sp.call(['sox',path,'-t','.sds','-r','44100','-b','16','-D','-c','1',filename+'.sds'])
    #sp.call(['2sds',filename])
    #sp.call(['sendsds',filename[:-4]+'.sds'])
    print('sending',filename+'.sds','over sysex')
    sp.call(['amidi','-p','hw:1,0,0','-s',filename+'.sds'])
    time.sleep(1)
    sp.call(['rm',filename+'.sds'])
    print('renaming sample to', name)
    renamesample(number,name)
    time.sleep(1)

def dump_plist():
    data = request('F0 47 00 02 48 F7').split()#format: f0,47,cc,PLIST,48,pp,pp, NAMES, f7
    num = int(data[5],16) #number of resident programs
    index = 7 #ab dem 8ten byte kommen die namen
    for i in range(num):
        print(i, akai_to_str(data[index:index+12]))
        index = index+12

def dump_slist():
    data = request('F0 47 00 04 48 F7').split()#format: f0,47,cc,PLIST,48,pp,pp, NAMES, f7
    num = int(data[5],16) #number of resident programs
    index = 7 #ab dem 8ten byte kommen die namen
    for i in range(num):
        print(i, akai_to_str(data[index:index+12]))
        index = index+12
    
def sampleinfo(number):
    data = request('F0 47 00 0A 48 '+numberstring(number)+' F7').split()
    data = data[5:-1] # strip sysex header and eox
    data = convert_nibbles(data) # ein paar = ein byte daten, schon umgedreht,
    sample = {}
    try:
        sample['number'] = int(data[0],16)
        sample['pitch'] = num_to_pitch( int(data[3],16) )
        if toInt(data[2]) == 1:
            sample['samplerate'] = 44100
        else:
            sample['samplerate'] = 22050
        sample['name'] = akai_to_str(data[4:16])
        sample['loops'] = toInt(data[17])
        if toInt(data[20]) == 0:
            sample['loop_mode'] = 'lp in release'
        elif toInt(data[20]) == 1:
            sample['loop_mode'] = 'lp to release'
        elif toInt(data[20]) == 2:
            sample['loop_mode'] = 'no looping'
        elif toInt(data[20]) == 3:
            sample['loop_mode'] = 'one-shot'
        sample['detune'] = str(signed_int(data[22]))+'.'+str(signed_int(data[21])) #cent detune geht noch nicht TODO
        sample['words'] = int(''.join(data[26:30]),16)
    except:
        print('Sample',number,'does not exist')
    return data,sample


def request(reqstring):
    p = sp.Popen(['amidi','-p',port,'-d','-t','1'],stdout=sp.PIPE) #prepare dump, one second timeout
    send(reqstring) #request program list
    data = str(p.stdout.readlines()[1])
    return data

def send(s):
    sp.call(['amidi','-p',port,'-S',s])
    #print(s)

if __name__ == '__main__':
    a = 1
    try:
        offset = int(sys.argv[1])
        a = a + 1
    except:
        offset = 0
    c = offset
    for i in sys.argv[a:]:
        handlefile(i,c)
        c = c + 1


