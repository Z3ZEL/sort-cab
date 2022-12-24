#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import tkinter as tk
import PyPDF2
import subprocess
import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import tkinter as tk
from tkinter import filedialog
from googleapiclient.http import MediaFileUpload
import datetime

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

def retrieve_pdf_info(file_path):
    '''Retrieve the pdf info from the file_path.''' 
    if(file_path == ''):
        return
    pdfFileObj = open(file_path, 'rb')
    subprocess.Popen([file_path],shell=True)
def retrieve_folders(service, root_folder_name):
    '''Retrieve the folders from the root folder.'''
    # Retrieve the root folder
    query = "mimeType='application/vnd.google-apps.folder' and trashed = false and name='" + root_folder_name + "'"
    results = service.files().list(q=query,fields="nextPageToken, files(id, name)").execute()
    files = results.get("files", [])
    if not files:
        print('No root folder found.')
        return
    else:
        root_folder = files[0]
        print('Root folder found: ' + root_folder["name"] + ' (' + root_folder["id"] + ')')
    # Retrieve the folders from the root folder 
    query = "mimeType='application/vnd.google-apps.folder' and trashed = false and parents in '" + root_folder["id"] + "'"
    results = service.files().list(q=query,fields="nextPageToken, files(id, name)").execute()
    files = results.get("files", [])
    if not files:
        print('No folders found.')
        return
    else:
        print('Folders found:')
        for file in files:
            print(file["name"] + ' (' + file["id"] + ')')
    return files
def retrieve_folder_from_name(service, folder_name):
    '''Retrieve a folder from its name.'''
    # Retrieve the folder
    query = "mimeType='application/vnd.google-apps.folder' and trashed = false and name='" + folder_name + "'"
    results = service.files().list(q=query,fields="nextPageToken, files(id, name)").execute()
    files = results.get("files", [])
    if not files:
        print('No folder found.')
        return
    else:
        folder = files[0]
        print('Folder found: ' + folder["name"] + ' (' + folder["id"] + ')')
    return folder
def char_to_int(char):
    """Convert a single character to an integer.

    Args:
        char: The character to convert.

    Returns:
        The integer value of the character.
    """
    return ord(char)
def find_folder(folder, folders):
    print(folder.name)
    for f in folders:
        if f.id == folder.id:
            return f
    print("name not found")
    return None

#CLASS
class Windows:
    '''Single object to manage the windows.

    Attributes:

        window: The main window.
        send_button: The send button.
        dialog_box: The dialog box label.

    Methods:

        redraw: Redraw the window.
        write: Write text in the dialog box label.
        clear: Clear the dialog box label.
    '''
    def __init__(self, window,send_button, dialog_box, pdf_info, date_prompt):
        self.send_button = send_button
        self.dialog_box = dialog_box
        self.window = window
        self.pdf_info = pdf_info
        self.date_prompt = date_prompt
    def redraw(self):
        self.window.update()
    def write(self, text):
        '''Write text in the dialog box label.'''
        self.dialog_box.configure(text= self.dialog_box["text"] + '\n' + text)
    def clear(self):
        self.dialog_box.delete(1.0, tk.END)
    def change_button_color(self, color):
        self.send_button.config(bg=color)
    def write_pdf_info(self, text):
        self.pdf_info.configure(text= text)
    def get_date(self):
        if self.date_prompt.get() == '':
            return datetime.datetime.now().strftime("%m-%Y")
        else:
            return self.date_prompt.get()

