import os
import sys
import uuid
from datetime import timedelta
import xlsxwriter
import pywin32_system32
import firebase_admin
import requests
from PySide6.QtCore import Qt, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImage, QPixmap, QTransform
from PySide6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, \
    QLineEdit, QLabel, QCheckBox, QFileDialog, QWidget
from PySide6.QtWidgets import QMainWindow
from firebase_admin import credentials, storage
from firebase_admin import firestore


class Person():
    def __init__(self, name, year, city, graduation, school, field, email, number, description, photoURL, id):
        super().__init__()
        self.photoURL = photoURL
        self.year = year
        self.city = city
        self.graduation = graduation
        self.school = school
        self.field = field
        self.email = email
        self.number = number
        self.description = description
        self.name = name
        self.id = id


cred = credentials.Certificate(
    "okul-mezun-takip-firebase-adminsdk-6gu3o-d3e256d063.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'gs://okul-mezun-takip.appspot.com'
})
bucket_name = "okul-mezun-takip.appspot.com"
bucket = storage.bucket(bucket_name)

db = firestore.client()

# Reference to a Firestore collection
collection_ref = db.collection("People")

defimgLink = "https://firebasestorage.googleapis.com/v0/b/okul-mezun-takip.appspot.com/o/photos%2F70d34b0f-38cc-4b6b-9154-c28589f9cadf.jpg?alt=media&token=613fd186-6d6a-40cf-85b4-3ede538d9b48"


def load_online_image(url):
    try:
        response = requests.get(url)
    except:
        response = requests.get(defimgLink)
    pixmap = QPixmap()
    pixmap.loadFromData(response.content)
    return pixmap


def scale_image(pixmap):
    scaled_pixmap = pixmap.scaled(130, 170)
    return scaled_pixmap


class AddWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kişi Ekle")
        self.setFixedSize(1400, 700)
        self.person_id = (uuid.uuid1().hex)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout(central_widget)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("Ad Soyad")
        self.layout.addWidget(self.name_edit)

        self.year_edit = QLineEdit(self)
        self.year_edit.setPlaceholderText("Lise Mezuniyet Yılı")
        self.layout.addWidget(self.year_edit)

        self.city_edit = QLineEdit(self)
        self.city_edit.setPlaceholderText("Bulunduğu İl")
        self.layout.addWidget(self.city_edit)

        self.school_edit = QLineEdit(self)
        self.school_edit.setPlaceholderText("Üniversite")
        self.layout.addWidget(self.school_edit)

        self.field_edit = QLineEdit(self)
        self.field_edit.setPlaceholderText("Bölüm")
        self.layout.addWidget(self.field_edit)

        self.checkbox = QCheckBox("Üniversite Mezuniyet Durumu", self)
        self.layout.addWidget(self.checkbox)

        self.description_edit = QLineEdit(self)
        self.description_edit.setPlaceholderText("Ek Not")
        self.layout.addWidget(self.description_edit)

        self.number_edit = QLineEdit(self)
        self.number_edit.setPlaceholderText("Telefon No (Başında 0 Olmadan)")
        self.layout.addWidget(self.number_edit)

        self.email_edit = QLineEdit(self)
        self.email_edit.setPlaceholderText("Email")
        self.layout.addWidget(self.email_edit)

        image_select_button = QPushButton("Resim Seç", self)
        image_select_button.clicked.connect(self.image_select)
        self.layout.addWidget(image_select_button)

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(130, 170)
        self.layout.addWidget(self.image_label)

        save_button = QPushButton("Kaydet", self)
        save_button.clicked.connect(self.save_changes)

        self.layout.addWidget(save_button)

    def save_changes(self):
        doc_ref = db.collection("People").document(self.person_id)

        name = self.name_edit.text()
        year = self.year_edit.text()
        city = self.city_edit.text()
        school = self.school_edit.text()
        field = self.field_edit.text()
        description = self.description_edit.text()
        number = self.number_edit.text()
        email = self.email_edit.text()
        checked = self.checkbox.isChecked()

        field_updates = {
            'id': self.person_id,
            'name': name,
            'year': int(year),
            'city': city,
            'school': school,
            'field': field,
            'graduation': checked,
            'description': description,
            'number': int(number),
            'email': email,
            'photoURL': self.photoURL
        }

        doc_ref.set(field_updates)
        self.close()

    def image_select(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.bmp)")
        if file_dialog.exec():
            self.selected_image_path = file_dialog.selectedFiles()[0]
            self.display_image(self.selected_image_path)

    def image_save(self):
        if self.selected_image_path:
            # Set your desired aspect ratio
            aspect_ratio = 13 / 17  # Width to height ratio

            image = QImage(self.selected_image_path)
            width = image.width()
            height = image.height()

            if width / height > aspect_ratio:
                target_width = int(height * aspect_ratio)
                target_height = height
                if width > height:
                    image = image.transformed(QTransform().rotate(90))
            else:
                target_width = width
                target_height = int(width / aspect_ratio)

            # Scale the image to the target dimensions while preserving the aspect ratio
            scaled_image = image.scaled(
                target_width, target_height, Qt.KeepAspectRatio)

            # Calculate the starting point for cropping
            x = (scaled_image.width() - target_width) // 2
            y = (scaled_image.height() - target_height) // 2

            # Crop the scaled image
            cropped_image = scaled_image.copy(
                x, y, target_width, target_height)

            # Upload the cropped image to Firebase Cloud Storage
            photoID = self.person_id
            cropped_image.save(photoID + "-photoID.jpg")
            # Upload the cropped image to Firebase Cloud Storage
            cropped_image.save(photoID +
                               "-photoID.jpg")

            image = QImage(photoID +
                           "-photoID.jpg")
            pixmap = QPixmap.fromImage(image)
            cropped_pixmap = pixmap.scaled(
                self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio)

            self.image_label.setPixmap(cropped_pixmap)
            self.image_label.setScaledContents(True)

            destination_blob_name = "photos/" + photoID + \
                                    "-photoID.jpg"  # Change the filename or path as needed

            try:
                # Convert QImage to bytes
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.WriteOnly)
                cropped_image.save(buffer, "JPEG")
                buffer.close()
                image_bytes = byte_array.data()

                # Upload the image bytes to Firebase Cloud Storage
                blob = storage.bucket(bucket_name).blob(destination_blob_name)
                blob.upload_from_string(image_bytes, content_type='image/jpeg')
                self.blob_name = "photos/" + photoID + "-photoID.jpg"

                # Get the blob
                self.blob = bucket.blob(self.blob_name)

                # Generate a signed URL with the specified expiration time
                self.photoURL = self.blob.generate_signed_url(
                    version='v4',
                    expiration=timedelta(days=7),
                    method='GET'
                )

                print("Image uploaded successfully.")
                delete = photoID + "-photoID.jpg"

                # Check if the file exists
                if os.path.exists(delete):
                    # Delete the file
                    os.remove(delete)
            except Exception as e:
                print(f"Image upload failed: {e}")
                delete = photoID + "-photoID.jpg"

                # Check if the file exists
                if os.path.exists(delete):
                    # Delete the file
                    os.remove(delete)

    def display_image(self, image_path):
        if image_path:
            image = QImage(image_path)
            pixmap = QPixmap.fromImage(image)
            cropped_pixmap = pixmap.scaled(
                self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio)

            self.image_label.setPixmap(cropped_pixmap)
            self.image_label.setScaledContents(True)
            self.image_save()


