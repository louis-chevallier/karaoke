import tkinter as tk
from queue import Queue, Empty

class Gui:
    def __init__(self, users):
        self.q=Queue()
        self.root=tk.Tk()
        self.root.title("Utilisateurs")
        self.labels={}
        for u in users:
            l=tk.Label(self.root,text=u,width=20,anchor="w",font=("Arial",14))
            l.pack(padx=5,pady=2)
            self.labels[u]=l
        self.root.after(100,self.poll)

    def flash(self,user,color="yellow"):
        if user not in self.labels:return
        lbl=self.labels[user]
        old=lbl.cget("bg")
        lbl.configure(bg=color)
        self.root.after(600,lambda: lbl.configure(bg=old))

    def poll(self):
        try:
            while True:
                user,val=self.q.get_nowait()
                self.flash(user,"lightgreen" if val=="yes" else "tomato")
        except Empty:
            pass
        self.root.after(100,self.poll)

    def run(self):
        self.root.mainloop()