class FileOrganiser:
    '''Single object to manage the file upload to the Google Drive right folder.
    
    Attributes:
        folders: The list of folders to sort the files into.
        file_to_sort: The path of the current file to sort.
        service: The Google Drive service.
        windows: The windows object.
    
    Methods:
        set_windows: Set the windows object.
        set_file_to_sort: Set the file to sort.
        upload_file: Upload a file to a folder. (internal method)
        class_files : Sort the file in the class folders.
        send_file_to: send the file to the right folder.
    '''

    def __init__(self, service, windows=None):
        self.file_to_sort = None
        self.service = service
        self.windows = windows
    def set_windows(self, windows):
        self.windows = windows
    def set_file_to_sort(self, file):
        self.file_to_sort = file
    def upload_file(self, file_path, folder_id, file_name, subfolder_name):
        '''
        Upload a file to a folder, according to specific root folder

        Args:

            file_path: The path of the file to upload.
            folder_id: The id of the folder to upload the file to.
            file_name: The name of the file to upload.
            subfolder_name: The name of the subfolder to upload the file to.
            root_folder: The name of the root folder to upload the file to.
        '''
        if(file_path == None or file_path == ''):
            self.windows.write("\u2612Aucun fichier sélectionné")
            self.windows.change_button_color("red")
            return
        if(folder_id == None or folder_id == ''):
            self.windows.write("\u2612Aucun dossier sélectionné")
            self.windows.change_button_color("red")
            return
        if(file_name == None or file_name == ''):
            self.windows.write("\u2612Aucun nom de fichier sélectionné")
            self.windows.change_button_color("red")
            return
        if(subfolder_name == None or subfolder_name == ''):
            self.windows.write("\u2612Aucun nom de fichier sélectionné")
            self.windows.change_button_color("red")
            return
        try:
            # Vérifier si le sous-dossier existe
            subfolder_id = None
            query = "mimeType='application/vnd.google-apps.folder' and trashed = false and name='" + subfolder_name + "' and '" + folder_id + "' in parents"
            results = self.service.files().list(q=query,fields="nextPageToken, files(id, name)").execute()
            files = results.get("files", [])
            if not files:
                # Créer le sous-dossier
                file_metadata = {'name': subfolder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [folder_id]}
                file = self.service.files().create(body=file_metadata, fields='id').execute()
                subfolder_id = file.get('id')
            else:
                subfolder_id = files[0].get('id')

            # Téléverser le fichier dans le sous-dossier
            file_metadata = {'name': file_name, 'parents': [subfolder_id]}
            media = MediaFileUpload(file_path, mimetype='application/octet-stream', resumable=True)
            self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            self.windows.write("\u2611Fichier téléversé avec succès")
            self.windows.change_button_color("green")
        except HttpError as error:
            self.windows.write('\u2612Erreur lors du téléversement du fichier: '+ error)
            self.windows.change_button_color("red")
    def class_files(self, name, folders):
        """Classify the files into their respective folders.

        Args:
            files: The list of files to classify.
        """

        if(name == None or name == ''):
            self.windows.write("\u2612Aucun nom de fichier sélectionné")
            self.windows.change_button_color("red")
            return
        
        selected_folders = folders.copy()
        returned_folder = selected_folders.copy()
        char_index = 0;

        while(len(returned_folder) > 1 or char_index < len(name)):
            char_integer = char_to_int(name[char_index])
            for i in range(len(selected_folders)):
                if(len(selected_folders[i].from_index) <= char_index or len(selected_folders[i].to_index) <= char_index):
                    continue
                if(selected_folders[i].from_index[char_index] == selected_folders[i].to_index[char_index] and selected_folders[i].from_index[char_index] != char_integer):
                    f = find_folder(selected_folders[i], returned_folder)
                    if f != None:
                        returned_folder.remove(f)
                elif selected_folders[i].from_index[char_index] > char_integer or selected_folders[i].to_index[char_index] < char_integer:
                    f = find_folder(selected_folders[i], returned_folder)
                    if f != None:
                        returned_folder.remove(f)
            
            char_index += 1
        if len(returned_folder) == 1:
            return returned_folder[0]
        if len(returned_folder) == 0:
            self.windows.write("\u2612Aucun dossier adapté trouvé")
            self.windows.change_button_color("red")
            return None
        
        max_index = 0
        max = len(returned_folder[0].from_index)
        for folder in returned_folder:
            if(len(folder.from_index) > max):
                max = len(folder.from_index)
                max_index = returned_folder.index(folder)
        return returned_folder[max_index]
    def send_file_to(self, name, activity, root_folder):
        """Upload a new file to a folder.

        Args:
            name (str): The name of the file to upload.
            activity (str): The activity of the file to upload.
        """

        # Create the file metadata
        if(name == None or name == ''):
            self.windows.write("\u2612Aucun nom de fichier sélectionné")
            self.windows.change_button_color("red")
            return
        if(root_folder == None):
            self.windows.write("\u2612Aucun dossier racine valable sélectionné")
            self.windows.change_button_color("red")
            return
        folder = self.class_files(name, root_folder["subfolders"])
        if(folder == None):
            return
        print(folder.name)
        #create custom name Month-Year - name - activity
        date = datetime.datetime.now()
        name_to_sort = str(self.windows.get_date())+"-"+str(activity)+"-"+name
        self.upload_file(self.file_to_sort, folder.id, name_to_sort, name)
