
import sys
import random
from PyQt5.QtWidgets import QColorDialog
import requests
from PyQt5.QtCore import QPoint,Qt
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QPixmap, QPainter,QColor,QFontMetrics
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QWidget, QVBoxLayout, QPushButton


class DraggableImageLabel(QLabel):
    imageResized = QtCore.pyqtSignal(QLabel)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(True)
        self.setMouseTracking(True)
        self.dragging = False
        self.mouse_press_pos = None
        self.mouse_move_pos = None


    #to make the image clickable and movable 
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.mouse_press_pos = event.globalPos()
            self.mouse_move_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.dragging:
            delta = event.globalPos() - self.mouse_move_pos
            self.move(self.pos() + delta)
            self.mouse_move_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            delta = event.globalPos() - self.mouse_press_pos
            if delta.manhattanLength() > 3:
                event.ignore()

    def setSelected(self, selected):
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def isSelected(self):
        return self.property("selected")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_text_on_image()
        self.imageResized.emit(self)

    def adjust_text_on_image(self):
        painter = QPainter(self.pixmap())
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)

        painter.setPen(Qt.white)

        text_pos = self.rect().topLeft() + QPoint(10, 10)

        # Draw the text background rectangle
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(text_pos.x(), text_pos.y(), self.width(), self.height(), Qt.AlignLeft, self.text())
        painter.fillRect(text_rect, QColor(50, 0, 0, 128))

        # Draw the text on the image label
        painter.drawText(text_pos, self.text())

        # Update the image label
        painter.end()
        self.update()