class EditWindow(QMainWindow):
    def __init__(self, row, name, year, city, school, field, graduation, description, number, email, id, photoURL):
        super().__init__()
        self.setWindowTitle("Düzenle " + name)
        self.setFixedSize(1400, 700)
        self.id = id
        self.photoURL = photoURL
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout(central_widget)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("Ad Soyad")
        self.name_edit.setText(name)
        self.layout.addWidget(self.name_edit)

        self.year_edit = QLineEdit(self)
        self.year_edit.setPlaceholderText("Lise Mezuniyet Yılı")
        self.year_edit.setText(year)
        self.layout.addWidget(self.year_edit)

        self.city_edit = QLineEdit(self)
        self.city_edit.setPlaceholderText("Bulunduğu İl")
        self.city_edit.setText(city)
        self.layout.addWidget(self.city_edit)

        self.school_edit = QLineEdit(self)
        self.school_edit.setPlaceholderText("Üniversite")
        self.school_edit.setText(school)
        self.layout.addWidget(self.school_edit)

        self.field_edit = QLineEdit(self)
        self.field_edit.setPlaceholderText("Bölüm")
        self.field_edit.setText(field)
        self.layout.addWidget(self.field_edit)

        self.checkbox = QCheckBox("Üniversite Mezuniyet Durumu", self)
        self.checkbox.setChecked(graduation)
        self.layout.addWidget(self.checkbox)

        self.description_edit = QLineEdit(self)
        self.description_edit.setPlaceholderText("Ek Not")
        self.description_edit.setText(description)
        self.layout.addWidget(self.description_edit)

        self.number_edit = QLineEdit(self)
        self.number_edit.setPlaceholderText("Telefon No (Başında 0 Olmadan)")
        self.number_edit.setText(number)
        self.layout.addWidget(self.number_edit)

        self.email_edit = QLineEdit(self)
        self.email_edit.setPlaceholderText("Email")
        self.email_edit.setText(email)
        self.layout.addWidget(self.email_edit)

        image_select_button = QPushButton("Resim Seç", self)
        image_select_button.clicked.connect(self.image_select)
        self.layout.addWidget(image_select_button)

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(130, 170)
        response = requests.get(self.photoURL)
        data = response.content
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        print(self.photoURL)
        self.image_label.setPixmap(pixmap.scaled(
            130, 170, Qt.AspectRatioMode.KeepAspectRatio))

        self.layout.addWidget(self.image_label)

        save_button = QPushButton("Kaydet", self)
        save_button.clicked.connect(self.save_changes)

        self.layout.addWidget(save_button)

        self.row = row

    def save_changes(self):
        person_id = self.id  # Replace `id` with the variable that holds the document ID
        doc_ref = db.collection("People").document(person_id)

        name = self.name_edit.text()
        year = self.year_edit.text()
        city = self.city_edit.text()
        school = self.school_edit.text()
        field = self.field_edit.text()
        description = self.description_edit.text()
        number = self.number_edit.text()
        email = self.email_edit.text()
        checked = self.checkbox.isChecked()

        field_updates = {
            'name': name,
            'year': int(year),
            'city': city,
            'school': school,
            'field': field,
            'graduation': checked,
            'description': description,
            'number': int(number),
            'email': email,
            "photoURL": self.photoURL

        }

        doc_ref.update(field_updates)
        self.close()

    def image_select(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.bmp)")
        if file_dialog.exec():
            self.selected_image_path = file_dialog.selectedFiles()[0]
            self.display_image(self.selected_image_path)

    def display_image(self, image_path):
        if image_path:
            image = QImage(image_path)
            pixmap = QPixmap.fromImage(image)
            cropped_pixmap = pixmap.scaled(
                self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio)

            self.image_label.setPixmap(cropped_pixmap)
            self.image_label.setScaledContents(True)
            self.image_save()

    def image_save(self):
        if self.selected_image_path:
            # Set your desired aspect ratio
            aspect_ratio = 13 / 17  # Width to height ratio

            image = QImage(self.selected_image_path)
            width = image.width()
            height = image.height()

            if width / height > aspect_ratio:
                target_width = int(height * aspect_ratio)
                target_height = height
                if width > height:
                    image = image.transformed(QTransform().rotate(90))
            else:
                target_width = width
                target_height = int(width / aspect_ratio)

            # Scale the image to the target dimensions while preserving the aspect ratio
            scaled_image = image.scaled(
                target_width, target_height, Qt.KeepAspectRatio)

            # Calculate the starting point for cropping
            x = (scaled_image.width() - target_width) // 2
            y = (scaled_image.height() - target_height) // 2

            # Crop the scaled image
            cropped_image = scaled_image.copy(
                x, y, target_width, target_height)

            # Upload the cropped image to Firebase Cloud Storage
            photoID = self.id
            cropped_image.save(photoID + "-photoID.jpg")
            # Upload the cropped image to Firebase Cloud Storage
            cropped_image.save(photoID +
                               "-photoID.jpg")

            image = QImage(photoID +
                           "-photoID.jpg")
            pixmap = QPixmap.fromImage(image)
            cropped_pixmap = pixmap.scaled(
                self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio)

            self.image_label.setPixmap(cropped_pixmap)
            self.image_label.setScaledContents(True)

            destination_blob_name = "photos/" + photoID + \
                                    "-photoID.jpg"  # Change the filename or path as needed

            try:
                # Convert QImage to bytes
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.WriteOnly)
                cropped_image.save(buffer, "JPEG")
                buffer.close()
                image_bytes = byte_array.data()

                # Upload the image bytes to Firebase Cloud Storage
                blob = storage.bucket(bucket_name).blob(destination_blob_name)
                blob.upload_from_string(image_bytes, content_type='image/jpeg')
                self.blob_name = "photos/" + photoID + "-photoID.jpg"

                # Get the blob
                self.blob = bucket.blob(self.blob_name)

                # Generate a signed URL with the specified expiration time
                self.photoURL = self.blob.generate_signed_url(
                    version='v4',
                    expiration=timedelta(days=7),
                    method='GET'
                )

                print("Image uploaded successfully.")
                delete = photoID + "-photoID.jpg"

                # Check if the file exists
                if os.path.exists(delete):
                    # Delete the file
                    os.remove(delete)
            except Exception as e:
                print(f"Image upload failed: {e}")
                delete = photoID + "-photoID.jpg"

                # Check if the file exists
                if os.path.exists(delete):
                    # Delete the file
                    os.remove(delete)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Mezun Takip Recep Tayyip Erdoğan Anadolu İmam Hatip Lisesi")
        self.setFixedSize(1400, 700)
        self.username_online = "HjıgurgdkQOHAOISOJojf"
        self.password_online = "jdogsıgjosıgoOHDOIHGSIORJGPıhWFGHI"

        doc_ref = db.collection("AdminData").document("user")
        doc = doc_ref.get()

        if doc.exists:
            # Access the document data
            data = doc.to_dict()

            # Access specific fields
            self.username_online = data.get("username")
            self.password_online = data.get("password")

        # Create a label, line edit, and button for login
        self.username_label = QLabel("Kullanıcı Adı:")
        self.username_edit = QLineEdit()
        self.password_label = QLabel("Şifre:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Giriş Yap")
        self.login_button.clicked.connect(self.login)

        # Set up the layout for the login section
        login_layout = QVBoxLayout()
        login_layout.addWidget(self.username_label)
        login_layout.addWidget(self.username_edit)
        login_layout.addWidget(self.password_label)
        login_layout.addWidget(self.password_edit)
        login_layout.addWidget(self.login_button)

        # Create a widget for the login section
        login_widget = QWidget()
        login_widget.setLayout(login_layout)

        # Create a label for the main window content
        self.content_label = QLabel("Hoş Geldin! Lütfen Giriş Yap.")

        # Set up the layout for the main window
        layout = QVBoxLayout()
        layout.addWidget(login_widget)
        layout.addWidget(self.content_label)

        # Create a central widget and set the layout
        central_widget = QWidget()
        central_widget.setLayout(layout)

        # Set the central widget of the main window
        self.setCentralWidget(central_widget)

    def open_secondary_window(self):
        self.secondary_window = SecondaryWindow()
        self.secondary_window.show()

    def login(self):
        username = self.username_edit.text()
        password = self.password_edit.text()

        # Perform login validation here
        if username == self.username_online and password == self.password_online:
            self.content_label.setText("Giriş Başarılı")
            self.open_secondary_window()
            self.close()

        else:
            self.content_label.setText("Geçersiz Giriş")


class SecondaryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Mezun Takip Recep Tayyip Erdoğan Anadolu İmam Hatip Lisesi")
        self.setFixedSize(1600, 800)
        self.photoURL = ""
        self.personList = []
        layout = QVBoxLayout()

        # Create the search filter layout
        search_layout = QHBoxLayout()

        # Create the search input field
        search_input = QLineEdit()
        self.search_input = search_input
        search_input.setPlaceholderText("Arama Yap...")
        search_input.textChanged.connect(self.filter_user_table)
        search_layout.addWidget(search_input)

        # Add search layout to main layout
        layout.addLayout(search_layout)

        # Create the user table
        user_table = QTableWidget()
        self.user_table = user_table
        user_table.setColumnCount(14)
        user_table.setHorizontalHeaderLabels(["Ad Soyad", "Lise Mezuniyet Yılı", "Bulunduğu İl", "Üniversite",
                                              "Bölüm", "Üniversite Mezuniyet Durumu", "Ek Not", "Telefon Numarası",
                                              "Email", "Fotoğraf", "Düzenle", "Kullanıcı ID", "Fotoğraf Link", "Sil"])
        user_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(user_table)

        # Create the button layout
        button_layout = QHBoxLayout()

        # Add a button to populate the user table
        populate_button = QPushButton("Verileri Getir")
        populate_button.clicked.connect(self.populate_user_table)
        button_layout.addWidget(populate_button)

        # Add a button to add people
        add_button = QPushButton("Kişi Ekle")
        add_button.clicked.connect(self.open_add_window)
        button_layout.addWidget(add_button)
        # Add the button layout to the main layout
        excel_button = QPushButton("Excel'e Aktar")
        excel_button.clicked.connect(self.create_excel)
        button_layout.addWidget(excel_button)

        layout.addLayout(button_layout)

        # Set the layout for the main window
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Show the main window
        self.show()

    def create_excel(self):
        home_dir = os.path.expanduser("~")

        # Specify the desktop path based on the operating system
        desktop_path = os.path.join(home_dir, "Downloads")

        # Specify the Excel file path
        excel_file_path = os.path.join(desktop_path, "MezunTakip.xlsx")

        # Create the directory if it doesn't exist
        if not os.path.exists(desktop_path):
            os.makedirs(desktop_path)
        workbook = xlsxwriter.Workbook(excel_file_path)
        worksheet = workbook.add_worksheet()
        row = 1
        col = 0
        myList = (
            "Ad Soyad", "Lise Mezuniyet Yılı", "Bulunduğu İl", "Üniversite", "Bölüm", "Üniversite Mezuniyet Durumu",
            "Ek Not", "Telefon",
            "Email",
            "Fotoğraf Link")
        iCount = 0
        for i in myList:
            worksheet.write(0, iCount, i)
            iCount += 1
        for i in self.personList:
            worksheet.write(row, col, i.name)
            worksheet.write(row, col + 1, i.year)
            worksheet.write(row, col + 2, i.city)
            worksheet.write(row, col + 3, i.school)
            worksheet.write(row, col + 4, i.field)
            if i.graduation:
                worksheet.write(row, col + 5, "Mezun")
            else:
                worksheet.write(row, col + 5, "Mezun Değil")

            worksheet.write(row, col + 6, i.description)
            worksheet.write(row, col + 7, "+90" + str(i.number))
            worksheet.write(row, col + 8, i.email)
            worksheet.write(row, col + 9, i.photoURL)
            row += 1
            col = 0

        workbook.close()

    def filter_user_table(self):
        keyword = self.search_input.text().lower()

        for row in range(self.user_table.rowCount()):
            visible = False
            for column in range(self.user_table.columnCount() - 5):
                item = self.user_table.item(row, column)
                if keyword in item.text().lower():
                    visible = True
                    break
            self.user_table.setRowHidden(row, not visible)

    def populate_user_table(self):
        # Simulated user data
        row = 0
        col = 0

        doc_snapshot = collection_ref.list_documents()
        self.personList = []
        for i in doc_snapshot:
            new = i.get().to_dict()
            a = Person(new["name"], new["year"], new["city"], new["graduation"], new["school"],
                       new["field"], new["email"], new["number"], new["description"], new["photoURL"], new["id"])
            self.personList.append(a)

        # Clear the existing table
        self.user_table.setRowCount(0)

        # Populate the table with user data
        image_width = 130
        image_height = 170

        for i in self.personList:
            self.user_table.insertRow(row)
            self.user_table.setItem(row, col, QTableWidgetItem(i.name))
            self.user_table.setItem(
                row, col + 1, QTableWidgetItem(str(i.year)))
            self.user_table.setItem(row, col + 2, QTableWidgetItem(i.city))
            self.user_table.setItem(row, col + 3, QTableWidgetItem(i.school))
            self.user_table.setItem(row, col + 4, QTableWidgetItem(i.field))
            if i.graduation:
                self.user_table.setItem(
                    row, col + 5, QTableWidgetItem("Mezun"))
            else:
                self.user_table.setItem(
                    row, col + 5, QTableWidgetItem("Mezun Değil"))
            self.user_table.setItem(
                row, col + 6, QTableWidgetItem(i.description))
            self.user_table.setItem(
                row, col + 7, QTableWidgetItem(str(i.number)))
            self.user_table.setItem(row, col + 8, QTableWidgetItem(i.email))

            # Get the bucket

            self.blob_name = "photos/" + i.id + "-photoID.jpg"

            # Get the blob
            self.blob = bucket.blob(self.blob_name)

            # Generate a signed URL with the specified expiration time
            self.photoURL = self.blob.generate_signed_url(
                version='v4',
                expiration=timedelta(days=7),
                method='GET'
            )

            # Load and set the online image for the cell
            image_item = QTableWidgetItem()
            # Implement load_online_image function
            pixmap = load_online_image(self.photoURL)
            # Implement scale_image function
            scaled_pixmap = scale_image(pixmap)
            self.user_table.setItem(row, col + 9, image_item)

            # Set the size of the cell widget and image
            cell_widget = QLabel()
            cell_widget.setPixmap(scaled_pixmap)
            cell_widget.setFixedSize(image_width, image_height)
            self.user_table.setCellWidget(row, col + 9, cell_widget)
            # Set the row height to match the image height
            self.user_table.setColumnWidth(col + 9, image_width)
            self.user_table.setRowHeight(row, image_height)

            # Add "Edit" button to each row
            edit_button = QPushButton("Düzenle")
            edit_button.setProperty("row", row)
            edit_button.clicked.connect(self.edit_row)
            self.user_table.setCellWidget(row, col + 10, edit_button)
            self.user_table.setItem(row, col + 11, QTableWidgetItem(i.id))
            self.user_table.setItem(
                row, col + 12, QTableWidgetItem(self.photoURL))
            del_button = QPushButton("Sil")
            del_button.setProperty("row", row)
            del_button.clicked.connect(self.del_row)
            self.user_table.setCellWidget(row, col + 13, del_button)

            row += 1
            col = 0

    def del_row(self):
        button = self.sender()
        row = button.property("row")
        person_item = self.user_table.item(row, 11)
        if person_item:
            id = person_item.text()
            doc_ref = db.collection("People").document(id)
            doc_ref.delete()
            self.populate_user_table()

    def edit_row(self):
        button = self.sender()
        row = button.property("row")
        person_item = self.user_table.item(row, 11)
        name_item = self.user_table.item(row, 0)
        year_item = self.user_table.item(row, 1)
        city_item = self.user_table.item(row, 2)
        school_item = self.user_table.item(row, 3)
        field_item = self.user_table.item(row, 4)
        graduation_item = self.user_table.item(row, 5)

        graduation = False
        if (graduation_item.text() == "Mezun"):
            graduation = True
        else:
            graduation = False

        description_item = self.user_table.item(row, 6)
        number_item = self.user_table.item(row, 7)
        email_item = self.user_table.item(row, 8)
        photoURL_item = self.user_table.item(row, 12)

        if name_item and year_item and city_item and school_item and field_item and graduation_item and description_item and number_item and email_item and person_item and photoURL_item:
            name = name_item.text()
            year = year_item.text()
            city = city_item.text()
            school = school_item.text()
            field = field_item.text()
            description = description_item.text()
            number = number_item.text()
            email = email_item.text()
            id = person_item.text()
            photoURL = photoURL_item.text()

            self.open_edit_window(
                row, name, year, city, school, field, graduation, description, number, email, id, photoURL)

    def open_edit_window(self, row, name, year, city, school, field, graduation, description, number, email, id,
                         photoURL):
        self.edit_window = EditWindow(
            row, name, year, city, school, field, graduation, description, number, email, id, photoURL)
        self.edit_window.setWindowModality(Qt.ApplicationModal)
        self.edit_window.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.edit_window.show()

    def open_add_window(self):
        self.add_window = AddWindow()
        self.add_window.setWindowModality(Qt.ApplicationModal)
        self.add_window.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.add_window.show()


if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)

    # Create the main window
    main_window = MainWindow()
    main_window.show()

    # Run the application event loop
    sys.exit(app.exec())