class Folder:
    """A class to represent a folder.
    """

    def __init__(self, rawfile, id):
        self.id = id
        self.name = rawfile["name"]
        frome = rawfile["from"]
        to = rawfile["to"]

        self.from_index = []
        self.to_index = []

        #loop on each char of from
        for char in frome:
            #convert char to int
            char = char_to_int(char)
            #add int to to
            self.from_index.append(char)
        
        #loop on each char of to
        for char in to:
            #convert char to int
            char = char_to_int(char)
            #add int to to
            self.to_index.append(char)


#GLOBAL VARIABLES
# Action method
def browse_file(organiser):
    file_path = filedialog.askopenfilename()
    if(file_path == ""):
        return
    organiser.set_file_to_sort(file_path)
    organiser.windows.write("\u2611Fichier sélectionné")
    organiser.windows.write_pdf_info(retrieve_pdf_info(file_path))
def send_file(organiser, name_to_sort, category, root_folder):
    organiser.windows.write("\u2610Fichier en cours d'envoi")
    organiser.windows.redraw()
    organiser.send_file_to(name_to_sort, category, root_folder)
     




def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    organizer = None

    #convert settings.json to a python dictionary
    raw = json.load(open('settings.json', 'r',encoding="utf8"))
    foldersRef = raw["folders"]
    categories = raw["categories"]
    rootFolders = raw["root-folders"]
    try:
        # Create the service object for interacting with the API.
        service = build('drive', 'v3', credentials=creds)

        # Set up the query parameters
        query = "mimeType='application/vnd.google-apps.folder'"     
        organizer = FileOrganiser(service)


    except HttpError as error:
        print('An error occurred'+error)
        return

    #Retrieve all root folders
    root_folders = {}
    for root_folder in rootFolders:
        temp = retrieve_folder_from_name(service, root_folder)
        if(temp == None):
            continue
        root_folders[root_folder] = temp
        root_folders[root_folder]["subfolders"] = []
        allFolders = retrieve_folders(service, root_folder)
        for file in foldersRef:
            for item in allFolders:
                if item['name'] == file['name']:
                    root_folders[root_folder]["subfolders"].append(Folder(file, item['id']))


    # Création de la fenêtre principale de taille 640x480
    window = tk.Tk()
    window.geometry("640x480")
    window.title("Cab Sort")

    # Création 

    # Création du champ de saisie pour le nom et le prénom
    name_entry = tk.Entry(window)
    selected = tk.StringVar()
    selected.set(categories[0])  # On définit l'option sélectionnée par défaut
    
    root_selected = tk.StringVar()
    root_selected.set(rootFolders[0])  # On définit l'option sélectionnée par défaut

    #Info pdf box
    info_pdf_box = tk.Label(window, text="Aucun fichier sélectionné")

    category_entry = tk.Entry(window)


    #Creation d'un text dialog avec texte modifiable
    dialog_box = tk.Label(window, text="Historique\nAucun fichier sélectionné")

    date_prompt = tk.Entry(window)

    # Encodage des caractères
    window.option_add("*tearOff", False)
    window.tk.call('encoding', 'system', 'utf-8')
    
    # Création des boutons
    dropdown = tk.OptionMenu(window, selected, *categories)
    root_selection = tk.OptionMenu(window, root_selected, *rootFolders)
    browse_button = tk.Button(text="Parcourir", command= lambda : browse_file(organizer))
    send_button = tk.Button(text="Envoyer", command= lambda  : send_file(organizer, name_entry.get(), selected.get() if category_entry.get() == "" else category_entry.get() , root_folders[root_selected.get()]))

    #Infobox
    infobox_category = tk.Label(window, text="Catégorie")
    infobox_name = tk.Label(window, text="Nom")
    infobox_root = tk.Label(window, text="Dossier racine")
    infobox_date = tk.Label(window, text="Date")

    # Packing all items on the left side vertically
    infobox_name.pack()
    name_entry.pack()
    infobox_root.pack()
    root_selection.pack()
    infobox_category.pack()
    category_entry.pack()
    dropdown.pack()


    infobox_date.pack()
    date_prompt.pack()

    browse_button.pack()
    send_button.pack()
    dialog_box.pack()

    #Packing the pdf info on the right side
    #info_pdf_box.pack(side="right")


    # Set windows
    organizer.set_windows(Windows(window,send_button,dialog_box, info_pdf_box, date_prompt))

    # Affichage de la fenêtre
    window.mainloop()

if __name__ == '__main__':
    main()