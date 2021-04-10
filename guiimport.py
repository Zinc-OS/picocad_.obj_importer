"""
A simple user interface for importobj.py that can be built using pyinstaller
to make versions that work on every os without the command line!
"""

# this is the module that we're providing a UI for
import importobj
# this is used for creating the UI
import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askdirectory
# these two are used for redirecting the print output to a display in the UI
import contextlib
import io
# these is for help with figuring out what folder path to export to!
import sys
import os
from pathlib import Path


class FloatEntry(tk.Entry):
	def __init__(self, master, initial_value, *args, **kwargs):
		self.textvariable = tk.StringVar()
		self.textvariable.set(str(initial_value))
		self.valCommand = (master.register(self.float_validate),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
		self.invalCommand = (master.register(self.float_invalid),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
		tk.Entry.__init__(self, master, *args, **kwargs, textvariable = self.textvariable, validatecommand = self.valCommand, invalidcommand = self.invalCommand, validate = "all")
		self.master = master
		self.float_value = initial_value
		self["validate"] = "all"

	def float_invalid(self, d, i, P, s, S, v, V, W):
		# if it's invalid and it's a period or a space when we're leaving focus then we should set it to zero!
		# print(self["validate"])
		# I think I could put this code in the validate function now that I know I need to reset the ["validate"] attribute but for now it works
		if V == "focusout":
			if len(P) == 0 or P == "-" or P == ".":
				self.set_to_value(0)

	def set_to_value(self, value):
		self.float_value = value
		self.textvariable.set(str(value))
		self["validate"] = "all" # for some reason we have to re-enable this after we set the value...

	def float_validate(self, d, i, P, s, S, v, V, W):
		try:
			f = float(P)
			# update our float value!
			self.float_value = f
			return True
		except:

			if len(P) == 0 or P == "-" or P == ".":
				self.float_value = 0
				if V == "focusout":
					return False
				return True # we'll let them do that since they're probably typing .125 or whatever
			return False

class GUIImport(tk.Frame):
	def __init__(self, master):
		tk.Frame.__init__(self, master)
		self.winfo_toplevel().title("OBJ to picoCAD")

		self.error_message_string = tk.StringVar()
		self.input_filepath = tk.StringVar()
		self.output_folderpath = tk.StringVar()
		self.output_folderpath.set(get_save_location()) # start in the picoCAD output folder!

		self.create_ui()

	def create_ui(self):
		# text at the top to explain the tool!
		explain_label = tk.Label(self, text="This tool will convert .obj files into picoCAD files!")
		explain_label.pack()

		help_label = tk.Label(self, text="Select an input file, output file folder,\n" +
							"a scale to multiply the object dimensions by,\nand then press convert!\n")
		help_label.pack()

		# button to select input file
		select_input_file_button = tk.Button(self, text = "Choose Input File", command = self.select_input_file)
		select_input_file_button.pack()

		# input filepath display
		input_filepath_display = tk.Label(self, textvariable=self.input_filepath, wraplength=300, justify="center")
		input_filepath_display.pack()

		# button to select output file
		select_output_file_button = tk.Button(self, text = "Choose Output Folder", command = self.select_output_file)
		select_output_file_button.pack()

		# output filepath display
		input_filepath_display = tk.Label(self, textvariable=self.output_folderpath, wraplength=300, justify="center")
		input_filepath_display.pack()

		scale_entry_label = tk.Label(self, text="Scale:")
		scale_entry_label.pack()

		self.scale_entry = FloatEntry(self, 1)
		self.scale_entry.pack()

		# button to convert the file over!
		convert_button = tk.Button(self, text = "Convert File", command = self.try_import)
		convert_button.pack()

		# status message that explains what the conversion module does!
		error_message_display = tk.Label(self, textvariable=self.error_message_string, wraplength=300, justify="center")
		error_message_display.pack()

	def select_input_file(self):
		input_file = askopenfilename(initialdir = get_save_location(), title = "Select .obj file to Copy In")
		if Path(input_file).exists():
			self.input_filepath.set(input_file)
		else:
			self.error_message_string.set("File Doesn't Exist!")

	def select_output_file(self):
		output_folder = askdirectory(initialdir = get_save_location(), title = "Select .obj file to Copy In")
		if Path(output_folder).exists():
			self.output_folderpath.set(output_folder)
		else:
			self.error_message_string.set("Folder Doesn't Exist!")

	def try_import(self):
		scale = self.scale_entry.float_value
		# redirect the print output from the module into our error display handler!
		if len(self.input_filepath.get()) == 0:
			self.error_message_string.set("Choose an input file!")
			return
		elif len(self.output_folderpath.get()) == 0:
			self.error_message_string.set("Choose an output filepath!")
			return
		elif scale == 0:
			self.error_message_string.set("Scale can't be zero!")
			return
		output_filepath = Path(self.output_folderpath.get()) / Path(Path(self.input_filepath.get()).stem + ".txt")
		if Path(output_filepath).exists():
			# then ask if we want to overwrite it or not!
			should_overwrite = tk.messagebox.askquestion ("Output File Already Exists!",
				"Do you want to overwrite the existing file '" + str(output_filepath) + "'", icon = "warning")
			if should_overwrite != "yes":
				self.error_message_string.set("Canceled due to existing file")
				return
		f = io.StringIO()
		with contextlib.redirect_stdout(f):
			importobj.convert_obj(self.input_filepath.get(), output_filepath, scale)
		self.error_message_string.set(f.getvalue())

def get_save_location():
	# get the picoCAD save folder location for whatever os you're on!
	if sys.platform.startswith("win"):
		p = os.getenv('APPDATA') + "/pico-8/appdata/picocad/"
		return p
	if sys.platform.startswith("darwin"):
		# then it should be a mac!
		return str(Path.home() / Path("/Library/Application Support/pico-8/appdata/picocad/"))
	if sys.platform.startswith("linux"):
		# then it should be linux!
		# do these paths work? Who knows! Someone please tell me :P
		return str(Path.home() / Path(".lexaloffle/pico-8/appdata/picocad/"))
	return "/"

def quit(root):
	# this gets called upon application closing
	root.destroy()



if __name__ == "__main__":
	root = tk.Tk()
	main = GUIImport(root)

	main.pack(side="top", fill="both", expand=True)
	root.protocol("WM_DELETE_WINDOW", lambda : quit(root))
	root.wm_geometry("320x400")
	root.mainloop()