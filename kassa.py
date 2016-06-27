#!/usr/bin/python
# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import glob
import importlib
import time
import json
import pickle
import copy
import sys

sessions={}

class log:
    pass

class Session:
    SID=""
    plugins={}
    counter=0
    nextcall={}
    prompt=""
    help={}
    cache={}

    def import_from(self, module, name):
        module = __import__(module, fromlist=[name])
        return getattr(module, name)

    def __init__(self,SID,client):
        self.SID=SID
        self.client=client
        self.plugins={}

    def startup(self):
        print "Startup",self.SID
        for fname in glob.glob("plugins/*.py"):
            plugname=fname.split("/")[1].rstrip(".py")
            if plugname!='__init__' and not plugname in self.plugins:
                if plugname in sys.modules:
                    del sys.modules[plugname]
        print self.plugins
        for fname in glob.glob("plugins/*.py"):
            plugname=fname.split("/")[1].rstrip(".py")
            if plugname!='__init__' and not plugname in self.plugins:
                if plugname in sys.modules:
                    del sys.modules[plugname]
                self.plugins[plugname]= self.import_from('plugins.'+plugname,plugname)(self.SID,self)
                print plugname,self.import_from('plugins.'+plugname,plugname)
                self.send_message(True,'message','loaded plugin '+plugname);
                try:
                    self.help.update(self.plugins[plugname].help())
                except:
                    pass
        self.receipt=self.plugins['receipt']
        self.accounts=self.plugins['accounts']
        self.products=self.plugins['products']
        self.log=self.plugins['log']
        self.POS=self.plugins['POS']
        self.counter+=1
        self.send_message(False,'message','Please wait while loading...');
        for plug in self.plugins:
            self.plugins[plug].startup()
        self.send_message(True,'commands',json.dumps(self.help))
        self.send_message(True,'message','Enter product, command or username');
        print self.plugins


    def realcallhook(self,hook,arg):
        for plug in self.plugins:
            try:
                getattr(self.plugins[plug], 'hook_'+hook)
                try:
                    getattr(self.plugins[plug], 'hook_'+hook)(arg)
                except:
                    import traceback
                    print traceback.format_exc()
            except AttributeError:
                pass

    def callhook(self,hook,arg):
        self.realcallhook('pre_'+hook,arg);
        self.realcallhook(hook,arg);
        self.realcallhook('post_'+hook,arg);

    def donext(self,plug,function):
        self.nextcall={'plug': plug, 'function': function}

    def input(self,text):
        if text=="":
            self.send_message(True,'message',"Enter product, command or username")
            self.send_message(True,'buttons',json.dumps({}))
            return True
        self.buttons={}
        done=0
        for plug in self.plugins:
            try:
                self.plugins[plug].pre_input(text)
            except AttributeError:
                pass
            except:
                import traceback
                print traceback.format_exc()

        self.prompt=""
        if self.nextcall!={}:
            try:
                print(text)
                print(self.nextcall)
                plug=self.nextcall['plug']
                func=self.nextcall['function']
                self.nextcall={}
                print(getattr(plug,func))
                if getattr(plug,func)(text):
                    done=1
            except:
                import traceback
                print(traceback.format_exc())
        if done==1:
            print("Call done with self.nextcall")
        elif done==0:
            for part in text.split():
              if part!='':
                done=0
                print("Running part",part,self.nextcall)
                self.prompt=""
                if self.nextcall!={}:
                    try:
                        plug=self.nextcall['plug']
                        func=self.nextcall['function']
                        self.nextcall={}
                        if getattr(plug,func)(part):
                            done=1
                    except:
                        import traceback
                        print(traceback.format_exc())
                if done==0:
                  for plug in self.plugins:
                    try:
                        if self.plugins[plug].input(part):
                            done=1
                            break;
                    except AttributeError:
                        import traceback
                        print(traceback.format_exc())
                        pass
                    except:
                        import traceback
                        print(traceback.format_exc())
                if done==0:
                    if self.plugins['withdraw'].withdraw(part):
                        done=1
                    if self.plugins['accounts'].newuser(part):
                        done=1
        if done==1 and self.prompt=="":
            self.send_message(True,'message',"Enter product, command or username")
        elif self.prompt=="":
            self.send_message(True,'message',"Unknown product, command or username")
            self.callhook('wrong',())
        if self.nextcall=={} and self.buttons=={}:
            self.send_message(True,'buttons',json.dumps({}))

    def send_message(self,retain,topic,message) :
        if not 'hack42bar/output/session/'+self.SID+'/'+topic in self.cache or self.cache['hack42bar/output/session/'+self.SID+'/'+topic]!=message or len(topic)<8:
            print(retain,'hack42bar/output/session/'+self.SID+'/'+topic,":",message)
            self.cache['hack42bar/output/session/'+self.SID+'/'+topic]=message
            if topic=="message":
                self.prompt=message
            if topic=="buttons":
                self.buttons=message
            self.client.publish('hack42bar/output/session/'+self.SID+'/'+topic,message,1,retain)


def get_session(SID,client):
    global sessions
    if not SID in sessions:
        print "Starting new session",SID
        sessions[SID]=Session(SID,client)
        sessions[SID].startup()
        client.publish('hack42bar/output/sessions',json.dumps(sessions.keys()))
    return sessions[SID]

def run_session(client,SID,action,data):
    if action=='input':
        session=get_session(SID,client)
        session.input(data)
    else:
        print("unhandled",action)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("hack42bar/input/#")

def on_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))
    elms=msg.topic.split("/")
    msg=msg.payload
    if len(elms)<3: return;
    #try:
    run_session(client,elms[3],elms[4],msg)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_start()
while True:
    time.sleep(1)
#client.loop_forever()
