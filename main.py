from __future__ import print_function
import tkinter as tk

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

def char_to_int(char: str) -> int:
    """Convert a single character to an integer.

    Args:
        char: The character to convert.

    Returns:
        The integer value of the character.
    """
    return ord(char)
def find_folder(folder, folders):
    for f in folders:
        if f.id == folder.id:
            return f
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
    def __init__(self, window,send_button, dialog_box):
        self.send_button = send_button
        self.dialog_box = dialog_box
        self.window = window
    def redraw(self):
        self.window.update()
    def write(self, text):
        '''Write text in the dialog box label.'''
        self.dialog_box.configure(text= self.dialog_box["text"] + '\n' + text)
    def clear(self):
        self.dialog_box.delete(1.0, tk.END)
    def change_button_color(self, color):
        self.send_button.config(bg=color)
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

    def __init__(self, folders, service, windows=None):
        self.folders = folders
        self.file_to_sort = None
        self.service = service
        self.windows = windows
    def set_windows(self, windows):
        self.windows = windows
    def set_file_to_sort(self, file):
        self.file_to_sort = file
    def upload_file(self, file_path, folder_id, file_name, subfolder_name):
        '''
        Upload a file to a folder.

        Args:

            file_path: The path of the file to upload.
            folder_id: The id of the folder to upload the file to.
            file_name: The name of the file to upload.
            subfolder_name: The name of the subfolder to upload the file to.
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
            # Vérifier si le sous-dossier existe déjà
            query = "mimeType='application/vnd.google-apps.folder' and trashed = false and name='" + subfolder_name + "' and parents in '" + folder_id + "'"
            results = self.service.files().list(q=query,fields="nextPageToken, files(id, name)").execute()
            files = results.get("files", [])

            # Si le sous-dossier n'existe pas, le créer
            if not files:
                folder_metadata = {
                    'name': subfolder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [folder_id]
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                subfolder_id = folder.get('id')
            else:
                subfolder_id = files[0]['id']

            # Téléverser le fichier dans le sous-dossier
            file_metadata = {'name': file_name, 'parents': [subfolder_id]}
            media = MediaFileUpload(file_path, mimetype='application/octet-stream', resumable=True)
            self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            self.windows.write("\u2611Fichier téléversé avec succès")
            self.windows.change_button_color("green")
        except HttpError as error:
            self.windows.write(F'\u2612Erreur lors du téléversement du fichier: {error}')
            self.windows.change_button_color("red")
    def class_files(self, name):
        """Classify the files into their respective folders.

        Args:
            files: The list of files to classify.
        """
        
        selected_folders = self.folders.copy()
        returned_folder = selected_folders.copy()
        char_index = 0;

        while(len(returned_folder) > 1):
            char_integer = char_to_int(name[char_index])
            for i in range(len(selected_folders)):
                if(len(selected_folders[i].from_index) <= char_index or len(selected_folders[i].to_index) <= char_index):
                    continue
                if(selected_folders[i].from_index[char_index] == selected_folders[i].to_index[char_index] and selected_folders[i].from_index[char_index] != char_integer):
                    returned_folder.remove(find_folder(selected_folders[i], returned_folder))
                elif selected_folders[i].from_index[char_index] > char_integer or selected_folders[i].to_index[char_index] < char_integer:
                    returned_folder.remove(find_folder(selected_folders[i], returned_folder))
            
            char_index += 1
        if len(returned_folder) == 1:
            return returned_folder[0]
        max_index = 0
        max = len(returned_folder[0].from_index)
        for folder in returned_folder:
            if(len(folder.from_index) > max):
                max = len(folder.from_index)
                max_index = returned_folder.index(folder)
        return returned_folder[max_index]
    def send_file_to(self, name, activity):
        """Upload a new file to a folder.

        Args:
            name (str): The name of the file to upload.
            activity (str): The activity of the file to upload.
        """
        # Create the file metadata
        folder = self.class_files(name)
        #create custom name Month-Year - name - activity
        date = datetime.datetime.now()
        name_to_sort = f"{date.month}-{date.year} - {activity} - {name}"
        self.upload_file(self.file_to_sort, folder.id, name_to_sort, name)
class Folder:
    """A class to represent a folder.
    """

    def __init__(self, rawfile: dict, id: str):
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
    organiser.set_file_to_sort(file_path)
    organiser.windows.write("\u2611Fichier sélectionné")
def send_file(organiser, name_to_sort, category):
    organiser.windows.write("\u2610Fichier en cours d'envoi")
    organiser.windows.redraw()
    organiser.send_file_to(name_to_sort, category)
     




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
    folders=[]
    try:
        # Create the service object for interacting with the API.
        service = build('drive', 'v3', credentials=creds)

        # Set up the query parameters
        query = "mimeType='application/vnd.google-apps.folder'"

        # Retrieve the list of folders
        results = service.files().list(q=query, fields='nextPageToken, '
                                                'files(id, name)').execute()
        items = results.get('files', [])

        # Identify folders
        for item in items:
            for file in foldersRef:
                if item['name'] == file['name']:
                    folders.append(Folder(file, item['id']))
                    
        organizer = FileOrganiser(folders, service)

    except HttpError as error:
        print('An error occurred'+error)


    # Création de la fenêtre principale de taille 640x480
    window = tk.Tk()
    window.geometry("640x480")
    window.title("Cab Sort")

    # Création du champ de saisie pour le nom et le prénom
    name_entry = tk.Entry(window)
    name_entry.pack()
    selected = tk.StringVar()
    selected.set(categories[0])  # On définit l'option sélectionnée par défaut
    
    #Creation d'un text dialog avec texte modifiable
    dialog_box = tk.Label(window, text="Historique\nAucun fichier sélectionné")

    # Encodage des caractères
    window.option_add("*tearOff", False)
    window.tk.call('encoding', 'system', 'utf-8')
    
    # Création des boutons
    dropdown = tk.OptionMenu(window, selected, *categories)
    browse_button = tk.Button(text="Parcourir", command= lambda : browse_file(organizer))
    send_button = tk.Button(text="Envoyer", command= lambda  : send_file(organizer, name_entry.get(), selected.get()))

    # Packing
    dropdown.pack()
    browse_button.pack()
    send_button.pack()
    dialog_box.pack()

    # Set windows
    organizer.set_windows(Windows(window,send_button,dialog_box))

    # Affichage de la fenêtre
    window.mainloop()

if __name__ == '__main__':
    main()