import json
import os

class historie:

    def __init__(self,SID,master):
        self.master=master
        self.SID=SID


    def reverse_readline(self,filename, buf_size=8192):
        """a generator that returns the lines of a file in reverse order"""
        with open(filename) as fh:
            segment = None
            offset = 0
            fh.seek(0, os.SEEK_END)
            file_size = remaining_size = fh.tell()
            while remaining_size > 0:
                offset = min(file_size, offset + buf_size)
                fh.seek(file_size - offset)
                buffer = fh.read(min(remaining_size, buf_size))
                remaining_size -= buf_size
                lines = buffer.split('\n')
                # the first line of the buffer is probably not a complete line so
                # we'll save it and append it to the last line of the next buffer
                # we read
                if segment is not None:
                    # if the previous chunk starts right from the beginning of line
                    # do not concact the segment to the last line of new chunk
                    # instead, yield the segment first 
                    if buffer[-1] is not '\n':
                        lines[-1] += segment
                    else:
                        yield segment
                segment = lines[0]
                for index in range(len(lines) - 1, 0, -1):
                    if len(lines[index]):
                        yield lines[index]
            # Don't yield None if the file was empty
            if segment is not None:
                yield segment

    def reversesearch(self,text):
        lines=[]
        for line in self.reverse_readline("data/revbank.log"):
          if line.find(text)>0:
            lines.insert(0,line)
          if len(lines)>100:
            return lines
        return lines

    def help(self):
        return {"history": "User History"}

    def history(self,text):
        if text in self.master.accounts.accounts:
            lines=self.reversesearch(text)
            self.master.send_message(False,'history',json.dumps(lines))
            self.master.send_message(True,'buttons',json.dumps({'special':'history'}))
            return True
        elif text=="abort":
            self.master.callhook('abort',None)
            return True
        else:
            self.master.donext(self,'history')
            self.master.send_message(True,'message','Unknown User; User to view history from?')
            self.master.send_message(True,'buttons',json.dumps({'special':'accounts'}))
            return True

    def input(self,text):
        if text=="history":
            self.master.donext(self,'history')
            self.master.send_message(True,'message','User to view history from?')
            self.master.send_message(True,'buttons',json.dumps({'special':'accounts'}))
            return True

    def startup(self):
        pass