class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setGeometry(100, 100, 800, 600)
        self.image_labels = []
        self.background_image = None
        imageResized = QtCore.pyqtSignal(QLabel, QtCore.QSize)

    

    def add_image(self, pixmap):
        image_label = DraggableImageLabel(self)
        image_label.setPixmap(pixmap)
        image_label.move(
            random.randint(0, self.width() - image_label.width()),
            random.randint(0, self.height() - image_label.height()),
        )
        self.image_labels.append(image_label)
        image_label.show()

        image_size = pixmap.size()
        size_text = f"size: {image_size.width()} x {image_size.height()}"
        self.draw_text_on_image(image_label, size_text)
        

        # Get image color
        image_color = self.get_average_image_color(pixmap)
        color_text = f"color: {image_color.name()}"
        self.draw_text_on_image(image_label, color_text, offset_y=20)
        image_label.imageResized.connect(self.resizeImage)

    def draw_text_on_image(self, image_label, text, offset_x=10, offset_y=10):
        # Create a QPainter and set the font
        painter = QPainter(image_label.pixmap())
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(Qt.white)
        text_pos = image_label.rect().topLeft() + QtCore.QPoint(offset_x, offset_y)

       
        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(text_pos.x(), text_pos.y(), image_label.width(), image_label.height(), Qt.AlignLeft, text)
        painter.fillRect(text_rect, QColor(50, 0, 0, 128))

        painter.drawText(text_pos, text)
        image_label.update()

    def get_average_image_color(self, pixmap):
        # Convert QPixmap to QImage
        image = pixmap.toImage()

        # Calculate average color
        total_red = 0
        total_green = 0
        total_blue = 0

        for y in range(image.height()):
            for x in range(image.width()):
                pixel_color = QColor(image.pixel(x, y))
                total_red += pixel_color.red()
                total_green += pixel_color.green()
                total_blue += pixel_color.blue()

        total_pixels = image.width() * image.height()
        average_red = total_red // total_pixels
        average_green = total_green // total_pixels
        average_blue = total_blue // total_pixels

        return QColor(average_red, average_green, average_blue)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.background_image:
            painter.drawPixmap(self.rect(), self.background_image)
        for image_label in self.image_labels:
            image_pixmap = image_label.pixmap()
            image_pos = image_label.pos()
            painter.drawPixmap(image_pos, image_pixmap)
        painter.end()
    def group_images(self):
        if len(self.image_labels) > 1:
            min_x = min([image_label.x() for image_label in self.image_labels])
            min_y = min([image_label.y() for image_label in self.image_labels])
            group_pos = QtCore.QPoint(min_x, min_y)

            group_widget = QWidget(self)
            group_layout = QVBoxLayout(group_widget)

            for image_label in self.image_labels:
                image_label.setParent(group_widget)
                group_layout.addWidget(image_label)

            group_widget.move(group_pos)
            group_widget.show()

        
    def resizeImage(self, image_label):
        current_pixmap = image_label.pixmap()
        scaled_pixmap = current_pixmap.scaled(
            current_pixmap.width() * 2,
            current_pixmap.height() * 2,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        image_label.setPixmap(scaled_pixmap)

        
    def resize_all_images(self, scale_factor):
        for image_label in self.image_labels:
            current_pixmap = image_label.pixmap()
            scaled_pixmap = current_pixmap.scaled(
                current_pixmap.width() * scale_factor,
                current_pixmap.height() * scale_factor,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            new_image_label = DraggableImageLabel(self)
            new_image_label.setPixmap(scaled_pixmap)
            new_image_label.move(image_label.pos())
            self.image_labels.remove(image_label)
            image_label.setParent(None)
            image_label.deleteLater()
            self.image_labels.append(new_image_label)
            new_image_label.show()

        self.update()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("DESKTOP")
        self.setGeometry(600, 600, 800, 600)

        self.canvas = Canvas(self)
        self.setCentralWidget(self.canvas)
        self.canvas.background_image = QtGui.QPixmap("profile")  


        self.button1 = QPushButton("1 DISPLAY IMAGE", self)
        self.button1.clicked.connect(self.display_image)
        self.button1.move(30, 450)
        self.button1.resize(150, 50)
        self.button1.setStyleSheet("QPushButton"
                                "{"
                                "background:lightblue;border: 5px solid black; border-radius: 9px;}"
                                "QPushButton:pressed"
                                "{"
                                "background:green;}"
                                "QPushButton:hover""{""background-color: green;""}")    
        
        self.button2 = QPushButton("2 GROUP IMAGES", self)
        self.button2.clicked.connect(self.canvas.group_images)
        self.button2.setStyleSheet("QPushButton"
                                "{"
                                "background:lightblue;border: 5px solid black; border-radius: 9px;}"
                                "QPushButton:pressed"
                                "{"
                                "background:green;}"
                                "QPushButton:hover""{""background-color: green;""}")    
                                   
        self.button2.move(220, 450)
        self.button2.resize(150, 50)
        
        self.button3 = QPushButton("3 CHANGE SIZE", self)
        self.button3.clicked.connect(self.resize_images)
        self.button3.setStyleSheet("QPushButton"
                                  "{"
                                  "background:lightblue;border: 5px solid black; border-radius: 9px;}"
                                  "QPushButton:pressed"
                                  "{"
                                  "background:green;}"
                                  "QPushButton:hover""{""background-color: green;""}")
        self.button3.move(420, 450)
        self.button3.resize(150, 50)
        
        self.button4 = QPushButton("4 CHANGE COLOUR", self)
        self.button4.clicked.connect(self.change_image_color)
        self.button4.setStyleSheet("QPushButton"
                                  "{"
                                  "background:lightblue;border: 5px solid black; border-radius: 9px;}"
                                  "QPushButton:pressed"
                                  "{"
                                  "background:green;}"
                                  "QPushButton:hover""{""background-color: green;""}")
        self.button4.move(620, 450)
        self.button4.resize(150, 50)
        

    #TO REQUEST AND DISPLAY THE IMAGE FROM GIVEN GITHUB REPOSITORY
    def display_image(self):
        url = "https://api.github.com/repos/hfg-gmuend/openmoji/contents/src/symbols/geometric"
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            image_files = [
                file["download_url"]
                for file in json_data
                if file["type"] == "file" and file["name"].endswith(".svg")
            ]

            if image_files:
                random_image = random.choice(image_files)
                image_response = requests.get(random_image)
                if image_response.status_code == 200:
                    pixmap = QPixmap()
                    pixmap.loadFromData(image_response.content)
                    self.canvas.add_image(pixmap)
      
    #SET DEFAULT RESIZE TO 1.1
    def resize_images(self):
        scale_factor = 1.1 
        self.canvas.resize_all_images(scale_factor)
       
    #FUNCTION TO CHANGE THE COLOUR PREFERRED BY USER
    def change_image_color(self):
        new_color = QColorDialog.getColor()
        if new_color.isValid():
            for image_label in self.canvas.image_labels:
                image_label.setPalette(QtGui.QPalette(new_color))
                image_label.setAutoFillBackground(True)
                image_label.update()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())